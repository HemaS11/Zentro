document.addEventListener('DOMContentLoaded', () => {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach((item) => {
    item.addEventListener('click', () => {
      navItems.forEach((nav) => nav.classList.remove('active'));
      item.classList.add('active');
    });
  });

  const cards = document.querySelectorAll('.agent-card');
  const summaryEl = document.getElementById('agent-focus-summary');
  const titleEl = document.getElementById('agent-focus-title');
  const jsonEl = document.getElementById('agent-json');

  const agentDetails = {
    'Mandate Creator': {
      summary: 'Mandate Creator is aligning the client policy framework, validating spend rules, and enabling approval flows without breaking the premium threshold.',
      json: '{\n  "agent": "Mandate Creator",\n  "decision": "APPROVE",\n  "confidence": 0.97,\n  "risk_score": 12,\n  "matched_policy": "Travel Luxury"\n}'
    },
    'Product Research': {
      summary: 'Product Research matched the merchant and category to the client’s preferred shopping behavior and premium purchasing pattern.',
      json: '{\n  "agent": "Product Research",\n  "decision": "REVIEW",\n  "confidence": 0.91,\n  "risk_score": 18,\n  "matched_policy": "Luxury Retail"\n}'
    },
    'Policy Judge': {
      summary: 'Policy Judge is running the compliance check across thresholds, rules, and exception patterns before the transaction reaches final clearance.',
      json: '{\n  "agent": "Policy Judge",\n  "decision": "CHECKING",\n  "confidence": 0.88,\n  "risk_score": 24,\n  "matched_policy": "Compliance Review"\n}'
    },
    'Risk Detection': {
      summary: 'Risk Detection isolated a duplicate pattern and a category drift signal, prompting a more conservative risk review for this transaction.',
      json: '{\n  "agent": "Risk Detection",\n  "decision": "ESCALATE",\n  "confidence": 0.82,\n  "risk_score": 71,\n  "matched_policy": "Fraud Sweep"\n}'
    },
    'Receipt Auditor': {
      summary: 'Receipt Auditor confirmed the merchant and receipt metadata match the approved transaction, closing the audit trail successfully.',
      json: '{\n  "agent": "Receipt Auditor",\n  "decision": "APPROVE",\n  "confidence": 0.96,\n  "risk_score": 9,\n  "matched_policy": "Document Integrity"\n}'
    }
  };

  function activateAgent(card) {
    cards.forEach((other) => other.classList.remove('is-active'));
    card.classList.add('is-active');

    const agentName = card.dataset.agent;
    const detail = agentDetails[agentName];

    if (titleEl && summaryEl && jsonEl && detail) {
      titleEl.textContent = agentName;
      summaryEl.textContent = detail.summary;
      jsonEl.textContent = detail.json;
    }
  }

  cards.forEach((card) => {
    card.addEventListener('click', () => activateAgent(card));
    card.addEventListener('mouseenter', () => activateAgent(card));
  });

  const primaryButton = document.querySelector('.primary-btn');
  const badge = document.querySelector('.badge.approve');
  if (primaryButton && badge) {
    primaryButton.addEventListener('click', () => {
      badge.textContent = 'APPROVED';
      badge.style.background = 'rgba(102, 132, 92, 0.12)';
      badge.style.color = '#486A42';
    });
  }
});
