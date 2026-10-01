# Client onboarding and handover guide

## Onboarding (after they say yes)
1. **Collect documents** and mark which are confidential (salary, legal, board papers).
2. **Decide who sees what**: create knowledge bases and set them to *Everyone* or *Restricted* (Settings → Knowledge bases & access). Mark the customer-facing one *Public* if they want the website widget.
3. **Agree the assistant's voice**: name, welcome message, tone, languages, fallback message and human contact.
4. **Get 30 real questions** from their team, with the correct answers. Add them to `scripts/eval_questions_holdout.json` and run `python -m scripts.evaluate`.
5. **Pilot**: review wrong or weak answers together. Usually the fix is a clearer document, not code.
6. **Go live**: add users, share the link, record a 3-minute walkthrough for staff.
7. **Plan updates**: who uploads new versions (Documents → Replace), and a monthly look at Insights → Unanswered questions.

## Handover checklist
- [ ] Live URL, admin login shared securely; demo account removed
- [ ] Knowledge bases and access rules checked with a non-admin login
- [ ] Branding set (logo, colour); widget installed on their site if purchased
- [ ] Test results shared (correct %, source %, refusals)
- [ ] Walkthrough video for staff; one-page guide for admins
- [ ] Support period and response time agreed in writing

## Quick guide for staff (paste into an email)
1. Open the link and sign in.
2. Pick a topic on the left (HR, IT, Products…), then type your question, in English, Urdu or Roman Urdu.
3. Check the source chip under each answer; click it to see the exact passage and open the document.
4. If it can't find the answer, press **Ask a human**.
5. Use 👍 / 👎 so the team knows which answers help.
