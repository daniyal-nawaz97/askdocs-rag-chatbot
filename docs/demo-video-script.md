# Demo script (5 minutes live, or 2-3 minutes as video)

`docs/demo.mp4` follows this script with on-screen captions (re-record: `python -m scripts.record_demo` against a fresh start).

| # | Time | Screen | Say |
|---|---|---|---|
| 1 | 20s | Login | "How many times a day does someone in your company ask the same question?" |
| 2 | 20s | Documents | "These are the company's own documents: HR policy, IT guide, catalogue, refund policy, shipping policy, FAQ." |
| 3 | 60s | Chat | Ask *How many casual leaves do I get?*, then *And for part-time staff?*, then a Roman Urdu question. Point at the source chips. |
| 4 | 20s | Source → document | Click **Open document at page 1**: "the exact passage, highlighted." |
| 5 | 30s | Chat | Ask *Is there a gym membership benefit?*: "It doesn't guess. It says it couldn't find it and offers a human." |
| 6 | 40s | Insights | Top questions, then unanswered questions: "This tells HR which policy to write next." |
| 7 | 30s | `/demo-site` | Open the widget, ask *How long does a refund take?*: "Same assistant on your website." |
| 8 | 30s | Close | Numbers from `docs/results.md`, then: "Send me 5 of your documents and I'll set up a demo on them." |

## 15 demo questions (all prepared and tested)
1. How many casual leaves do I get? *(easy)*
2. And for part-time staff? *(follow-up)*
3. Can I work from home?
4. How do I claim medical reimbursement?
5. What are the office hours in Ramadan?
6. How do I reset my password?
7. How do I connect to the VPN from home?
8. My laptop is broken. What should I do?
9. What is the warranty on the AirCool AC?
10. How long does a refund take? → *And for cash on delivery orders?* *(follow-up)*
11. What warranty does the AirCool 1.5 ton AC have, and how do I make a warranty claim? *(two documents; best shown with AI answers on)*
12. Mujhe saal mein kitni casual chuttiyan milti hain? *(Roman Urdu)*
13. Is there a gym membership benefit? *(not in documents → fallback)*
14. Do you sell televisions? *(not in documents)*
15. What is the salary range for grade G3? *(Management knowledge base: visible to admins only)*

## Before any live demo
- [ ] Try the demo works; Insights already shows sample activity
- [ ] `/demo-site` widget opens
- [ ] If possible, a knowledge base built from the prospect's public documents
- [ ] Latest numbers from `docs/results.md`
