<?php
/* Billing self-test — run with `php tests/billing_test.php`.
 *
 * It builds a throwaway database in the system temp directory, so it never touches the real
 * one, and asserts the things that would cost money or trust if they were wrong: the price
 * relationships, that a practice's own stated plan cannot entitle it to anything, that
 * enforcement is off until it is switched on, that a credit is spent once and only when there
 * is one, and that ending an entitlement actually shuts the tool.
 */
declare(strict_types=1);

$tmp = sys_get_temp_dir() . '/specline-billing-test-' . bin2hex(random_bytes(4));
@mkdir($tmp, 0777, true);
putenv('SPECLINE_DATA_DIR=' . $tmp);
$_SERVER['REQUEST_METHOD'] = 'GET';
$_SERVER['SCRIPT_NAME'] = '/tests/billing_test.php';

require __DIR__ . '/../site/app/bootstrap.php';

$pass = 0; $fail = 0;
function ok(string $what, bool $cond, string $detail = ''): void {
    global $pass, $fail;
    if ($cond) { $pass++; echo "  ok   $what\n"; }
    else { $fail++; echo "  FAIL $what" . ($detail ? "  — $detail" : '') . "\n"; }
}

/* ---- prices ---- */
foreach (price_rules() as $r) ok('price rule: ' . $r['rule'], $r['pass'], $r['says']);

/* ---- a practice and a user to hang it on ---- */
q('INSERT INTO practices (name, address, designer, phone, plan, seats, contact_email, created_at) VALUES (?,?,?,?,?,?,?,?)',
  ['Fletcher Vane Architects', '3 Quay Street', 'R Ridley', '', 'practice', 5, 'studio@example.test', now()]);
$pid = (int)db()->lastInsertId();
q('INSERT INTO users (practice_id, email, name, pass_hash, role, verified_at, created_at) VALUES (?,?,?,?,?,?,?)',
  [$pid, 'a@example.test', 'A Vane', 'x', 'member', now(), now()]);
$u = ['practice_id' => $pid, 'role' => 'member', 'email' => 'a@example.test'];

/* ---- the switch ---- */
ok('enforcement is off until it is switched on', !billing_enforced());
ok('with it off, the tool opens', entitled_to_open($u));
ok('with it off, issuing is allowed', entitled_to_issue($pid));
set_setting('billing_enforce', '1');
ok('with it on, no entitlement means no tool', !entitled_to_open($u));
ok('and the refusal says why in the practice\'s own terms', str_contains(open_refusal($u), 'does not have a subscription'), open_refusal($u));

/* ---- the practice's OWN stated plan must entitle it to nothing ---- */
q('UPDATE practices SET plan = ? WHERE id = ?', ['practice', $pid]);
ok('a practice cannot entitle itself by choosing a plan on its account page', !entitled_to_open($u));

/* ---- a grant ---- */
grant_entitlement($pid, 'practice', 'active', null, 'founding', 'Founding member, locked for life', 'owner@example.test');
$e = entitlement($pid);
ok('the grant is live', $e['live'] && $e['plan'] === 'practice', $e['status']);
ok('seats come from the plan', $e['seats'] === 5, (string)$e['seats']);
ok('one user of five is not over', !$e['over'], $e['seats_used'] . ' of ' . $e['seats']);
ok('the tool opens on a grant', entitled_to_open($u));
ok('and issuing is allowed', entitled_to_issue($pid));

/* ---- seats ---- */
for ($i = 2; $i <= 6; $i++)
    q('INSERT INTO users (practice_id, email, name, pass_hash, role, created_at) VALUES (?,?,?,?,?,?)',
      [$pid, "u$i@example.test", "User $i", 'x', 'member', now()]);
$e = entitlement($pid);
ok('six users on five seats reads as over', $e['over'] && $e['seats_used'] === 6, $e['seats_used'] . ' of ' . $e['seats']);
ok('being over seats does not shut the tool (it is not enforced, and says so)', entitled_to_open($u));

/* ---- expiry ---- */
grant_entitlement($pid, 'solo', 'active', gmdate('c', strtotime('-1 day')), 'manual', 'expired trial', 'owner@example.test');
$e = entitlement($pid);
ok('an entitlement past its end date is not live', !$e['live'], $e['status']);
ok('an expired entitlement shuts the tool', !entitled_to_open($u));
ok('and a lapsed practice is told its subscription ended, not that it never had one',
   str_contains(open_refusal($u), 'subscription for this practice ended'), open_refusal($u));
ok('the refusal names the plan they held', str_contains(open_refusal($u), 'Solo'), open_refusal($u));
ok('expiry is recorded, not merely computed',
   (string)val('SELECT status FROM entitlements WHERE practice_id = ? ORDER BY id DESC LIMIT 1', [$pid]) === 'expired');

/* ---- per-spec credits ---- */
ok('no credits to start', spec_credit_balance($pid) === 0);
ok('nothing to spend means the issue is refused', !consume_spec_credit($pid, 'j1', 'a@example.test'));
add_spec_credits($pid, 3, 'bought', 'owner@example.test');
ok('three bought', spec_credit_balance($pid) === 3);
ok('credits alone open the tool for a per-spec practice', entitled_to_open($u));
ok('and allow an issue', entitled_to_issue($pid));
ok('issuing spends one', consume_spec_credit($pid, 'j1', 'a@example.test') && spec_credit_balance($pid) === 2);
consume_spec_credit($pid, 'j2', 'a@example.test');
consume_spec_credit($pid, 'j3', 'a@example.test');
ok('spent down to nothing', spec_credit_balance($pid) === 0);
ok('and the fourth issue is refused', !consume_spec_credit($pid, 'j4', 'a@example.test'));
ok('every movement is explainable', (int)val('SELECT COUNT(*) FROM spec_credits WHERE practice_id = ?', [$pid]) === 4);

/* ---- ending ---- */
grant_entitlement($pid, 'solo', 'active', null, 'manual', '', 'owner@example.test');
ok('granted again', entitlement($pid)['live']);
end_entitlement($pid, 'owner@example.test', 'stopped paying');
ok('ending shuts the tool', !entitlement($pid)['live'] && !entitled_to_open($u));
ok('only one live row is ever left',
   (int)val("SELECT COUNT(*) FROM entitlements WHERE practice_id = ? AND status IN ('trialing','active')", [$pid]) === 0);

/* ---- the vendor's own account is never locked out ---- */
ok('the owner keeps access whatever billing says', entitled_to_open(['practice_id' => $pid, 'role' => 'owner', 'email' => 'owner@example.test']));

/* ---- the audit trail ---- */
ok('grants, expiries and issues are all audited', (int)val('SELECT COUNT(*) FROM audit') >= 8);

/* ---------------------------------------------------------------- Stripe ---- */
/* No network: the signature check and the event handling are pure, and they are the two
   places where being wrong costs money or lets a stranger grant themselves a subscription. */

$GLOBALS['CFG']['payment_processor']     = 'stripe';
$GLOBALS['CFG']['stripe_secret_key']     = 'sk_test_abc123';
$GLOBALS['CFG']['stripe_webhook_secret'] = 'whsec_test_secret';

ok('the key tells us which mode we are in', stripe_mode() === 'test', stripe_mode());
$GLOBALS['CFG']['stripe_secret_key'] = 'sk_live_abc123';
ok('and a live key is not mistaken for a test one', stripe_mode() === 'live', stripe_mode());
$GLOBALS['CFG']['stripe_secret_key'] = 'sk_test_abc123';

/* --- signature verification, which is the whole security model of the webhook --- */
$body = '{"id":"evt_1","type":"ping"}';
$sign = function (string $payload, int $t, string $secret): string {
    return 't=' . $t . ',v1=' . hash_hmac('sha256', $t . '.' . $payload, $secret);
};
$now = time();
ok('a correctly signed event verifies', stripe_verify($body, $sign($body, $now, 'whsec_test_secret'), 'whsec_test_secret', $now));
ok('a signature from another secret does not', !stripe_verify($body, $sign($body, $now, 'whsec_someone_else'), 'whsec_test_secret', $now));
ok('a tampered payload does not', !stripe_verify('{"id":"evt_1","type":"grant.me.everything"}', $sign($body, $now, 'whsec_test_secret'), 'whsec_test_secret', $now));
ok('a stale timestamp does not (replay window)', !stripe_verify($body, $sign($body, $now - 4000, 'whsec_test_secret'), 'whsec_test_secret', $now));
ok('a missing header does not', !stripe_verify($body, '', 'whsec_test_secret', $now));
ok('NO SECRET CONFIGURED MEANS NOTHING VERIFIES, not everything', !stripe_verify($body, $sign($body, $now, ''), '', $now));
ok('a header without a v1 digest does not', !stripe_verify($body, 't=' . $now, 'whsec_test_secret', $now));
ok('one good digest among several is accepted (Stripe rotates secrets)',
   stripe_verify($body, 't=' . $now . ',v1=deadbeef,v1=' . hash_hmac('sha256', $now . '.' . $body, 'whsec_test_secret'), 'whsec_test_secret', $now));

/* --- the price map --- */
set_setting(stripe_price_key('practice', 'month'), 'price_practice_monthly');
set_setting(stripe_price_key('payg', 'each'), 'price_credit');
ok('a price maps back to its plan', stripe_plan_for_price('price_practice_monthly')['plan'] === 'practice');
ok('an unknown price maps to nothing rather than guessing', stripe_plan_for_price('price_never_seen')['plan'] === '');

/* --- test and live prices are different objects, and must not share a setting --- */
/* A price created in test mode does not exist in live. One set of identifiers could only ever be
   right for one mode, so the instant the key was swapped every checkout pointed at a price Stripe
   had never heard of — and the failure lands on the subscriber at the till, not here. */
ok('the bucket follows the key', stripe_price_bucket() === 'test', stripe_price_bucket());
$GLOBALS['CFG']['stripe_secret_key'] = 'sk_live_abc123';
ok('a live key reads the live set', stripe_price_bucket() === 'live', stripe_price_bucket());
ok('and the live set is empty rather than inheriting the test identifiers',
   stripe_price_id('practice', 'month') === '', stripe_price_id('practice', 'month'));
set_setting(stripe_price_key('practice', 'month'), 'price_live_practice_monthly');
ok('a live price saves under its own name', stripe_price_id('practice', 'month') === 'price_live_practice_monthly');
$GLOBALS['CFG']['stripe_secret_key'] = 'sk_test_abc123';
ok('and saving it did not disturb the test one', stripe_price_id('practice', 'month') === 'price_practice_monthly');
ok('an event naming the live price is still understood in test mode',
   stripe_plan_for_price('price_live_practice_monthly')['plan'] === 'practice');

/* --- a Stripe customer belongs to one mode too --- */
/* The first live checkout failed on exactly this: the practice still held the customer created
   during the test purchase, and Stripe answered "No such customer ...; a similar object exists in
   test mode, but a live mode key was used". Every practice that had bought in test would have been
   unable to buy anything in live. */
q('UPDATE practices SET stripe_customer_id = \'\', stripe_customer_id_test = \'\' WHERE id = ?', [$pid]);
stripe_remember_customer($pid, 'cus_test_one');
ok('a customer met in test mode is remembered as a test customer', stripe_customer_for($pid) === 'cus_test_one');
$GLOBALS['CFG']['stripe_secret_key'] = 'sk_live_abc123';
ok('AND IS NEVER OFFERED TO A LIVE CHECKOUT — Stripe refuses it outright',
   stripe_customer_for($pid) === '', stripe_customer_for($pid));
stripe_remember_customer($pid, 'cus_live_one');
ok('the live customer is remembered separately', stripe_customer_for($pid) === 'cus_live_one');
$GLOBALS['CFG']['stripe_secret_key'] = 'sk_test_abc123';
ok('and the test one is still there to go back to', stripe_customer_for($pid) === 'cus_test_one');

/* An event carrying no practice metadata is placed by its customer, and must be placed whichever
   mode it came from — the identifiers are unique across the two. */
$byCust = function (string $evid, string $cust) {
    return ['id' => $evid, 'type' => 'customer.subscription.updated', 'data' => ['object' => [
        'id' => 'sub_c', 'customer' => $cust, 'status' => 'active', 'metadata' => [],
        'items' => ['data' => [['price' => ['id' => 'price_practice_monthly']]]],
    ]]];
};
ok('an event is placed by a live customer id even while the key is test',
   stripe_practice_of($byCust('evt_c1', 'cus_live_one')['data']['object']) === $pid);
ok('and by a test one', stripe_practice_of($byCust('evt_c2', 'cus_test_one')['data']['object']) === $pid);
ok('an unknown customer places nothing', stripe_practice_of($byCust('evt_c3', 'cus_nobody')['data']['object']) === 0);
/* Left clear, so what follows meets this practice with no customer of either kind. */
q("UPDATE practices SET stripe_customer_id = '', stripe_customer_id_test = '' WHERE id = ?", [$pid]);

/* The identifiers saved before the buckets existed are test-mode ones and must keep working. */
set_setting('stripe_price_solo_year', 'price_legacy_solo_year');
ok('an identifier saved before the buckets existed still answers for test',
   stripe_price_id('solo', 'year') === 'price_legacy_solo_year');
$GLOBALS['CFG']['stripe_secret_key'] = 'sk_live_abc123';
ok('AND IS NEVER READ AS A LIVE PRICE — live is set up deliberately, never inherited',
   stripe_price_id('solo', 'year') === '', stripe_price_id('solo', 'year'));
$GLOBALS['CFG']['stripe_secret_key'] = 'sk_test_abc123';

/* --- events become entitlements --- */
q('DELETE FROM entitlements WHERE practice_id = ?', [$pid]);
q('DELETE FROM spec_credits WHERE practice_id = ?', [$pid]);

$sub = function (string $evid, string $status, ?int $ends = null, string $subid = 'sub_1') use ($pid) {
    return ['id' => $evid, 'type' => 'customer.subscription.updated', 'data' => ['object' => [
        'id' => $subid, 'customer' => 'cus_123', 'status' => $status,
        'current_period_end' => $ends, 'metadata' => ['practice_id' => (string)$pid],
        'items' => ['data' => [['price' => ['id' => 'price_practice_monthly']]]],
    ]]];
};

stripe_handle_event($sub('evt_a', 'active', time() + 2592000));
$e = entitlement($pid);
ok('a subscription event grants the plan its price names', $e['live'] && $e['plan'] === 'practice', $e['plan'] . ' ' . $e['status']);
ok('and it is recorded as coming from Stripe', $e['source'] === 'stripe', $e['source']);
ok('the customer is remembered for the events that follow',
   stripe_customer_for($pid) === 'cus_123', stripe_customer_for($pid));

$before = (int)val('SELECT COUNT(*) FROM entitlements WHERE practice_id = ?', [$pid]);
$again = stripe_handle_event($sub('evt_a', 'active', time() + 2592000));
ok('a REPLAYED event is ignored, not granted twice',
   str_contains($again, 'already seen') && (int)val('SELECT COUNT(*) FROM entitlements WHERE practice_id = ?', [$pid]) === $before, $again);

stripe_handle_event($sub('evt_b', 'past_due', time() + 2592000));
$e = entitlement($pid);
ok('a failed payment does not shut the tool on the first retry', $e['live'] && $e['status'] === 'past_due', $e['status']);
ok('but it is visible as past due, not as healthy', $e['status'] !== 'active');

stripe_handle_event(['id' => 'evt_c', 'type' => 'customer.subscription.deleted',
                     'data' => ['object' => ['id' => 'sub_1', 'customer' => 'cus_123', 'metadata' => ['practice_id' => (string)$pid]]]]);
ok('a cancelled subscription ends the entitlement', !entitlement($pid)['live']);

/* --- the renewal date, wherever this API version keeps it --- */
/* The webhook destination created on 9 September 2026 is API version 2026-06-24.dahlia, which
   carries current_period_end on the subscription ITEM, not the subscription. Read both. */
$soon = time() + 86400 * 30;
ok('the renewal date is read from the subscription item (2025+ versions)',
   stripe_period_end(['items' => ['data' => [['current_period_end' => $soon]]]]) === $soon);
ok('and still from the subscription itself (older versions)',
   stripe_period_end(['current_period_end' => $soon]) === $soon);
ok('the latest item wins where a subscription has several',
   stripe_period_end(['items' => ['data' => [['current_period_end' => $soon - 100], ['current_period_end' => $soon]]]]) === $soon);
ok('and neither present returns nothing rather than a guessed date',
   stripe_period_end(['id' => 'sub_x']) === null);

q('DELETE FROM entitlements WHERE practice_id = ?', [$pid]);
stripe_handle_event(['id' => 'evt_period', 'type' => 'customer.subscription.updated', 'data' => ['object' => [
    'id' => 'sub_2', 'customer' => 'cus_123', 'status' => 'active', 'metadata' => ['practice_id' => (string)$pid],
    'items' => ['data' => [['current_period_end' => $soon, 'price' => ['id' => 'price_practice_monthly']]]]]]]);
$e = entitlement($pid);
ok('an event in the new shape still sets the renewal date',
   $e['live'] && substr((string)$e['ends_at'], 0, 10) === gmdate('Y-m-d', $soon), (string)$e['ends_at']);

/* --- an event with no practice on it must write nothing --- */
$orphan = stripe_handle_event(['id' => 'evt_d', 'type' => 'customer.subscription.updated',
    'data' => ['object' => ['id' => 'sub_x', 'customer' => 'cus_unknown', 'status' => 'active',
               'items' => ['data' => [['price' => ['id' => 'price_practice_monthly']]]]]]]);
ok('an event this site cannot place writes nothing', str_contains($orphan, 'no practice'), $orphan);

/* --- the two faults the first real payment exposed --- */
/* Stripe issued created (incomplete) and updated (active) in the same second on the first live
   test. `incomplete` is the gap between a subscription existing and its first payment
   confirming — it is not a cancellation, and it must not end anything. */
q('DELETE FROM entitlements WHERE practice_id = ?', [$pid]);
$mk = function (string $evid, string $status, int $at, string $subid = 'sub_o') use ($pid, $soon) {
    return ['id' => $evid, 'type' => 'customer.subscription.updated', 'created' => $at, 'data' => ['object' => [
        'id' => $subid, 'customer' => 'cus_123', 'status' => $status, 'metadata' => ['practice_id' => (string)$pid],
        'items' => ['data' => [['current_period_end' => $soon, 'price' => ['id' => 'price_practice_monthly']]]],
    ]]];
};
$t0 = time();
$r = stripe_handle_event($mk('evt_inc', 'incomplete', $t0));
ok('an incomplete subscription writes nothing at all', str_contains($r, 'waiting'), $r);
ok('and does not end an entitlement that is not there yet', !entitlement($pid)['live']);

stripe_handle_event($mk('evt_act', 'active', $t0 + 1));
ok('the payment confirming grants it', entitlement($pid)['live'] && entitlement($pid)['plan'] === 'practice');

/* Delivery order is not guaranteed. A stale created arriving after a fresh updated must not
   undo it — which is exactly what would have happened had the two arrived the other way. */
$late = stripe_handle_event($mk('evt_stale', 'incomplete', $t0 - 60));
ok('an event older than the one already applied is ignored', str_contains($late, 'older than'), $late);
ok('and the live subscription is untouched by it', entitlement($pid)['live']);

/* A status this site has never heard of writes nothing rather than guessing at it. */
$unknown = stripe_handle_event($mk('evt_new', 'some_future_status', $t0 + 2));
ok('an unrecognised status writes nothing', str_contains($unknown, 'waiting'), $unknown);
ok('and still leaves the subscription live', entitlement($pid)['live']);

/* The ones that really are over do end it. */
stripe_handle_event($mk('evt_gone', 'canceled', $t0 + 3));
ok('a cancelled subscription ends the entitlement', !entitlement($pid)['live']);

/* --- per-spec credits arrive by checkout --- */
stripe_handle_event(['id' => 'evt_e', 'type' => 'checkout.session.completed', 'data' => ['object' => [
    'mode' => 'payment', 'payment_status' => 'paid', 'customer' => 'cus_123', 'payment_intent' => 'pi_1',
    'client_reference_id' => (string)$pid, 'metadata' => ['practice_id' => (string)$pid, 'credits' => '4']]]]);
ok('a paid checkout adds the credits it was for', spec_credit_balance($pid) === 4, (string)spec_credit_balance($pid));

stripe_handle_event(['id' => 'evt_f', 'type' => 'checkout.session.completed', 'data' => ['object' => [
    'mode' => 'payment', 'payment_status' => 'unpaid', 'customer' => 'cus_123',
    'metadata' => ['practice_id' => (string)$pid, 'credits' => '9']]]]);
ok('an unpaid checkout adds nothing', spec_credit_balance($pid) === 4, (string)spec_credit_balance($pid));

/* --- and the money is traceable --- */
$ref = (string)val("SELECT ref FROM spec_credits WHERE practice_id = ? AND delta > 0 ORDER BY id DESC LIMIT 1", [$pid]);
ok('a bought credit keeps the payment it came from', $ref === 'pi_1', $ref);
ok('every event is kept for the audit', (int)val('SELECT COUNT(*) FROM billing_events') >= 6);

echo "\n$pass passed, $fail failed\n";

/* leave nothing behind */
foreach (glob($tmp . '/*') ?: [] as $f) @unlink($f);
@rmdir($tmp);
exit($fail ? 1 : 0);
