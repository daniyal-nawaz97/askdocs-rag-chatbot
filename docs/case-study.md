# Case study: an HR, IT and product assistant for a 7-document company

> Built on a fictitious demo company (Nimbus Home Appliances). After your first pilot, copy this page and replace the numbers with the client's measured results (template below).

## Problem
Staff at a mid-size appliance company ask HR and IT the same questions every day: leave balances, reimbursement rules, password resets, VPN setup. Customers ask support the same things about delivery, refunds and warranty. The answers exist in 7 documents, but nobody can find them quickly, and chatbots that "make things up" aren't acceptable for policy questions.

## Solution
AskDocs, a chat assistant over the company's own documents. It searches by meaning and keywords, answers only from the passages it finds, shows the file and page for every answer, and says "I couldn't find this" when the documents don't cover it. HR and IT use it internally; the product knowledge base powers a website chat widget. Confidential salary bands are restricted to management.

## Result (measured with `scripts/evaluate.py`, offline mode)

| | Held-out questions (22) |
|---|---|
| Correct answers | **88.9%** of answerable questions |
| Correct source document shown | **94.4%** |
| Questions not in the documents correctly refused | **3 of 4** |
| Average answer time | under 0.1 s (offline mode) |
| Cost per 1,000 questions | 0 (offline); Groq free tier for AI answers |

Covered question types: simple facts, follow-ups ("And for part-time staff?"), a question needing two documents, Roman Urdu and Urdu questions, and questions deliberately outside the documents.

**What the Insights screen shows the client:** the most asked questions (password reset, work from home, casual leave), and the gaps, e.g. "Is there a gym membership benefit?" asked 6 times with no answer, which tells HR exactly which policy to write next.

## Screenshot
![Answer with source](screenshots/chat.png)

## Link
Live demo: *(your deployed URL)* → **Try the demo**. Website widget: *(your URL)*/demo-site

---

### Template for a real client case study
- **Client:** (type of organisation; name only with permission)
- **Problem:** which questions repeat, who answers them today, how much time it takes
- **Solution:** (2-3 lines) documents loaded, knowledge bases, channels (staff app / website / WhatsApp)
- **Result:** % correct on their 30-50 test questions · % correct source · refusals · questions per week after launch · top knowledge gaps found
- **Quote:** one sentence from the client
