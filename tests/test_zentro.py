import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest import mock

from google.api_core import exceptions as google_exceptions

from fastapi.testclient import TestClient

ROOT = os.path.dirname(os.path.dirname(__file__))
AGENT_DIR = os.path.join(ROOT, 'ai-agents')
if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)

from agent_coordinator import AgentCoordinator
from mandate_creator import MandateCreator
from backend.policy_engine import MandateParsingError, PolicyDecisionEngine, PolicyMandateParser
from backend.server import app


client = TestClient(app)


class ZentroAgentTests(unittest.TestCase):
    def test_backend_health_and_dashboard_routes(self):
        health = client.get('/api/health')
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()['status'], 'ok')
        self.assertIn('gemini', health.json())

        status = client.get('/api/gemini/status')
        self.assertEqual(status.status_code, 200)
        self.assertIn('gemini', status.json())

        dashboard = client.get('/api/dashboard')
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn('summaryCards', dashboard.json())
        self.assertIn('recentTransactions', dashboard.json())

    def test_policy_endpoints_support_approve_block_and_escalate(self):
        approve_payload = {
            'user_id': 'user-1',
            'mandate_id': 'm-approve',
            'product_name': 'USB-C Hub',
            'product_category': 'electronics',
            'product_price': 2500,
            'merchant_name': 'Dell Technologies',
            'merchant_trust_status': 'verified',
            'currency': 'INR',
            'transaction_date': '2026-11-06',
            'mandate_rules': {
                'max_transaction_amount': 5000,
                'allowed_categories': ['electronics'],
                'blocked_categories': [],
                'allowed_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'require_approval_above': 3000,
                'currency': 'INR',
                'merchant_verification_required': True,
            },
        }
        block_payload = {**approve_payload, 'product_price': 7000, 'product_name': 'Gaming Laptop'}
        escalate_payload = {**approve_payload, 'merchant_name': 'Unknown Seller', 'merchant_trust_status': 'unknown'}

        approve = client.post('/api/policy/evaluate', json=approve_payload)
        self.assertEqual(approve.status_code, 200)
        self.assertEqual(approve.json()['decision']['decision'], 'APPROVE')

        block = client.post('/api/policy/evaluate', json=block_payload)
        self.assertEqual(block.status_code, 200)
        self.assertEqual(block.json()['decision']['decision'], 'BLOCK')

        escalate = client.post('/api/policy/evaluate', json=escalate_payload)
        self.assertEqual(escalate.status_code, 200)
        self.assertEqual(escalate.json()['decision']['decision'], 'ESCALATE')

    def test_mandate_routes_persist_and_retrieve(self):
        create = client.post('/api/mandates', json={
            'name': 'Test Live Mandate',
            'status': 'active',
            'monthlyLimit': 7500,
            'perPurchaseLimit': 2200,
            'approvalThreshold': 85,
            'allowedCategories': ['Technology'],
            'prohibitedCategories': [],
            'sellerRestrictions': ['verified sellers only']
        })
        self.assertEqual(create.status_code, 200)
        payload = create.json()
        self.assertTrue(payload['success'])

        mandates = client.get('/api/mandates')
        self.assertEqual(mandates.status_code, 200)
        self.assertGreaterEqual(len(mandates.json()['mandates']), 1)

    def test_default_model_matches_requirements(self):
        from config import get_agent_config
        self.assertEqual(get_agent_config()['model'], 'gemini-3.8-flash')

    def test_mandate_creator_returns_structured_mandate(self):
        result = MandateCreator({'gemini_api_key': ''}).evaluate({
            'mandate_text': 'Allow monthly technology spending up to 50000 rupees. Any single purchase above 10000 rupees requires human approval. Only verified sellers are allowed.'
        })
        self.assertIsNotNone(result.mandate)
        self.assertIn('allowed_categories', result.mandate)
        self.assertIn('monthly_limit', result.mandate)
        self.assertIn('single_purchase_limit', result.mandate)
        self.assertIn('approval_threshold', result.mandate)
        self.assertIn('verified_seller_only', result.mandate)

    def test_coordinator_runs_all_agents_and_builds_final_authorization(self):
        transaction = {
            'id': 'TXN-9001',
            'merchant': 'Dell Technologies',
            'category': 'Technology',
            'amount': 12500,
            'date': '2026-11-06',
            'status': 'pending',
            'paymentReference': 'INV-9001',
            'description': 'Laptop purchase'
        }
        payload = AgentCoordinator().run_all(transaction)
        self.assertEqual(len(payload['results']), 5)
        self.assertIn('final_authorization', payload)
        self.assertIn(payload['final_authorization']['decision'], {'APPROVE', 'BLOCK', 'ESCALATE', 'REVIEW'})

    def test_policy_engine_approves_valid_purchase(self):
        engine = PolicyDecisionEngine()
        result = engine.evaluate_purchase(
            user_id='user-1',
            mandate_id='mandate-approve',
            product_name='USB-C Hub',
            product_category='electronics',
            product_price=2500,
            merchant_name='Dell Technologies',
            merchant_trust_status='verified',
            currency='INR',
            transaction_date='2026-11-06',
            mandate_rules={
                'max_transaction_amount': 5000,
                'allowed_categories': ['electronics'],
                'blocked_categories': [],
                'allowed_days': ['Monday', 'Thursday', 'Friday'],
                'require_approval_above': 3000,
                'currency': 'INR',
                'merchant_verification_required': True,
                'require_user_confirmation_for': ['unknown']
            },
        )
        self.assertEqual(result['decision'], 'APPROVE')

    def test_policy_engine_blocks_above_limit(self):
        engine = PolicyDecisionEngine()
        result = engine.evaluate_purchase(
            user_id='user-1',
            mandate_id='mandate-limit',
            product_name='Gaming Laptop',
            product_category='electronics',
            product_price=7000,
            merchant_name='Dell Technologies',
            merchant_trust_status='verified',
            currency='INR',
            transaction_date='2026-11-06',
            mandate_rules={
                'max_transaction_amount': 5000,
                'allowed_categories': ['electronics'],
                'blocked_categories': [],
                'allowed_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'require_approval_above': 3000,
                'currency': 'INR',
                'merchant_verification_required': True,
            },
        )
        self.assertEqual(result['decision'], 'BLOCK')
        self.assertIn('maximum_allowed', result)

    def test_policy_engine_blocks_blocked_category(self):
        engine = PolicyDecisionEngine()
        result = engine.evaluate_purchase(
            user_id='user-1',
            mandate_id='mandate-category',
            product_name='Luxury Watch',
            product_category='jewelry',
            product_price=4500,
            merchant_name='Aurum Store',
            merchant_trust_status='verified',
            currency='INR',
            transaction_date='2026-11-06',
            mandate_rules={
                'max_transaction_amount': 5000,
                'allowed_categories': ['electronics'],
                'blocked_categories': ['jewelry'],
                'allowed_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'require_approval_above': 3000,
                'currency': 'INR',
            },
        )
        self.assertEqual(result['decision'], 'BLOCK')

    def test_policy_engine_escalates_unknown_merchant(self):
        engine = PolicyDecisionEngine()
        result = engine.evaluate_purchase(
            user_id='user-1',
            mandate_id='mandate-merchant',
            product_name='Office Chair',
            product_category='furniture',
            product_price=2500,
            merchant_name='Unknown Seller',
            merchant_trust_status='unknown',
            currency='INR',
            transaction_date='2026-11-06',
            mandate_rules={
                'max_transaction_amount': 5000,
                'allowed_categories': ['electronics', 'furniture'],
                'blocked_categories': [],
                'allowed_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'require_approval_above': 3000,
                'currency': 'INR',
                'merchant_verification_required': True,
            },
        )
        self.assertEqual(result['decision'], 'ESCALATE')

    def test_policy_engine_escalates_ambiguous_category(self):
        engine = PolicyDecisionEngine()
        result = engine.evaluate_purchase(
            user_id='user-1',
            mandate_id='mandate-ambiguous-category',
            product_name='Mixed Item',
            product_category='miscellaneous',
            product_price=500,
            merchant_name='Unknown Seller',
            merchant_trust_status='unknown',
            currency='INR',
            transaction_date='2026-11-06',
            mandate_rules={
                'max_transaction_amount': 2000,
                'allowed_categories': ['food', 'education'],
                'blocked_categories': ['electronics', 'entertainment'],
                'allowed_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                'require_approval_above': 1500,
                'currency': 'INR',
                'merchant_verification_required': True,
                'require_user_confirmation_for': ['unknown'],
                'unknown_merchant_blocked': True,
                'allow_unknown_merchants': False,
            },
        )
        self.assertEqual(result['decision'], 'ESCALATE')

    def test_policy_engine_requires_price(self):
        engine = PolicyDecisionEngine()
        with self.assertRaises(ValueError):
            engine.evaluate_purchase(
                user_id='user-1',
                mandate_id='mandate-price',
                product_name='Headphones',
                product_category='electronics',
                product_price=None,
                merchant_name='Dell Technologies',
                merchant_trust_status='verified',
                currency='INR',
                transaction_date='2026-11-06',
                mandate_rules={
                    'max_transaction_amount': 5000,
                    'allowed_categories': ['electronics'],
                    'blocked_categories': [],
                    'allowed_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                    'require_approval_above': 3000,
                    'currency': 'INR',
                },
            )

    def test_policy_engine_conflicting_rules_are_blocked(self):
        engine = PolicyDecisionEngine()
        result = engine.evaluate_purchase(
            user_id='user-1',
            mandate_id='mandate-conflict',
            product_name='Monitor',
            product_category='electronics',
            product_price=2000,
            merchant_name='Dell Technologies',
            merchant_trust_status='verified',
            currency='INR',
            transaction_date='2026-11-06',
            mandate_rules={
                'max_transaction_amount': 5000,
                'allowed_categories': ['electronics'],
                'blocked_categories': ['electronics'],
                'allowed_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'require_approval_above': 3000,
                'currency': 'INR',
            },
        )
        self.assertEqual(result['decision'], 'BLOCK')

    def test_policy_engine_expired_mandate_is_blocked(self):
        engine = PolicyDecisionEngine()
        expired = (datetime.utcnow() - timedelta(days=2)).strftime('%Y-%m-%d')
        result = engine.evaluate_purchase(
            user_id='user-1',
            mandate_id='mandate-expired',
            product_name='Keyboard',
            product_category='electronics',
            product_price=1200,
            merchant_name='Dell Technologies',
            merchant_trust_status='verified',
            currency='INR',
            transaction_date='2026-11-06',
            mandate_rules={
                'max_transaction_amount': 5000,
                'allowed_categories': ['electronics'],
                'blocked_categories': [],
                'allowed_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'require_approval_above': 3000,
                'currency': 'INR',
                'expires_on': expired,
            },
        )
        self.assertEqual(result['decision'], 'BLOCK')

    def test_policy_engine_invalid_gemini_response_is_handled(self):
        parser = PolicyMandateParser(api_key='dummy-key', gemini_client=None)
        normalized = parser._normalize_response('{not valid json}')
        self.assertEqual(normalized, {})

    def test_live_gemini_mandate_parsing_integration(self):
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('ZENTRO_GEMINI_API_KEY')
        if not api_key:
            self.skipTest('GEMINI_API_KEY is not configured for live integration testing.')

        parser = PolicyMandateParser(api_key=api_key, gemini_client=None)
        try:
            result = parser.parse('Allow monthly technology spending up to 50000 rupees. Any single purchase above 10000 rupees requires human approval. Only verified sellers are allowed.')
        except MandateParsingError as exc:
            if exc.error_type in {'quota_error', 'timeout', 'network_error', 'authentication_error', 'missing_api_key'}:
                self.skipTest(f'Live Gemini integration is unavailable in this environment: {exc.error_type}: {exc}')
            raise
        except google_exceptions.GoogleAPIError as exc:
            self.skipTest(f'Live Gemini integration is unavailable in this environment: {type(exc).__name__}: {exc}')

        self.assertIn('max_transaction_amount', result)
        self.assertIn('allowed_categories', result)
        self.assertTrue(result['merchant_verification_required'])

    def test_policy_engine_requires_explicit_error_when_gemini_unavailable(self):
        with mock.patch.dict(os.environ, {'GEMINI_API_KEY': '', 'ZENTRO_GEMINI_API_KEY': ''}, clear=False):
            parser = PolicyMandateParser(api_key='', gemini_client=None)
            with self.assertRaises(MandateParsingError) as cm:
                parser.parse('Buy electronics under ₹5,000.')
            self.assertEqual(cm.exception.error_type, 'missing_api_key')

    def test_policy_engine_explicit_fallback_is_separate_from_live_ai(self):
        with mock.patch.dict(os.environ, {'GEMINI_API_KEY': '', 'ZENTRO_GEMINI_API_KEY': ''}, clear=False):
            parser = PolicyMandateParser(api_key='', gemini_client=None)
            result = parser.parse_with_fallback('Buy electronics under ₹5,000.')
            self.assertEqual(result['source'], 'fallback')
            self.assertIn('rules', result)
            self.assertIn('max_transaction_amount', result['rules'])

    def test_policy_engine_rejects_invalid_gemini_response(self):
        parser = PolicyMandateParser(api_key='dummy-key', gemini_client=None)
        parser._call_gemini = lambda text: {}
        with self.assertRaises(MandateParsingError) as cm:
            parser.parse('Allow monthly technology spending up to 50000 rupees.')
        self.assertIn(cm.exception.error_type, {'invalid_model_response', 'invalid_mandate_schema'})

    def test_policy_engine_rejects_unauthorized_mandate_access(self):
        engine = PolicyDecisionEngine()
        engine.store_mandate('user-1', 'm-1', {'max_transaction_amount': 5000})
        with self.assertRaises(PermissionError):
            engine.get_mandate('user-2', 'm-1')

    def test_policy_engine_escalates_for_user_confirmation(self):
        engine = PolicyDecisionEngine()
        result = engine.evaluate_purchase(
            user_id='user-1',
            mandate_id='mandate-confirm',
            product_name='Monitor',
            product_category='electronics',
            product_price=4500,
            merchant_name='Dell Technologies',
            merchant_trust_status='verified',
            currency='INR',
            transaction_date='2026-11-06',
            mandate_rules={
                'max_transaction_amount': 10000,
                'allowed_categories': ['electronics'],
                'blocked_categories': [],
                'allowed_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'require_approval_above': 3000,
                'currency': 'INR',
                'require_user_confirmation': True,
            },
        )
        self.assertEqual(result['decision'], 'ESCALATE')


if __name__ == '__main__':
    unittest.main()
