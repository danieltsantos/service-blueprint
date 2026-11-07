# Assisted invoice disputes: concept (workshop output, 5 Nov)

Synthetic test material.

## Problem
B2B customers who disagree with an invoice email billing@ or call their account manager. Disputes sit in a shared inbox for 6 working days on average (billing team estimate, not measured). Customers often pay late while they wait, which triggers automatic dunning letters.

## Concept
The in-product assistant handles the first contact for invoice questions and disputes.

1. Customer opens an invoice in the portal and taps "Question this invoice", or asks the assistant in chat.
2. Assistant reads the invoice lines, the contract price list and usage records. It explains the charge.
3. If the customer still disagrees, the assistant opens a dispute case in the billing system with the disputed lines and the customer's reason.
4. Opening a case pauses dunning for that invoice. **Decided** (Finance, 5 Nov).
5. Billing analyst reviews the case. Outcomes: credit note issued in the ERP, or dispute rejected with a reason.
6. Customer is notified by email and in the portal. Case status visible in the portal: Open, Under review, Resolved.

## Decisions
- Assistant never promises a credit. It can only explain and open a case. (Legal, 5 Nov)
- Credit notes over €5,000 need a second approval from the finance controller. (Finance)
- Release 1: portal entry point only. Chat entry point comes in release 2.

## Open questions
- What does the assistant do when usage records are missing or late?
- Who owns the case if the billing analyst needs information from the account manager?
- Do we tell the customer an expected resolution date? Billing does not want to commit to one.
- How does a customer reopen a resolved dispute?

## Not discussed
- Partial credits across several invoices.
- What happens to a dunning letter already sent before the case was opened.
