### Case 1 — Merchandise Not Received

```
Analyze this VISA dispute case and give me a recommendation.

## Dispute Case CASE-007

- **Merchant ID:** MER-001
- **Merchant Name:** Tech Store Guatemala
- **Date:** 2026-03-15
- **Amount:** $450.00
- **Cardholder claim:** The customer says they never received the laptop
  they ordered online. Order placed 2026-03-01, expected delivery 2026-03-10.
  Carrier tracking shows "delivered" but the customer denies receiving it.
- **Merchant response:** Merchant has carrier tracking proof showing delivery
  to the billing address. No signature was collected at delivery.

Use search_visa_rules and query_warehouse before answering.
Structure your response exactly like this:

🔧 Calling search_visa_rules("...")...
→ Condition XX.X — [Title] (score: 0.XX)

🔧 Calling query_warehouse("MER-XXX")...
→ [Merchant Name]: X prior cases — X merchant_won, X merchant_lost, X settled

📋 RECOMMENDATION: [ACCEPT DISPUTE | REJECT DISPUTE | REQUEST MORE EVIDENCE]

Applicable rule: Condition XX.X — [Title]
[Explanation of why this rule applies to the case]

Merchant risk profile: [LOW | MEDIUM | HIGH] RISK
[Summary of merchant's dispute history]

Next steps:
1. [Action item]
2. [Action item]
3. [Action item]
```

---

### Case 2 — Cancelled Recurring Transaction

```
Analyze this VISA dispute case and give me a recommendation.

## Dispute Case CASE-008

- **Merchant ID:** MER-002
- **Merchant Name:** Ropa Online SA
- **Date:** 2026-02-28
- **Amount:** $35.00
- **Cardholder claim:** The customer cancelled their monthly subscription
  on 2026-01-15 via email. The merchant charged them again on 2026-02-01
  and has not issued a refund.
- **Merchant response:** Merchant claims the cancellation request was never
  received and that the service was still active.

Use search_visa_rules and query_warehouse before answering.
Structure your response exactly like this:

🔧 Calling search_visa_rules("...")...
→ Condition XX.X — [Title] (score: 0.XX)

🔧 Calling query_warehouse("MER-XXX")...
→ [Merchant Name]: X prior cases — X merchant_won, X merchant_lost, X settled

📋 RECOMMENDATION: [ACCEPT DISPUTE | REJECT DISPUTE | REQUEST MORE EVIDENCE]

Applicable rule: Condition XX.X — [Title]
[Explanation of why this rule applies to the case]

Merchant risk profile: [LOW | MEDIUM | HIGH] RISK
[Summary of merchant's dispute history]

Next steps:
1. [Action item]
2. [Action item]
3. [Action item]
```

---

### Case 3 — Defective Merchandise

```
Analyze this VISA dispute case and give me a recommendation.

## Dispute Case CASE-009

- **Merchant ID:** MER-003
- **Merchant Name:** Electrodomésticos XYZ
- **Date:** 2026-01-20
- **Amount:** $899.00
- **Cardholder claim:** Customer received a refrigerator but it arrived
  with a broken door hinge and internal damage. The product did not match
  the description shown on the website. Merchant refused to replace it and
  referred the customer to the manufacturer.
- **Merchant response:** Merchant claims the product was inspected before
  shipping and left the warehouse in perfect condition.

Use search_visa_rules and query_warehouse before answering.
Structure your response exactly like this:

🔧 Calling search_visa_rules("...")...
→ Condition XX.X — [Title] (score: 0.XX)

🔧 Calling query_warehouse("MER-XXX")...
→ [Merchant Name]: X prior cases — X merchant_won, X merchant_lost, X settled

📋 RECOMMENDATION: [ACCEPT DISPUTE | REJECT DISPUTE | REQUEST MORE EVIDENCE]

Applicable rule: Condition XX.X — [Title]
[Explanation of why this rule applies to the case]

Merchant risk profile: [LOW | MEDIUM | HIGH] RISK
[Summary of merchant's dispute history]

Next steps:
1. [Action item]
2. [Action item]
3. [Action item]
```
