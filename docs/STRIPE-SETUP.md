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

1. Recreate the five prices in live mode (test and live objects are separate in Stripe) and paste
   the live identifiers into the admin page.
2. Add a live webhook endpoint and put its `whsec_` into the config file.
3. Swap `sk_test_…` for `sk_live_…`.
4. Confirm the admin page reads **LIVE mode**, and that the price rules still hold.
5. Only then: **Administration → Billing → Start enforcing.** Until that switch is on, billing
   changes nothing for anyone — which is how it has shipped so far.

---

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
