<?php
/* Stripe — the only place this site talks to a payment processor.
 *
 * No SDK and no composer: the rest of the site has no dependencies and this does not introduce
 * one. Stripe's API is form-encoded HTTPS and its webhook signature is an HMAC, both of which
 * are a few lines each and easier to audit than a vendored library.
 *
 * The security model is one sentence: AN ENTITLEMENT IS ONLY EVER WRITTEN FROM AN EVENT WHOSE
 * SIGNATURE VERIFIED. Anyone can POST to a webhook address. `stripe_verify()` is what makes the
 * difference between a payment system and a free-for-all, so it is written to fail closed —
 * no secret configured means no event is accepted, not "accept everything".
 *
 * Keys live in specline-config.php, above the web root, where a deployment cannot overwrite them
 * and this repository cannot leak them:
 *
 *     'payment_processor'      => 'stripe',
 *     'stripe_secret_key'      => 'sk_test_… or sk_live_…',
 *     'stripe_webhook_secret'  => 'whsec_…',
 *
 * The price identifiers are not secret and live in settings, set on the admin Billing page,
 * so they can be changed without touching a file above the web root.
 */

declare(strict_types=1);

const STRIPE_API = 'https://api.stripe.com/v1/';
const STRIPE_TOLERANCE = 300;   // seconds either side, as Stripe recommends

function stripe_key(): string { return (string)cfg('stripe_secret_key', ''); }
function stripe_webhook_secret(): string { return (string)cfg('stripe_webhook_secret', ''); }
function stripe_ready(): bool { return stripe_key() !== ''; }

/** test or live, read from the key itself so nobody mistakes one for the other. */
function stripe_mode(): string {
    $k = stripe_key();
    if ($k === '') return 'none';
    if (str_starts_with($k, 'sk_live_') || str_starts_with($k, 'rk_live_')) return 'live';
    if (str_starts_with($k, 'sk_test_') || str_starts_with($k, 'rk_test_')) return 'test';
    return 'unknown';
}

/* ---------------------------------------------------------------- the price map */

/** plan+period => the Stripe price id, set on the admin page. Not secret. */
function stripe_price_key(string $plan, string $period): string { return 'stripe_price_' . $plan . '_' . $period; }
function stripe_price_id(string $plan, string $period): string { return (string)setting(stripe_price_key($plan, $period), ''); }

/** Every price this site can sell, and whether it has been set up. */
function stripe_price_map(): array {
    $out = [];
    foreach (['solo' => ['month', 'year'], 'practice' => ['month', 'year'], 'payg' => ['each']] as $plan => $periods)
        foreach ($periods as $p)
            $out[] = ['plan' => $plan, 'period' => $p, 'key' => stripe_price_key($plan, $p), 'id' => stripe_price_id($plan, $p)];
    return $out;
}

/** The other direction: which plan a Stripe price belongs to, for an incoming event. */
function stripe_plan_for_price(string $price_id): array {
    foreach (stripe_price_map() as $p)
        if ($p['id'] !== '' && $p['id'] === $price_id) return ['plan' => $p['plan'], 'period' => $p['period']];
    return ['plan' => '', 'period' => ''];
}

/* ---------------------------------------------------------------- the API call */

/**
 * One POST or GET to Stripe. Returns [ok, status, body]. Never throws, never prints the key,
 * and never lets a network failure look like a refusal from Stripe.
 */
function stripe_call(string $path, array $params = [], string $method = 'POST'): array {
    if (!stripe_ready()) return ['ok' => false, 'status' => 0, 'body' => ['error' => ['message' => 'No Stripe key is configured.']]];
    $url = STRIPE_API . ltrim($path, '/');
    $ch = curl_init();
    $opts = [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 20,
        CURLOPT_HTTPHEADER     => ['Authorization: Bearer ' . stripe_key(), 'Stripe-Version: 2024-06-20'],
    ];
    if ($method === 'POST') {
        $opts[CURLOPT_POST] = true;
        $opts[CURLOPT_POSTFIELDS] = http_build_query($params, '', '&', PHP_QUERY_RFC3986);
    } else {
        $url .= $params ? ('?' . http_build_query($params)) : '';
    }
    $opts[CURLOPT_URL] = $url;
    curl_setopt_array($ch, $opts);
    $raw = curl_exec($ch);
    $status = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err = curl_error($ch);
    curl_close($ch);
    if ($raw === false) return ['ok' => false, 'status' => 0, 'body' => ['error' => ['message' => 'Could not reach Stripe: ' . $err]]];
    $body = json_decode((string)$raw, true);
    if (!is_array($body)) $body = ['error' => ['message' => 'Stripe sent something this site could not read.']];
    return ['ok' => $status >= 200 && $status < 300, 'status' => $status, 'body' => $body];
}

/* ---------------------------------------------------------------- checkout */

/**
 * A Checkout Session for a subscription or for per-spec credits.
 *
 * `client_reference_id` carries the practice, and metadata carries it again on the subscription
 * itself, because the events that matter later arrive against the SUBSCRIPTION, not the session.
 * Without that the webhook has to guess which practice paid, and a payment system must never
 * guess.
 */
function stripe_checkout(int $practice_id, string $plan, string $period, int $qty, string $email, string $base): array {
    $price = stripe_price_id($plan, $period);
    if ($price === '') return ['ok' => false, 'error' => 'No Stripe price has been set up for ' . $plan . ' ' . $period . '.'];
    $sub = $plan !== 'payg';
    $p = [
        'mode'                 => $sub ? 'subscription' : 'payment',
        'success_url'          => $base . '/account/subscribe.php?done=1&session={CHECKOUT_SESSION_ID}',
        'cancel_url'           => $base . '/account/subscribe.php?cancelled=1',
        'client_reference_id'  => (string)$practice_id,
        'line_items'           => [['price' => $price, 'quantity' => max(1, $qty)]],
        'metadata'             => ['practice_id' => (string)$practice_id, 'plan' => $plan, 'period' => $period],
    ];
    if ($email !== '') $p['customer_email'] = $email;
    $cust = (string)(val('SELECT stripe_customer_id FROM practices WHERE id = ?', [$practice_id]) ?? '');
    if ($cust !== '') { $p['customer'] = $cust; unset($p['customer_email']); }
    if ($sub) {
        $p['subscription_data'] = ['metadata' => ['practice_id' => (string)$practice_id, 'plan' => $plan, 'period' => $period]];
        $p['allow_promotion_codes'] = 'true';
    } else {
        $p['payment_intent_data'] = ['metadata' => ['practice_id' => (string)$practice_id, 'credits' => (string)max(1, $qty)]];
    }
    $r = stripe_call('checkout/sessions', $p);
    if (!$r['ok']) return ['ok' => false, 'error' => (string)($r['body']['error']['message'] ?? 'Stripe refused to open a checkout.')];
    audit('billing.checkout', "practice $practice_id $plan $period x$qty");
    return ['ok' => true, 'url' => (string)($r['body']['url'] ?? '')];
}

/** The customer portal, where a subscriber changes a card or cancels — Stripe's page, not ours. */
function stripe_portal(int $practice_id, string $base): array {
    $cust = (string)(val('SELECT stripe_customer_id FROM practices WHERE id = ?', [$practice_id]) ?? '');
    if ($cust === '') return ['ok' => false, 'error' => 'This practice has no Stripe customer record yet.'];
    $r = stripe_call('billing_portal/sessions', ['customer' => $cust, 'return_url' => $base . '/account/']);
    if (!$r['ok']) return ['ok' => false, 'error' => (string)($r['body']['error']['message'] ?? 'Stripe refused to open the billing portal.')];
    return ['ok' => true, 'url' => (string)($r['body']['url'] ?? '')];
}

/* ---------------------------------------------------------------- the webhook */

/**
 * Verify a Stripe signature. Fails closed: no secret, no header, a stale timestamp or a
 * mismatched digest all mean NO. `hash_equals` because a timing-safe comparison is the whole
 * point of signing in the first place.
 */
function stripe_verify(string $payload, string $sigHeader, string $secret, ?int $now = null): bool {
    if ($secret === '' || $sigHeader === '') return false;
    $now = $now ?? time();
    $t = null; $v1 = [];
    foreach (explode(',', $sigHeader) as $part) {
        $bits = explode('=', trim($part), 2);
        if (count($bits) !== 2) continue;
        if ($bits[0] === 't') $t = (int)$bits[1];
        elseif ($bits[0] === 'v1') $v1[] = $bits[1];
    }
    if ($t === null || !$v1) return false;
    if (abs($now - $t) > STRIPE_TOLERANCE) return false;
    $expected = hash_hmac('sha256', $t . '.' . $payload, $secret);
    foreach ($v1 as $candidate) if (hash_equals($expected, $candidate)) return true;
    return false;
}

/**
 * When the current period ends, from wherever this API version puts it.
 *
 * Stripe moved `current_period_end` off the subscription and onto each subscription ITEM in the
 * 2025 versions, and the webhook destination created for Specline is on 2026-06-24.dahlia. Read
 * both, newest shape first, and return null rather than a guess if neither is there — a null
 * simply means the entitlement runs until Stripe says otherwise, which is safe. Inventing a
 * renewal date would put a figure in front of a subscriber that nothing supports.
 */
function stripe_period_end(array $sub): ?int {
    $items = $sub['items']['data'] ?? [];
    if (is_array($items)) {
        $ends = [];
        foreach ($items as $it) if (!empty($it['current_period_end'])) $ends[] = (int)$it['current_period_end'];
        if ($ends) return max($ends);
    }
    if (!empty($sub['current_period_end'])) return (int)$sub['current_period_end'];
    return null;
}

/** Which practice an event is about. Metadata first, then the customer we already know. */
function stripe_practice_of(array $obj): int {
    $meta = $obj['metadata'] ?? [];
    if (!empty($meta['practice_id'])) return (int)$meta['practice_id'];
    if (!empty($obj['client_reference_id'])) return (int)$obj['client_reference_id'];
    $cust = (string)($obj['customer'] ?? '');
    if ($cust !== '') {
        $id = val('SELECT id FROM practices WHERE stripe_customer_id = ?', [$cust]);
        if ($id !== null) return (int)$id;
    }
    return 0;
}

/** Remember the customer so later events can find their way home. */
function stripe_remember_customer(int $practice_id, string $customer): void {
    if ($practice_id <= 0 || $customer === '') return;
    q('UPDATE practices SET stripe_customer_id = ? WHERE id = ? AND (stripe_customer_id IS NULL OR stripe_customer_id = \'\')',
      [$customer, $practice_id]);
}

/**
 * Turn one verified event into an entitlement, a credit, or nothing.
 *
 * Idempotent by construction: the event id is stored with a unique key before anything is
 * written, so a replay — and Stripe replays — is recorded and ignored rather than granting
 * twice. Returns a short line for the log and the admin page.
 */
function stripe_handle_event(array $ev): string {
    $id   = (string)($ev['id'] ?? '');
    $type = (string)($ev['type'] ?? '');
    $obj  = (array)($ev['data']['object'] ?? []);
    if ($id === '' || $type === '') return 'ignored: not an event';

    try {
        q('INSERT INTO billing_events (event_id, type, at, payload, note) VALUES (?,?,?,?,?)',
          [$id, $type, now(), mb_substr(json_encode($ev, JSON_UNESCAPED_SLASHES) ?: '', 0, 20000), '']);
    } catch (Throwable $t) {
        return 'already seen: ' . $id;          // the unique index did its job
    }

    $pid = stripe_practice_of($obj);
    $note = '';

    switch ($type) {

    case 'checkout.session.completed': {
        stripe_remember_customer($pid, (string)($obj['customer'] ?? ''));
        if (($obj['mode'] ?? '') === 'payment') {
            /* per-spec credits: what was bought is on the session's own metadata, because a
               one-off payment has no subscription to carry it. */
            $n = (int)($obj['metadata']['credits'] ?? 0);
            if ($n <= 0) $n = 1;
            if ($pid > 0 && ($obj['payment_status'] ?? '') === 'paid') {
                add_spec_credits($pid, $n, 'bought', 'stripe', (string)($obj['payment_intent'] ?? $id));
                $note = "practice $pid bought $n credit" . ($n === 1 ? '' : 's');
            } else {
                $note = 'payment not completed; no credits added';
            }
        } else {
            $note = "practice $pid started a subscription";   // the subscription event does the granting
        }
        break;
    }

    case 'customer.subscription.created':
    case 'customer.subscription.updated':
    case 'customer.subscription.resumed': {
        stripe_remember_customer($pid, (string)($obj['customer'] ?? ''));
        $status = (string)($obj['status'] ?? '');
        $price  = (string)($obj['items']['data'][0]['price']['id'] ?? '');
        $found  = stripe_plan_for_price($price);
        $plan   = $found['plan'] ?: (string)($obj['metadata']['plan'] ?? 'solo');
        $pe     = stripe_period_end($obj);
        $ends   = $pe ? gmdate('c', $pe) : null;
        $subId  = (string)($obj['id'] ?? '');
        $at     = (int)($ev['created'] ?? 0);
        if ($pid <= 0) { $note = 'no practice on the event; nothing written'; break; }

        /* Stripe does not promise delivery order, and the first real payment showed why that
           matters: created (incomplete) and updated (active) were issued in the same second.
           Had they arrived the other way round, a stale created would have undone a live
           subscription. An event older than the one already acted on for this subscription is
           therefore ignored — the state we hold came from a later truth. */
        $seen = entitlement_event_at($subId);
        if ($at && $seen && $at < $seen) {
            $note = "practice $pid — older than the event already applied; ignored";
            break;
        }

        /* `incomplete` is the moment between a subscription being created and its first payment
           confirming. It is NOT a cancellation, and treating it as one ended the entitlement for
           the instant between two events on the very first live test. Only the states that mean
           the subscription is over end anything; anything unrecognised — including a status
           Stripe adds later — writes nothing rather than guessing. */
        $liveStates = ['active', 'trialing', 'past_due'];
        $overStates = ['canceled', 'cancelled', 'unpaid', 'incomplete_expired', 'paused'];
        if (in_array($status, $liveStates, true)) {
            grant_entitlement($pid, $plan, $status === 'trialing' ? 'trialing' : ($status === 'past_due' ? 'past_due' : 'active'),
                              $ends, 'stripe', 'Stripe subscription ' . $subId, 'stripe', null, $subId, $at);
            $note = "practice $pid $plan $status" . ($ends ? ' until ' . substr($ends, 0, 10) : '');
        } elseif (in_array($status, $overStates, true)) {
            end_entitlement($pid, 'stripe', 'Stripe says the subscription is ' . $status);
            $note = "practice $pid ended ($status)";
        } else {
            $note = "practice $pid $status — waiting, nothing written";
        }
        break;
    }

    case 'customer.subscription.deleted':
    case 'customer.subscription.paused': {
        if ($pid > 0) { end_entitlement($pid, 'stripe', 'Stripe: subscription ' . ($type === 'customer.subscription.paused' ? 'paused' : 'cancelled')); $note = "practice $pid ended"; }
        else $note = 'no practice on the event; nothing written';
        break;
    }

    default:
        $note = 'no action for ' . $type;
    }

    q('UPDATE billing_events SET practice_id = ?, note = ? WHERE event_id = ?', [$pid, $note, $id]);
    return $note;
}
