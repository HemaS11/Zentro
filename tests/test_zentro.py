import os
import sys
import unittest
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(__file__))
AGENT_DIR = os.path.join(ROOT, 'ai-agents')
if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)

from agent_coordinator import AgentCoordinator
from mandate_creator import MandateCreator
from backend.policy_engine import PolicyDecisionEngine, PolicyMandateParser


class ZentroAgentTests(unittest.TestCase):
    def test_default_model_matches_requirements(self):
        from config import get_agent_config
        self.assertEqual(get_agent_config()['model'], 'gemini-3.5-flash')

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

    def test_policy_engine_handles_unavailable_gemini(self):
        parser = PolicyMandateParser(api_key='', gemini_client=None)
        result = parser.parse('Buy electronics under ₹5,000.')
        self.assertIn('max_transaction_amount', result)
        self.assertIn('allowed_categories', result)

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
