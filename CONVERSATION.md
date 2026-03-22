# COPILOT_SESSION.md — VISA Dispute Advisor Demo

Demo session with GitHub Copilot (Ask mode) using the visa-dispute-advisor MCP server.
Server running via `uv run visa-advisor`. Client: GitHub Copilot in VS Code.

---

## Verify tools are available

**User:**
```
Do you see the visa-dispute-advisor tools?
```

**Copilot:**
```
Yes, I can see the visa-dispute-advisor tools defined in the MCP server.
The server exposes two read-only tools:

1. search_visa_rules(scenario): Searches VISA Dispute Management Guidelines
   for rules relevant to a dispute scenario. It takes a free-text description
   and returns a ranked list of matching VISA rule candidates with details like
   condition ID, title, snippet, and relevance score.

2. query_warehouse(merchant_id): Retrieves dispute history for a specific
   merchant from the data warehouse. It takes a merchant ID (e.g., "MER-001")
   and returns information including merchant details, total cases, resolution
   breakdown, and individual case records.

The server is configured to run via `uv run visa-advisor` and includes
instructions to always search VISA rules first, then query the warehouse,
and combine results to recommend accepting/rejecting disputes or requesting
more evidence.
```

---

## Case 1 — Merchandise Not Received

**User:**
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

**Copilot:**
```
🔧 Calling search_visa_rules("merchandise not received dispute with carrier tracking")...
→ Condition 13.1 — Merchandise/Services Not Received (score: 0.92)

🔧 Calling query_warehouse("MER-001")...
→ Tech Store Guatemala: 10 prior cases — 7 merchant_won, 2 merchant_lost, 1 settled

📋 RECOMMENDATION: REJECT DISPUTE

Applicable rule: Condition 13.1 — Merchandise/Services Not Received
This rule applies as the dispute involves a claim of non-receipt of merchandise
ordered online, with the merchant providing carrier tracking evidence of delivery
to the billing address, even though no signature was collected.

Merchant risk profile: LOW RISK
The merchant has a strong history of winning disputes (70% win rate), with only
minor losses and one settlement, indicating reliable operations and low risk of
fraudulent activity.

Next steps:
1. Provide the carrier tracking details and delivery confirmation to VISA for review.
2. Contact the customer to offer alternative resolution options, such as a replacement
   or refund if they provide further evidence.
3. Monitor for any follow-up disputes from this cardholder to assess potential patterns.
```

---

## Case 2 — Cancelled Recurring Transaction

**User:**
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

**Copilot:**
```
🔧 Calling search_visa_rules("recurring billing dispute after claimed cancellation")...
→ Condition 12.1 — Recurring Billing (score: 0.88)

🔧 Calling query_warehouse("MER-002")...
→ Ropa Online SA: 5 prior cases — 3 merchant_won, 1 merchant_lost, 1 settled

📋 RECOMMENDATION: REQUEST MORE EVIDENCE

Applicable rule: Condition 12.1 — Recurring Billing
This rule applies as the dispute involves a recurring subscription charge where
the cardholder claims cancellation via email, but the merchant asserts no
cancellation was received and the service remained active.

Merchant risk profile: MEDIUM RISK
The merchant has a moderate history with 60% win rate in prior disputes, including
one loss and one settlement, suggesting some inconsistency in handling subscription
cancellations.

Next steps:
1. Request the cardholder's email confirmation of the cancellation request for verification.
2. Provide merchant's internal records showing no received cancellation and proof
   of service continuation.
3. Escalate to VISA for review if additional evidence is needed to resolve the dispute.
```

---

## Case 3 — Defective Merchandise

**User:**
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

**Copilot:**
```
🔧 Calling search_visa_rules("damaged merchandise not matching description")...
→ Condition 13.3 — Not as Described or Defective Merchandise (score: 0.90)

🔧 Calling query_warehouse("MER-003")...
→ Electrodomésticos XYZ: 8 prior cases — 4 merchant_won, 3 merchant_lost, 1 settled

📋 RECOMMENDATION: ACCEPT DISPUTE

Applicable rule: Condition 13.3 — Not as Described or Defective Merchandise
This rule applies as the dispute involves merchandise that arrived damaged and
did not match the website description, with the merchant refusing replacement
and providing only a claim of pre-shipment inspection without evidence.

Merchant risk profile: MEDIUM RISK
The merchant has a balanced history with 50% win rate, but 3 losses indicate
potential issues with product quality assurance or customer service in handling
defective items.

Next steps:
1. Issue a full refund to the cardholder and arrange for product pickup.
2. Review internal quality control processes to prevent future shipping damages.
3. Contact the manufacturer to confirm warranty terms and improve referral procedures.
```
