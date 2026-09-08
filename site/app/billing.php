<?php
/* Billing — the part that does not need a payment processor.
 *
 * The commercial model is in CLAUDE.md: subscription only, Solo £39/£390, Practice £89/£890,
 * Per specification £25, white-labelling in every tier. This file is the server's single
 * source of truth for those figures and for the one question the rest of the site asks:
 * MAY THIS PRACTICE USE THE TOOL, AND MAY IT ISSUE?
 *
 * Four rules hold it together.
 *
 * 1. `practices.plan` is an INTENTION, not an entitlement. A practice types it on its own
 *    account page — it always could — so it can never be what opens the tool. Entitlement is
 *    a row in `entitlements` that only the owner or a payment processor can write. Reading
 *    the wrong one of those two is how a paid product ends up free.
 *
 * 2. Nothing changes until `billing_enforce` is on, and it is off by default. The site is
 *    pre-launch; deploying this must not lock out the accounts that already exist. With it
 *    off, `entitled_to_open()` answers yes for everyone `app_access()` already admitted.
 *
 * 3. No figure is invented. The catalogue below is the only place prices live on this side,
 *    and `price_rules()` asserts the two relationships the model depends on — annual is ten
 *    months, and three per-spec purchases cost more than a month of Solo, so the cheap option
 *    pushes upward rather than replacing the subscription. If a price moves and a rule breaks,
 *    the admin page says so rather than quietly selling the wrong thing.
 *
 * 4. Per-spec is a ledger, not a counter. Credits are rows with a reason and a date, so a
 *    balance can always be explained, and issuing consumes one at the moment of issue.
 *
 * The processor itself is deliberately absent: see `processor_status()`. Nothing here calls
 * out to a network, and no key is committed — a key belongs in specline-config.php, above the
 * web root, with everything else that must survive a deployment.
 */

declare(strict_types=1);

/* ---------------------------------------------------------------- the catalogue */

/** Prices are pounds per period, excluding VAT, as CLAUDE.md states them. */
function plan_catalogue(): array {
    return [
        'solo' => [
            'n' => 'Solo', 'seats' => 1, 'month' => 39, 'year' => 390,
            'what' => 'One user, all eight project types, unlimited specifications.',
        ],
        'practice' => [
            'n' => 'Practice', 'seats' => 5, 'month' => 89, 'year' => 890,
            'what' => 'Up to five users, the shared job library, the practice’s own added clauses.',
        ],
        'payg' => [
            'n' => 'Per specification', 'seats' => 1, 'each' => 25,
            'what' => 'No subscription. One issued specification for each credit.',
        ],
    ];
}
function plan_meta(string $plan): array { return plan_catalogue()[$plan] ?? ['n' => 'None', 'seats' => 0, 'what' => '']; }

/** The relationships the commercial model depends on. Checked, never assumed. */
function price_rules(): array {
    $c = plan_catalogue();
    $out = [];
    foreach (['solo', 'practice'] as $k) {
        $out[] = [
            'rule' => ucfirst($k) . ' annual is ten months',
            'pass' => $c[$k]['year'] === $c[$k]['month'] * 10,
            'says' => '£' . $c[$k]['year'] . ' against £' . ($c[$k]['month'] * 10),
        ];
    }
    $out[] = [
        'rule' => 'Three per-spec purchases cost more than a month of Solo',
        'pass' => $c['payg']['each'] * 3 > $c['solo']['month'],
        'says' => '£' . ($c['payg']['each'] * 3) . ' against £' . $c['solo']['month'],
    ];
    $out[] = [
        'rule' => 'Practice costs more per seat than Solo does not hold — it must cost less',
        'pass' => ($c['practice']['month'] / max(1, $c['practice']['seats'])) < $c['solo']['month'],
        'says' => '£' . round($c['practice']['month'] / max(1, $c['practice']['seats']), 2) . ' a seat against £' . $c['solo']['month'],
    ];
    return $out;
}

/* ---------------------------------------------------------------- the switch */

function billing_enforced(): bool { return setting('billing_enforce', '0') === '1'; }

/** What is connected. Nothing yet, and this says so rather than implying otherwise. */
function processor_status(): array {
    $name = (string)cfg('payment_processor', '');
    $key  = stripe_ready();
    $hook = stripe_webhook_secret() !== '';
    $mode = stripe_mode();
    $prices = array_filter(stripe_price_map(), fn($p) => $p['id'] !== '');
    return [
        'chosen'    => $name !== '',
        'name'      => $name ?: 'none chosen',
        'connected' => $key && $hook,
        'mode'      => $mode,
        'key'       => $key,
        'webhook'   => $hook,
        'prices'    => count($prices),
        'prices_total' => count(stripe_price_map()),
        'note'      => !$key   ? 'No Stripe key is configured, so nothing can be charged. Entitlements can only be granted here, by hand.'
                     : (!$hook ? 'A Stripe key is configured but no webhook secret, so payments would be taken and never recorded. Add stripe_webhook_secret before selling anything.'
                     : ($mode === 'test' ? 'Connected in TEST mode. Cards are not really charged.'
                     : 'Connected in live mode.')),
    ];
}

/* ---------------------------------------------------------------- entitlement */

/* `past_due` is live ON PURPOSE. Stripe retries a failed card for about two weeks, and shutting
   a practice out of its own drafts on the first failed retry — over a card that expired — costs
   more goodwill than the fortnight is worth. It is shown as a warning on the account page and on
   the admin page, and Stripe ends the subscription itself when the retries run out, which
   arrives here as `customer.subscription.deleted`. Question 11 for the solicitor. */
const ENTITLEMENT_LIVE = ['trialing', 'active', 'past_due'];

/**
 * What this practice is entitled to, and why. The latest row that has not ended wins;
 * everything else is history and stays for the audit.
 */
function entitlement(int $practice_id): array {
    $in = "'" . implode("','", ENTITLEMENT_LIVE) . "'";
    $row = row("SELECT * FROM entitlements WHERE practice_id = ? AND status IN ($in)
                ORDER BY id DESC LIMIT 1", [$practice_id]);
    if ($row && !empty($row['ends_at']) && $row['ends_at'] < now()) {
        q("UPDATE entitlements SET status = 'expired' WHERE id = ?", [(int)$row['id']]);
        audit('billing.expire', 'practice ' . $practice_id . ' entitlement ' . $row['id']);
        $row = null;
    }
    $used = (int)val('SELECT COUNT(*) FROM users WHERE practice_id = ?', [$practice_id]);
    if (!$row) {
        return ['live' => false, 'status' => 'none', 'plan' => '', 'plan_name' => 'No subscription',
                'seats' => 0, 'seats_used' => $used, 'over' => $used > 0, 'ends_at' => null,
                'source' => '', 'note' => '', 'credits' => spec_credit_balance($practice_id)];
    }
    $seats = (int)$row['seats'] ?: (int)plan_meta((string)$row['plan'])['seats'];
    return [
        'live' => true, 'status' => (string)$row['status'], 'plan' => (string)$row['plan'],
        'plan_name' => plan_meta((string)$row['plan'])['n'],
        'seats' => $seats, 'seats_used' => $used, 'over' => $used > $seats,
        'ends_at' => $row['ends_at'] ?: null, 'source' => (string)$row['source'],
        'note' => (string)$row['note'], 'credits' => spec_credit_balance($practice_id),
    ];
}

/**
 * May this practice open the tool?
 *
 * With enforcement off, this is not the gate — `app_access()` is, exactly as before. With it
 * on, a live entitlement opens the tool; so does per-spec, because a per-spec practice is a
 * customer who pays at the point of issue and must be able to draft first.
 */
function entitled_to_open(array $u): bool {
    if (!billing_enforced()) return true;
    if (($u['role'] ?? '') === 'owner') return true;          // the vendor's own account
    $e = entitlement((int)$u['practice_id']);
    if ($e['live']) return true;
    return $e['credits'] > 0;
}

/** The latest entitlement of any status, live or not: what this practice USED to hold. */
function last_entitlement(int $practice_id): ?array {
    return row('SELECT * FROM entitlements WHERE practice_id = ? ORDER BY id DESC LIMIT 1', [$practice_id]);
}

/**
 * Why the tool is shut, in the practice's own terms. Empty string when it is not.
 *
 * A practice that has paid before is told its subscription ended, not that it never had one:
 * `entitlement()` cannot tell the difference, because an expired row stops being live, so this
 * asks what was held last. Telling a lapsed customer to "choose a plan" reads as though the
 * record of their subscription has been lost.
 */
function open_refusal(array $u): string {
    if (entitled_to_open($u)) return '';
    $pid = (int)$u['practice_id'];
    $had = last_entitlement($pid);
    if ($had) {
        $when = !empty($had['ends_at']) ? ' on ' . substr((string)$had['ends_at'], 0, 10) : '';
        return 'The ' . plan_meta((string)$had['plan'])['n'] . ' subscription for this practice ended' . $when
             . '. Renew it to open the tool; every job you have saved is still here.';
    }
    return 'This practice does not have a subscription. Choose a plan to open the tool; anything already saved stays exactly as it is.';
}

/**
 * May this practice ISSUE a specification? A subscription says yes. Per-spec says yes only
 * while there is a credit to spend, and spending it is `consume_spec_credit()`.
 */
function entitled_to_issue(int $practice_id): bool {
    if (!billing_enforced()) return true;
    $e = entitlement($practice_id);
    if ($e['live'] && $e['plan'] !== 'payg') return true;
    return $e['credits'] > 0;
}

/** Grant, extend or start something. The only way an entitlement is written by hand. */
function grant_entitlement(int $practice_id, string $plan, string $status, ?string $ends_at,
                           string $source, string $note, string $by, ?int $seats = null, string $ref = ''): int {
    $plan = array_key_exists($plan, plan_catalogue()) ? $plan : 'solo';
    $status = in_array($status, ENTITLEMENT_LIVE, true) ? $status : 'active';
    $seats = $seats !== null ? max(1, $seats) : (int)plan_meta($plan)['seats'];
    $in = "'" . implode("','", ENTITLEMENT_LIVE) . "'";
    q("UPDATE entitlements SET status = 'superseded', ended_at = ? WHERE practice_id = ? AND status IN ($in)",
      [now(), $practice_id]);
    q('INSERT INTO entitlements (practice_id, plan, seats, status, source, note, ref, started_at, ends_at, created_at, created_by)
       VALUES (?,?,?,?,?,?,?,?,?,?,?)',
      [$practice_id, $plan, $seats, $status, $source, $note, $ref, now(), $ends_at, now(), $by]);
    audit('billing.grant', "practice $practice_id $plan $status" . ($ends_at ? " until $ends_at" : ' open-ended') . " by $by");
    return (int)db()->lastInsertId();
}

function end_entitlement(int $practice_id, string $by, string $why = ''): void {
    $in = "'" . implode("','", ENTITLEMENT_LIVE) . "'";
    q("UPDATE entitlements SET status = 'cancelled', ended_at = ?, note = CASE WHEN note = '' THEN ? ELSE note END
       WHERE practice_id = ? AND status IN ($in)", [now(), $why, $practice_id]);
    audit('billing.end', "practice $practice_id by $by" . ($why ? " — $why" : ''));
}

/* ---------------------------------------------------------------- per-spec credits */

function spec_credit_balance(int $practice_id): int {
    return (int)(val('SELECT COALESCE(SUM(delta), 0) FROM spec_credits WHERE practice_id = ?', [$practice_id]) ?? 0);
}

function add_spec_credits(int $practice_id, int $n, string $reason, string $by, string $ref = ''): void {
    $n = max(1, $n);
    q('INSERT INTO spec_credits (practice_id, delta, reason, ref, job_id, at, by_who) VALUES (?,?,?,?,?,?,?)',
      [$practice_id, $n, $reason, $ref, '', now(), $by]);
    audit('billing.credits', "practice $practice_id +$n ($reason) by $by");
}

/**
 * Spend one credit for an issued specification. Returns false when there is none to spend,
 * and the caller must then refuse the issue rather than let it through unrecorded.
 */
function consume_spec_credit(int $practice_id, string $job_id, string $by): bool {
    if (spec_credit_balance($practice_id) <= 0) return false;
    q('INSERT INTO spec_credits (practice_id, delta, reason, ref, job_id, at, by_who) VALUES (?,?,?,?,?,?,?)',
      [$practice_id, -1, 'issued', '', $job_id, now(), $by]);
    audit('billing.issue', "practice $practice_id job $job_id by $by");
    return true;
}

/* ---------------------------------------------------------------- reporting */

/** Every practice with its entitlement, for the administrator. */
function billing_overview(): array {
    $out = [];
    foreach (rows('SELECT id, name, plan, created_at FROM practices ORDER BY id') as $p) {
        $e = entitlement((int)$p['id']);
        $e['practice_id'] = (int)$p['id'];
        $e['practice'] = (string)$p['name'];
        $e['intent'] = (string)$p['plan'];
        $e['created_at'] = (string)$p['created_at'];
        $out[] = $e;
    }
    return $out;
}
