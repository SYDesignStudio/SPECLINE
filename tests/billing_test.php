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

echo "\n$pass passed, $fail failed\n";

/* leave nothing behind */
foreach (glob($tmp . '/*') ?: [] as $f) @unlink($f);
@rmdir($tmp);
exit($fail ? 1 : 0);
