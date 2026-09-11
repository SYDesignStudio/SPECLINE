# Connecting Stripe

Everything on the Specline side is built. This is the half that happens in the Stripe dashboard
and in one file on the server, in the order to do it.

**Do it in test mode first, all the way through.** The admin Billing page shows `TEST` or `LIVE`
read from the key itself, so there is no way to be in one and think you are in the other.

**Never paste a key into a chat, an email, a commit or a support ticket.** The only place a secret
key belongs is the config file in step 3, which sits above the web root where no deployment can
overwrite it and this repository cannot leak it. If a key is ever exposed, roll it in Stripe
first and update the file second.

---

## 1. Create the products and prices

In Stripe, **Products → Add product**. Prices exclude VAT; add tax behaviour later if and when
SY Design Studio Ltd registers.

| Product | Price | Billing | Gives you |
|---|---|---|---|
| Specline Solo | £39 | Recurring, monthly | `price_…` for Solo monthly |
| Specline Solo | £390 | Recurring, yearly | `price_…` for Solo annual |
| Specline Practice | £89 | Recurring, monthly | `price_…` for Practice monthly |
| Specline Practice | £890 | Recurring, yearly | `price_…` for Practice annual |
| Specification credit | £25 | **One-off** | `price_…` for per-spec |

Add the annual price to the *same* product as the monthly one — two prices, one product — so a
subscriber can switch between them in the billing portal without a new subscription.

The five identifiers are not secret. Copy them; they go into the admin page in step 4.

## 2. Create the webhook

**Developers → Webhooks → Add endpoint.**

- Endpoint URL: `https://specline.co.uk/webhook.php`
- Events to send:
  - `checkout.session.completed`
  - `customer.subscription.created`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `customer.subscription.paused`
  - `customer.subscription.resumed`

Stripe then shows a **signing secret** beginning `whsec_`. That is the one thing standing between
this and a stranger granting themselves a subscription by posting to a public address, so it
matters more than the API key. Copy it for step 3.

Nothing else needs to be sent. The endpoint answers `200` to events it does not act on, so extra
events are harmless — they are simply recorded and ignored.

## 3. Put the keys above the web root

Over SFTP or File Manager, edit (or create) `specline-config.php` in the **domain directory above
`public_html`** — the same directory that holds `specline.sqlite` and the waiting-list CSV. It
returns one array; keep any keys that are already in it:

```php
<?php return [
    'base_url'              => 'https://specline.co.uk',
    'payment_processor'     => 'stripe',
    'stripe_secret_key'     => 'sk_test_…',   // sk_live_… when you go live
    'stripe_webhook_secret' => 'whsec_…',
];
```

That file is never deployed, never committed and never served. If it is missing, the site runs
exactly as it does today and simply cannot charge anyone.

## Where this got to on 9 September 2026

Steps 1, 2 and 4 are **done in test mode**. The three products and five prices exist, the webhook
destination `Specline` is Active on `https://specline.co.uk/webhook.php` listening to the six
events, and the admin page reads **Prices set up 5 of 5**. The test-mode identifiers saved there:

| | Price |
|---|---|
| Solo monthly | `price_1UDXzVKGvzcMFbObWc5vzmYi` |
| Solo annual | `price_1UDY1HKGvzcMFbObYfgIqYrA` |
| Practice monthly | `price_1UDY2HKGvzcMFbObwI3qe0OM` |
| Practice annual | `price_1UDY30KGvzcMFbObrOKMuPPs` |
| Specification credit | `price_1UDY40KGvzcMFbObaJbsus5S` |

**Step 3 is yours, and is the only thing between here and a working test payment**: the secret key
and the webhook signing secret into `specline-config.php`. The signing secret is on the
destination's own page in Stripe, behind the reveal icon beside *Signing secret*. Until both are
there the admin page reads `Secret key NOT SET` and `Webhook secret NOT SET`, and nothing can be
charged.

The destination was created on API version **2026-06-24.dahlia**, which carries
`current_period_end` on the subscription ITEM rather than on the subscription. `stripe_period_end()`
reads both shapes and returns nothing rather than a guess when neither is present.

## Where LIVE mode got to on 9 September 2026

Everything that can be done without a key is done. The three products and five prices exist in live
mode, the destination **Specline** is Active on `https://specline.co.uk/webhook.php` listening to
the same six events, and both sets of identifiers are saved on the admin page, which reads
`Prices set up · test in use 5 of 5` and `Prices set up · live 5 of 5 ready for when the key is
live`. The live identifiers, which are not secret:

| | Price |
|---|---|
| Solo monthly | `price_1UDZVXKGvzcMFbObuY09fYVV` |
| Solo annual | `price_1UDZXFKGvzcMFbOb3gw5tWNt` |
| Practice monthly | `price_1UDZYqKGvzcMFbObEWqLsDEz` |
| Practice annual | `price_1UDZYqKGvzcMFbOb9M1lEnwr` |
| Specification credit | `price_1UDZZpKGvzcMFbObRHJ0SEXc` |

**It is live and proven.** The keys went in on the evening of 9 September 2026 and a real £25
specification credit was bought with a real card at 02:38. Everything answered: the payment
succeeded in Stripe, the webhook delivered at a 0 per cent error rate, the admin page recorded
*practice 1 bought 1 credit*, the ledger shows `+1 bought · stripe`, and the account page reads
*Specification credits 1*. The refusal counter did not move, which is the only proof that exists
that the LIVE signing secret is the right one — a wrong secret shows up there and nowhere else.

The first live checkout before that failed, and finding it was worth the attempt: a Stripe customer
belongs to one mode, and the practice was still carrying the customer created during the test
purchase. See CLAUDE.md, *Test and live prices are kept apart*.

Two things to tidy when you are ready: refund the £25 in Stripe, and take the credit off the
practice by hand on the admin page — a refund does not undo the credit, and nothing should pretend
it does.

**The step that was left, now done**: put the live secret key and the live webhook signing
secret into `specline-config.php`, in the same edit. The live signing secret is a different string
from the test one; it is on the live destination's own page in Stripe behind the reveal icon beside
*Signing secret*. Until both are there the site stays in test mode, which is a safe place to sit —
nothing live can be charged, and any live event that does arrive is refused rather than acted on.

**The Stripe account also sells ArchLens**, so its public business name is *SY design studio* rather
than *Specline*, and that is what a subscriber sees on the checkout page, in the billing portal and
on the card statement. Renaming the account would mislabel the other product, so the honest fix if
it matters is a per-product statement descriptor, not a rename.

---

## 4. Paste the price identifiers

**Administration → Billing → Stripe.** Paste each `price_…` into its row and save. Anything that
does not look like a Stripe price identifier is refused rather than saved, so a typo cannot reach
a checkout. The panel above shows what is still missing: a plan with no price is disabled on the
subscribe page rather than failing at the till.

## 5. Test it, in test mode

1. Sign in as a member account (not the owner) whose practice has no entitlement.
2. **Account → Plans → Monthly** on Solo. Stripe's test card is `4242 4242 4242 4242`, any future
   expiry, any CVC.
3. Back on the account page, the subscription appears — **after** Stripe's webhook arrives, which
   is usually a second or two. It is deliberate that the return from checkout does not grant
   anything: a page that granted access on the way back would grant it to anyone who guessed the
   address.
4. Administration → Billing shows the event, the practice and what the site did with it.
5. In Stripe, cancel the test subscription. The entitlement ends, and the practice keeps every job.
6. Buy a specification credit and check the ledger on the same page.

## 6. Go live

The order matters, and it is this way round on purpose: **everything live is prepared while the
site is still running on the test key**, so there is never a moment when the site is charging real
cards through a configuration that is half done.

1. Recreate the three products and five prices in live mode. Test and live objects are separate in
   Stripe, and a test price does not exist in live.
2. Paste the live identifiers into **Administration → Billing → Live prices**. The admin page holds
   both sets at once and the key chooses which is read, so pasting these changes nothing while the
   key is still `sk_test_`. The panel above shows `Prices set up · live 5 of 5` when the set is
   ready for the switch.
3. Add a **live** webhook destination on `https://specline.co.uk/webhook.php` with the same six
   events. It has its own `whsec_`, different from the test one.
4. In `specline-config.php`, swap `sk_test_…` for `sk_live_…` and the test `whsec_` for the live
   one. **Both, in the same edit** — a live key with a test signing secret means every real payment
   is refused at the webhook and no entitlement is ever written, which looks exactly like a payment
   that never arrived.
5. Confirm the admin page reads **LIVE mode**, `Prices set up · live 5 of 5`, and that the price
   rules still hold.
6. Buy something real and small to prove it, then refund it in Stripe. A £25 credit is the cheapest
   honest end-to-end test, and the refund does not undo the credit — remove that by hand on the
   same page if you want the ledger clean.
7. Only then: **Administration → Billing → Start enforcing.** Until that switch is on, billing
   changes nothing for anyone — which is how it has shipped so far.

**The customer sees your Stripe account's public name**, on the checkout page, the billing portal
and the card statement. Set it to Specline in Stripe under Settings → Business, or a subscriber who
bought Specline gets a receipt from a company they have not heard of.

### Test and live prices are kept apart

`stripe_price_bucket()` reads the mode from the key and picks the settings the price identifiers are
stored under. Before this the site held **one** set: swapping the key pointed every checkout at a
price that did not exist in that mode, and the failure surfaced on the subscriber at the till rather
than anywhere an administrator would see it. Identifiers saved before the buckets existed are read
as test-mode ones, and **live is never inherited** — it is set up deliberately or it is empty.

---

## Founding members, and what "locked for life" means in practice

Thirty places, promised on the home page. The **count** is enforced: `founding_taken()` counts
distinct practices with a founding entitlement, a regrant of the same practice does not spend a
second place, and the thirty-first is still entitled but is recorded as a standard grant with a
note saying the places were full. Administration → Billing shows how many are taken.

The **price being held is a procedure, not a feature.** Stripe keeps a subscription on the price it
started on until somebody moves it, so honouring the promise means one thing:

> **When prices rise, create new prices and leave every existing subscription where it is.**
> Never migrate a founding member's subscription to a new price, and never use Stripe's bulk
> price-migration tools on the whole product.

That is the whole mechanism. It is written on the admin page as well, because the moment it matters
is a price rise, which will be months away and long after anyone remembers this file.

## Two things still to do before selling

- **Issuing a specification must spend a credit.** The server side is built and honest about
  whether it charged (`/api.php`, op `spec.issue`); the app has still to call it at the moment of
  issue. Until it does, per-spec cannot be enforced — subscriptions can.
- **The solicitor**, on auto-renewal, refunds, unspent credits and the founding-member promise:
  questions 5 to 11 in `docs/TERMS-DRAFT.md`. Both published pages say they have not been
  reviewed, and that has to stop being true before the first live card is charged.

## The one that cost an evening

**The checkout button appeared to do nothing.** Every click created a real Checkout Session at
Stripe — twelve of them in thirty-six seconds, all 200 OK — and the browser then refused to follow
the redirect, silently. The cause was this site's own `Content-Security-Policy`: `form-action`
governs the whole redirect chain of a form submission in Chrome and Safari, not just where the
form posts, so a 302 to `checkout.stripe.com` was blocked.

Two things worth remembering from it:

- **The policy the browser enforces is the one in the root `.htaccess`**, not the one in
  `site/app/bootstrap.php`. `Header always set` overrides what PHP sends. Change both, together,
  or spend an hour watching a fix do nothing.
- **Check the browser console before theorising.** The message named the directive outright. It
  was the second thing looked at rather than the first, and the first hour went on the wrong
  suspects — a slow deployment, a rate limit, a stale cache.

## If something goes wrong

- **The subscribe page says payment is not connected.** The key or the webhook secret is missing
  from the config file; the admin Billing page says which.
- **Checkout opens but nothing happens afterwards.** The webhook is not arriving. Stripe's webhook
  page shows the delivery attempts and the response; the admin page counts refused (unsigned)
  attempts separately, so a signing-secret mismatch shows up as refusals rather than silence.
- **A practice paid and has no access.** Administration → Billing → Recent events shows what the
  site did with each event. A grant can always be made by hand there, and the event stays in the
  record either way.
