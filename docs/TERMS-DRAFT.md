# Specline — subscription terms

**SUPERSEDED, 6 SEPTEMBER 2026. THIS FILE IS THE BRIEF, NOT THE TERMS.** The operative terms
drafted from it are `site/terms.html`, published at https://specline.co.uk/terms.html, with
`site/privacy.html` alongside. Keep this file as the record of what each clause was meant to
achieve, and give it to the solicitor together with the published wording.

**NEITHER PUBLISHED DOCUMENT HAS BEEN REVIEWED BY A SOLICITOR. THAT REVIEW MUST HAPPEN BEFORE THE
FIRST PAID SUBSCRIPTION IS TAKEN.** Both pages say so on their face.

This file sets out the headings the terms will need and the intent behind each. It is a brief for
the solicitor, not a legal document. Nothing below is finished wording and nothing below has been
checked against the Consumer Rights Act 2015, UK GDPR, the Unfair Contract Terms Act 1977, or the
rules on business-to-business contracts. Where a clause has a number in it, that number is a
placeholder to be confirmed.

Provider: SY Design Studio Ltd, trading as Specline. 49 Durham Avenue, Hounslow TW5 0HG.

---

## 1. Subscription and renewal

Intent: the product is sold only by subscription (Solo, Practice) or per issued specification
(Per spec). Never a perpetual licence. Monthly plans renew monthly; annual plans renew annually at
the then-current price unless the founding-member lock applies. State the cancellation notice
period, what happens to access at the end of a paid period, and whether unused time is refunded
(intent: no refund on monthly; pro-rata on annual to be decided). State how price changes are
notified and how far in advance. Founding-member pricing: the first 30 subscribers keep their
joining price for as long as the subscription is continuous.

## 2. The subscriber remains the responsible designer

Intent: the person or practice issuing the specification is the designer of record and carries
the professional responsibility for it. Specline supplies text and calculations that the designer
selects, checks and issues under their own name. The subscriber warrants that they are competent
to do so, holds any professional indemnity insurance their work requires, and will check every
figure against the Approved Documents and standards in force at the date of submission. Nothing
in the product replaces the judgement of a competent designer or the design of a structural
engineer or other specialist.

## 3. A drafting aid, not a compliance certification

Intent: this is the clause that must be exact. Specline drafts specifications. It does not certify,
approve, warrant or guarantee that any specification, building, or element of work complies with
the Building Regulations or will be accepted by a building control body. Building control approves
the work; the software drafts the document. No output of the product is a certificate, an
approval, a plan check, or an opinion on compliance. Marketing and the product interface must be
consistent with this clause; the solicitor should read the website and the app's "Review and
issue" step against it.

## 4. Limitation of liability

Intent: exclude liability for loss arising from the use of a specification on a project to the
fullest extent the law allows, given clause 2 and clause 3. Cap remaining liability at a figure to
be decided (intent: the fees paid in the preceding 12 months). Do not attempt to exclude liability
for death or personal injury caused by negligence, for fraud, or for anything else that cannot
lawfully be excluded. The solicitor should advise on whether the cap and the exclusions hold for
business subscribers and whether any part of the customer base could be a consumer.

## 5. Currency of the library, and what we commit to when the Approved Documents change

Intent: the library is maintained against the Approved Documents for England. State what
"maintained" commits us to: a target period within which the library is reviewed after a new
edition of an Approved Document is published (intent: to be decided; the 2026 editions of L1 and
F1 are the first test, in force 24 March 2027). State plainly that a specification generated
before a change is not retrospectively updated, that the flag the product places on every
document is the subscriber's prompt to check the edition in force, and that transitional
provisions are for the subscriber to apply to their own project. State that Wales, Scotland and
Northern Ireland are not covered unless and until a region is added.

## 6. Ownership of the specifications a subscriber generates

Intent: the subscriber owns the specification documents they issue and may use them freely on
their own projects under their own name. Specline retains all rights in the library text, the
calculations and the software; the licence to use them is for generating the subscriber's own
specifications only. The subscriber may not extract, republish, resell or build a competing
library from the clause text. Clauses the subscriber adds under the Practice tier remain the
subscriber's. State what a subscriber may keep after the subscription ends (intent: every document
they issued, in the form they downloaded it).

## 7. Termination, and what happens to saved jobs

Intent: either side may end the subscription with the notice in clause 1. Specline may suspend or
end access for non-payment, breach of clause 6, or misuse. On termination, state how long saved
jobs remain retrievable and in what form (intent: a period to be decided, then deletion; the
subscriber is told to export before the end). Issued documents already downloaded are unaffected.
State what happens to a Practice tier's shared library when the practice leaves and when one seat
leaves.

## 8. Data protection

Intent: identify the controller (SY Design Studio Ltd) and what is processed: the practice
profile, user accounts, the job records and the site addresses and client names inside them, and
usage data. State the lawful basis, retention, sub-processors (the hosting provider and any
payment processor once one exists), and the subscriber's rights. The job records will contain
third-party personal data (clients, site addresses): state whether Specline is a processor for
that data on the subscriber's behalf and provide the processing terms UK GDPR Article 28 requires.
A separate privacy notice will be needed for the website.

---

Open questions for the solicitor, in priority order:

1. Does clause 3 hold as written, and does the product interface need a click-through
   acknowledgement at the point of issue?
2. Is a five-seat Practice tier a single contracting party, and how do seat-holders' obligations
   under clause 2 attach?
3. Governing law and jurisdiction: England and Wales.
4. Whether any subscriber could be a consumer, and what that changes.
5. Auto-renewal. Monthly and annual subscriptions renew unless cancelled. What notice does a
   subscriber get before an annual renewal is taken, what notice must they give to stop it, and
   does the answer change if any subscriber turns out to be a consumer (question 4)?
6. Founding-member pricing is a promise to hold a price "for as long as the subscription is
   continuous". Is that enforceable as written, what breaks continuity (a lapsed card, a
   downgrade, a gap of one day), and can it be withdrawn on notice if costs move?
7. Per-spec credits are paid for in advance and spent on issue. Do unspent credits expire, are
   they refundable, and what happens to them if the subscriber closes the account or Specline
   stops trading?
8. Refunds. Intent is no refund on a monthly period already started, and pro-rata on an annual
   cancellation — but that intent is not settled and clause 1 says so. What is defensible?
9. VAT. Prices are quoted excluding VAT throughout. Confirm the display obligation for a B2B
   product sold from a UK company, and what changes at the registration threshold.
10. Price rises. Clause 1 says renewal is "at the then-current price". What notice period and
    what right to cancel does that need beside it?
11. Failed payment. How long may access continue while a payment is retried, and is suspending
    the tool (jobs kept, nothing deleted) sound?

---

## Billing, as built — for the solicitor and for whoever maintains it

Written 9 September 2026 alongside `site/app/billing.php`. Nothing here charges anyone: no
payment processor is connected and no card is held.

- **Entitlement is separate from intention.** `practices.plan` is what a practice says it wants
  on its own account page. What it may actually use is a row in `entitlements`, written only by
  the administrator (and later by a processor's webhook). The two were the same field until
  billing existed, which would have let any practice grant itself the Practice tier.
- **Enforcement is a switch, off by default** (`billing_enforce`). With it off the site behaves
  exactly as it did before. With it on, `app.php` and `api.php` both refuse a practice with no
  entitlement — the tool and the store together, because a store left open is a tool left open.
- **Nothing is deleted when a subscription ends.** The refusal page says so, and means it: jobs
  and the practice profile are untouched, which is also what clause 7 of these terms promises.
- **Per-spec is a ledger.** Credits bought or granted are positive rows, an issue is a negative
  row naming the job. A balance can always be explained, which is what a customer will ask for.
- **The vendor's own account is never locked out**, so a billing mistake cannot lock the
  administrator out of the administration.

Still to do, and stated plainly because a half-built payment path is worse than none:

1. ~~Choose the processor.~~ **Stripe, chosen 9 September 2026 and built the same day**
   (`site/app/stripe.php`, `docs/STRIPE-SETUP.md`). SY Design Studio Ltd is therefore the seller
   of record and handles VAT itself: prices are quoted excluding VAT throughout, and question 9
   below is the one to put to the solicitor and the accountant before the first live charge.
   Cancellation and card changes are handled by Stripe's own billing portal, so clause 1's
   cancellation mechanics must match what that portal actually does.
2. ~~The webhook.~~ **Built.** `/webhook.php` verifies Stripe's signature and writes
   `entitlements` on created, updated, deleted, paused and resumed, and credits on a paid
   checkout. Two behaviours the solicitor should know about because they are promises to a
   customer: a subscription in `past_due` keeps working while Stripe retries the card (see
   question 11), and ending a subscription deletes nothing at all.
3. **Issuing must spend a credit.** The server side is built (`/api.php` op `spec.issue`, which
   is honest about whether it charged); the app has still to call it at the moment of issue.
   Until it does, per-spec cannot be enforced and only subscriptions can be sold.
4. **The solicitor**, on questions 5 to 11 above, before the first card is charged.
