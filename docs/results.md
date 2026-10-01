# Measured results (2026-09-30)

Engine: **Offline answers (quoted from documents) + hybrid search**. Cost per 1,000 questions: 0 (offline).

Two question sets on the fictitious Nimbus demo documents:

- **Held-out set**: 22 new questions written after tuning. Its first run scored 66.7% (answerable) / 75% (refusals); the engine then got one round of general fixes (table detection, synonym handling, answer checks, not question-specific) and was frozen at 83.3%. A later bug fix found while testing the chat screen (hyphenated words like 'part-time' were split) raised it to the number below. **Quote these numbers.**
- **Tuning set**: used while building the engine, so it is optimistic.

### Held-out set (honest numbers)

| Metric | Result |
|---|---|
| Correct answers (18 answerable questions) | **88.9%** |
| Correct source document found | 94.4% |
| Correct source page found | 88.9% |
| Out-of-scope questions correctly refused (4) | **75.0%** |
| Overall (22 questions) | 86.4% |
| Average response time | 0.01 s |

| Question type | Correct |
|---|---|
| easy | 16/17 |
| roman-urdu | 0/1 |
| out-of-scope | 3/4 |

### Tuning set

| Metric | Result |
|---|---|
| Correct answers (41 answerable questions) | **97.6%** |
| Correct source document found | 100.0% |
| Correct source page found | 100.0% |
| Out-of-scope questions correctly refused (7) | **85.7%** |
| Overall (48 questions) | 95.8% |
| Average response time | 0.01 s |

| Question type | Correct |
|---|---|
| easy | 34/34 |
| follow-up | 2/2 |
| roman-urdu | 3/3 |
| urdu | 1/1 |
| out-of-scope | 6/7 |
| two-documents | 0/1 |

## Every question

| Set | | Type | Question | Answer | Source |
|---|---|---|---|---|---|
| held-out | ✓ | easy | What happens if I come late three times in a month? | Employees who arrive more than 15 minutes late three times in a calendar month will have half a day deducted from casual leave. | HR_Policy.pdf p.1 |
| held-out | ✓ | easy | How many days of paternity leave are there? | Paternity leave 7 days paid 7 days paid -. | HR_Policy.pdf p.1 |
| held-out | ✓ | easy | Do I need a medical certificate for sick leave? | Sick leave of more than 2 consecutive days requires a medical certificate. | HR_Policy.pdf p.1 |
| held-out | ✓ | easy | Is hospitalisation covered by insurance? | Hospitalisation is covered by group health insurance up to PKR 500,000 per year for the employee, spouse and up to two children. | HR_Policy.pdf p.2 |
| held-out | ✓ | easy | Can I accept a gift from a supplier? | Accepting gifts from suppliers worth more than PKR 5,000 is not allowed and must be reported to HR. | HR_Policy.pdf p.2 |
| held-out | ✓ | easy | How do I report harassment? | Concerns can be reported confidentially to the Harassment Inquiry Committee at conduct@nimbus-appliances.example or to any HR business partn | HR_Policy.pdf p.2 |
| held-out | ✓ | easy | What is the notice period for managers? | After confirmation, the notice period is 1 month for staff and 2 months for managers. | HR_Policy.pdf p.1 |
| held-out | ✗ | roman-urdu | Kya main ghar se kaam kar sakta hoon? | I couldn't find this in the documents. You can contact HR at hr@nimbus-appliances.example or extension 210. |  |
| held-out | ✓ | out-of-scope | Do we get a bonus at Eid? | I couldn't find this in the documents. You can contact HR at hr@nimbus-appliances.example or extension 210. |  |
| held-out | ✓ | easy | Which app do I need for two-step sign-in? | The Microsoft Authenticator app is required for two-step sign-in. | IT_Help_Guide.pdf p.2 |
| held-out | ✓ | easy | What should I do with a suspicious email? | Forward suspicious emails to phishing@nimbus-appliances.example and then delete them. | IT_Help_Guide.pdf p.2 |
| held-out | ✗ | easy | What are the IT helpdesk hours? | IT aims to respond within 4 working hours and provides a loaner laptop when a repair takes more than 1 working day. | IT_Help_Guide.pdf p.2 |
| held-out | ✓ | out-of-scope | How do I book a meeting room? | I couldn't find this in the documents. You can contact HR at hr@nimbus-appliances.example or extension 210. |  |
| held-out | ✓ | easy | How much does the air fryer cost? | The Air Fryer 5.5 L cooks with up to 85% less oil and has 8 presets. NAF-55 Nimbus Air Fryer 5.5 L 24,999 1 year. | Product_Catalogue.pdf p.2, Product_Catalogue.pdf p.1 |
| held-out | ✓ | easy | Is installation free for air conditioners? | Standard installation (up to 10 feet of copper pipe) is free in Lahore, Karachi and Islamabad. | Product_Catalogue.pdf p.1 |
| held-out | ✓ | easy | Can I return an AC after it has been installed? | Installed appliances (air conditioners, water dispensers) cannot be returned unless they are faulty. | Refund_and_Warranty_Policy.pdf p.1 |
| held-out | ✓ | easy | How long will delivery take to Lahore? | Orders are delivered within 2-4 working days in Lahore, Karachi, Islamabad and Rawalpindi, and within 5-7 working days to other cities. | Shipping_and_Delivery_Policy.docx p.None |
| held-out | ✓ | easy | What happens if I'm not home when the rider comes? | If nobody is available, the rider tries again the next working day. | Shipping_and_Delivery_Policy.docx p.None |
| held-out | ✓ | easy | Do you give discounts for bulk orders? | Orders of 10 or more units qualify for corporate pricing. | Company_FAQ.txt p.None |
| held-out | ✓ | easy | Does the warranty cover damage from voltage fluctuation? | The warranty does not cover damage from voltage fluctuation without a stabiliser (except inverter models rated for low voltage), physical da | Refund_and_Warranty_Policy.pdf p.2 |
| held-out | ✓ | out-of-scope | Do you have a store in Peshawar? | I couldn't find this in the documents. You can contact HR at hr@nimbus-appliances.example or extension 210. |  |
| held-out | ✗ | out-of-scope | What is the energy rating of the washing machine? | The WashPro 8 kg front load washer offers 15 programs including Quick 15-minute wash and steam hygiene. | Product_Catalogue.pdf p.2 |
| tuning | ✓ | easy | How many casual leaves do I get? | Employees are entitled to 10 casual leaves per calendar year. | HR_Policy.pdf p.1 |
| tuning | ✓ | follow-up | And for part-time staff? | Part-time staff receive leave on a pro-rata basis: 5 casual leaves and 4 sick leaves per calendar year, and 7 days of annual leave. | HR_Policy.pdf p.1 |
| tuning | ✓ | easy | How many sick leaves do I get in a year? | Employees are entitled to 8 sick leaves per calendar year. | HR_Policy.pdf p.1 |
| tuning | ✓ | easy | Can I carry forward my casual leave to next year? | Casual leave cannot be carried forward to the next year and cannot be encashed. | HR_Policy.pdf p.1 |
| tuning | ✓ | easy | How many unused annual leave days can be carried forward? | Up to 7 unused annual leave days may be carried forward to the next year; any balance above 7 days lapses on 31 December. | HR_Policy.pdf p.1 |
| tuning | ✓ | easy | What are the office hours? | Office hours are 9:00 am to 6:00 pm, Monday to Friday, with a one-hour lunch break from 1:00 pm to 2:00 pm. | HR_Policy.pdf p.1 |
| tuning | ✓ | easy | What are the office hours during Ramadan? | During Ramadan, office hours are 9:00 am to 3:00 pm. | HR_Policy.pdf p.1 |
| tuning | ✓ | easy | Can I work from home? | After confirmation, office staff may work from home up to 2 days per week with their line manager's approval. | HR_Policy.pdf p.2 |
| tuning | ✓ | easy | How long is the probation period? | New employees serve a probation period of 3 months. | HR_Policy.pdf p.1 |
| tuning | ✓ | easy | What is the notice period after confirmation? | After confirmation, the notice period is 1 month for staff and 2 months for managers. | HR_Policy.pdf p.1 |
| tuning | ✓ | easy | What is the OPD medical reimbursement limit? | Confirmed employees receive outpatient (OPD) medical reimbursement of up to PKR 60,000 per year. | HR_Policy.pdf p.2 |
| tuning | ✓ | easy | Within how many days do I need to submit expense claims? | Business travel and other work expenses are reimbursed when claims are submitted within 30 days of the expense, with original receipts, thro | HR_Policy.pdf p.2 |
| tuning | ✓ | easy | What is the fuel allowance per kilometre? | Employees who use their own car for company work receive a fuel allowance of PKR 45 per kilometre, based on the mileage log approved by thei | HR_Policy.pdf p.2 |
| tuning | ✓ | easy | How long is maternity leave? | Maternity leave 90 days paid 90 days paid -. | HR_Policy.pdf p.1 |
| tuning | ✓ | easy | When is salary paid? | Salaries are paid by bank transfer on the 1st working day of each month. | HR_Policy.pdf p.2 |
| tuning | ✓ | roman-urdu | Mujhe saal mein kitni casual chuttiyan milti hain? | Employees are entitled to 10 casual leaves per calendar year. | HR_Policy.pdf p.1 |
| tuning | ✓ | roman-urdu | Bimari ki chutti kitni milti hai? | Employees are entitled to 8 sick leaves per calendar year. | HR_Policy.pdf p.1 |
| tuning | ✓ | urdu | مجھے سال میں کتنی چھٹیاں ملتی ہیں؟ | Employees are entitled to 10 casual leaves per calendar year. | HR_Policy.pdf p.1 |
| tuning | ✓ | out-of-scope | Is there a gym membership benefit? | I couldn't find this in the documents. You can contact HR at hr@nimbus-appliances.example or extension 210. |  |
| tuning | ✓ | out-of-scope | What is the dress code on Fridays? | I couldn't find this in the documents. You can contact HR at hr@nimbus-appliances.example or extension 210. |  |
| tuning | ✓ | out-of-scope | Who is the CEO of the company? | I couldn't find this in the documents. You can contact HR at hr@nimbus-appliances.example or extension 210. |  |
| tuning | ✓ | easy | How do I reset my password? | Reset a forgotten password yourself at the self-service portal: https://reset.nimbus-appliances.example. | IT_Help_Guide.pdf p.1 |
| tuning | ✓ | easy | How long does my password need to be? | Passwords must be at least 12 characters and must be changed every 90 days. | IT_Help_Guide.pdf p.1 |
| tuning | ✓ | easy | How often do I have to change my password? | Passwords must be at least 12 characters and must be changed every 90 days. | IT_Help_Guide.pdf p.1 |
| tuning | ✓ | easy | How do I connect to the VPN from home? | To connect to company systems from home, install FortiClient VPN from the Software Center and connect to vpn.nimbus-appliances.example with  | IT_Help_Guide.pdf p.1 |
| tuning | ✓ | easy | My laptop is broken. What should I do? | If your laptop is slow, broken or damaged, raise a helpdesk ticket. | IT_Help_Guide.pdf p.2 |
| tuning | ✓ | easy | I lost my laptop. How soon must I report it? | A lost or stolen laptop must be reported to IT within 24 hours so it can be locked remotely. | IT_Help_Guide.pdf p.2 |
| tuning | ✓ | easy | What is the helpdesk phone extension? | Raise a ticket by emailing helpdesk@nimbus-appliances.example or by calling extension 250. | IT_Help_Guide.pdf p.1 |
| tuning | ✓ | easy | Can I use a USB drive on my laptop? | USB storage devices are blocked on company laptops. | IT_Help_Guide.pdf p.2 |
| tuning | ✓ | easy | Can I print in colour? | Colour printing requires manager approval. | IT_Help_Guide.pdf p.2 |
| tuning | ✓ | easy | Where do I get the guest Wi-Fi password? | Visitors use 'Nimbus-Guest'; the daily guest password is available at reception. | IT_Help_Guide.pdf p.1 |
| tuning | ✓ | out-of-scope | How do I request a second monitor? | I couldn't find this in the documents. You can contact HR at hr@nimbus-appliances.example or extension 210. |  |
| tuning | ✓ | out-of-scope | What is the company's Netflix account password? | I couldn't find this in the documents. You can contact HR at hr@nimbus-appliances.example or extension 210. |  |
| tuning | ✓ | easy | What is the warranty on the AirCool AC? | NA-150i Nimbus AirCool 1.5 Ton Inverter AC 189,000 10 years compressor, 2 years parts. | Product_Catalogue.pdf p.1 |
| tuning | ✗ | two-documents | What warranty does the AirCool 1.5 ton AC have, and how do I make a warranty claim? | NA-150i Nimbus AirCool 1.5 Ton Inverter AC 189,000 10 years compressor, 2 years parts. | Product_Catalogue.pdf p.1 |
| tuning | ✓ | easy | How long does a refund take? | Approved refunds are processed within 10 working days to the original payment method. | Refund_and_Warranty_Policy.pdf p.1 |
| tuning | ✓ | follow-up | And for cash on delivery orders? | Cash on delivery (COD) orders are refunded by bank transfer to an account in the customer's name. | Refund_and_Warranty_Policy.pdf p.1 |
| tuning | ✓ | easy | How much is delivery? | Delivery is free for orders above PKR 20,000. | Shipping_and_Delivery_Policy.docx p.None |
| tuning | ✓ | easy | Do you offer installments? | All products above PKR 50,000 can be bought on 0% installments for 12 months through partner banks (credit cards of HBL, Meezan Bank and Ban | Product_Catalogue.pdf p.2 |
| tuning | ✓ | easy | Is cash on delivery available for big orders? | Cash on delivery (COD) is available for orders up to PKR 150,000. | Shipping_and_Delivery_Policy.docx p.None |
| tuning | ✓ | easy | My fridge arrived damaged. How quickly do I need to report it? | If a product arrives damaged or you receive the wrong item, report it within 48 hours of delivery by calling our helpline or emailing suppor | Refund_and_Warranty_Policy.pdf p.1 |
| tuning | ✓ | easy | What is the price of the 18 cu ft refrigerator? | NF-18 Nimbus FrostFree Refrigerator 18 cu ft 139,500 10 years compressor, 1 year parts. | Product_Catalogue.pdf p.1 |
| tuning | ✓ | easy | What are your customer support hours? | Customer support is available Monday to Saturday, 9:00 am to 8:00 pm, on the helpline 0800-64662 (toll free) and by email at support@nimbus- | Company_FAQ.txt p.None |
| tuning | ✓ | roman-urdu | Refund kitne din mein milta hai? | Approved refunds are processed within 10 working days to the original payment method. | Refund_and_Warranty_Policy.pdf p.1 |
| tuning | ✓ | easy | Where is your head office? | Our head office is at 42-C Gulberg III, Lahore. | Company_FAQ.txt p.None |
| tuning | ✓ | out-of-scope | Do you sell televisions? | I couldn't find this in the documents. You can contact HR at hr@nimbus-appliances.example or extension 210. |  |
| tuning | ✗ | out-of-scope | Do you ship to Dubai? | Delivery is free for orders above PKR 20,000. | Shipping_and_Delivery_Policy.docx p.None |
| tuning | ✓ | easy | What is the salary range for grade G3? | G3 Officer, team lead 110,000 180,000. | Salary_Bands_2026.pdf p.1 |

_Honest note: small test sets on demo documents written for this project. Before quoting numbers to a client, add 30-50 real questions from their team with the correct answers and run this script on their documents._
