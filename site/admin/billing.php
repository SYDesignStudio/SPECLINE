<?php
/* Billing — who may use the tool, and on what.
 *
 * Everything here is by hand, because that is the honest state: no payment processor is
 * connected, and this page says so rather than implying a subscription exists somewhere.
 * It is also how the first founding members get set up, and how a comp or an extension is
 * given without touching the database directly.
 */
require __DIR__ . '/../app/bootstrap.php';
$me = require_admin();

if (is_post()) {
    csrf_check();
    $a = (string)($_POST['action'] ?? '');
    $pid = (int)($_POST['practice_id'] ?? 0);
    if ($a === 'enforce') {
        $on = ($_POST['billing_enforce'] ?? '') === '1';
        set_setting('billing_enforce', $on ? '1' : '0');
        flash($on ? 'Enforcement on. A practice without an entitlement can no longer open the tool.'
                  : 'Enforcement off. The tool opens on the sign-up rules alone, as it did before billing existed.');
    } elseif ($a === 'grant' && $pid) {
        $plan   = (string)($_POST['plan'] ?? 'solo');
        $months = max(0, min(60, (int)($_POST['months'] ?? 0)));
        $ends   = $months ? gmdate('c', strtotime("+$months months")) : null;
        $seats  = (int)($_POST['seats'] ?? 0);
        grant_entitlement($pid, $plan, (string)($_POST['status'] ?? 'active'), $ends,
                          (string)($_POST['source'] ?? 'manual'), clean('note', 200), (string)$me['email'],
                          $seats ?: null);
        flash('Entitlement granted. It is theirs from now' . ($ends ? ' until ' . e(substr($ends, 0, 10)) : ', open-ended') . '.');
    } elseif ($a === 'end' && $pid) {
        end_entitlement($pid, (string)$me['email'], clean('note', 200));
        flash('Ended. Their work is untouched; with enforcement on they can no longer open the tool.');
    } elseif ($a === 'prices') {
        $n = 0;
        foreach (stripe_price_map() as $p) {
            $v = trim((string)($_POST[$p['key']] ?? ''));
            /* A price identifier is Stripe's own shape. Refusing anything else keeps a typo out
               of a checkout, where it would surface as an error the subscriber sees. */
            if ($v !== '' && !preg_match('/^price_[A-Za-z0-9]+$/', $v)) continue;
            set_setting($p['key'], $v); $n++;
        }
        flash($n . ' price ' . ($n === 1 ? 'identifier' : 'identifiers') . ' saved. Anything that did not look like price_… was left alone.');
    } elseif ($a === 'credits' && $pid) {
        add_spec_credits($pid, (int)($_POST['n'] ?? 1), clean('note', 40) ?: 'granted', (string)$me['email']);
        flash('Credits added. One is spent on each specification issued.');
    }
    redirect('/admin/billing.php');
}

$rows  = billing_overview();
$rules = price_rules();
$proc  = processor_status();
$cat   = plan_catalogue();
$on    = billing_enforced();
$live  = array_values(array_filter($rows, fn($r) => $r['live']));
$ledger = rows('SELECT c.*, p.name FROM spec_credits c LEFT JOIN practices p ON p.id = c.practice_id ORDER BY c.id DESC LIMIT 30');

page_start('Billing', ['admin' => true]);
?>
<header><div><h1>Billing</h1><p>What each practice may use, and on what basis. Subscriptions are charged by Stripe; everything on this page is what this site does with what Stripe says.</p></div></header>
<?php show_flash(); ?>

<section>
  <h2>Enforcement</h2>
  <p class="small muted" style="max-width:78ch;margin-bottom:14px">Off, the tool opens on the sign-up rules alone and every existing account keeps working — which is what a pre-launch site needs. On, a practice must hold an entitlement below, or a per-spec credit, before the tool will open for it. Your own account is never shut out.</p>
  <form method="post" class="inline" style="gap:14px"><?= csrf_field() ?><input type="hidden" name="action" value="enforce">
    <input type="hidden" name="billing_enforce" value="<?= $on ? '0' : '1' ?>">
    <span class="pill <?= $on ? 'pill-pass' : 'pill-hold' ?>"><?= $on ? 'Enforced — an entitlement is required' : 'Not enforced — sign-up rules only' ?></span>
    <button class="btn btn-sm" type="submit"><?= $on ? 'Stop enforcing' : 'Start enforcing' ?></button>
  </form>
  <p class="small notice <?= $proc['connected'] ? 'notice-ok' : 'notice-hold' ?>" style="margin-top:14px;max-width:78ch">
    <b>Payment processor:</b> <?= e($proc['name']) ?><?= $proc['mode'] !== 'none' ? ' · ' . e(strtoupper($proc['mode'])) . ' mode' : '' ?>. <?= e($proc['note']) ?>
    <?= $proc['connected'] ? '' : 'Until it is connected, every entitlement on this page is one you granted by hand, and no card is ever charged.' ?>
  </p>
</section>

<section>
  <h2>Prices, and the rules they have to keep</h2>
  <p class="small muted" style="max-width:78ch;margin-bottom:14px">The catalogue in <span class="mono">site/app/billing.php</span> is the only place these figures live on this side. The rules are checked on every visit, because a price that moves without them is how the cheap option quietly replaces the subscription.</p>
  <table class="ledger">
    <thead><tr><th>Plan</th><th>Seats</th><th>Monthly</th><th>Annual</th><th>What it covers</th></tr></thead>
    <tbody><?php foreach ($cat as $k => $p): ?>
      <tr><td><b><?= e($p['n']) ?></b></td><td class="mono"><?= (int)$p['seats'] ?></td>
        <td class="mono"><?= isset($p['month']) ? '£' . (int)$p['month'] : '£' . (int)$p['each'] . ' each' ?></td>
        <td class="mono"><?= isset($p['year']) ? '£' . (int)$p['year'] : '—' ?></td>
        <td class="small"><?= e($p['what']) ?></td></tr>
    <?php endforeach; ?></tbody>
  </table>
  <ul class="small" style="margin-top:12px;list-style:none;padding:0">
    <?php foreach ($rules as $r): ?>
      <li><span class="pill <?= $r['pass'] ? 'pill-pass' : 'pill-fail' ?>"><?= $r['pass'] ? 'holds' : 'BROKEN' ?></span>
        <?= e($r['rule']) ?> — <span class="mono"><?= e($r['says']) ?></span></li>
    <?php endforeach; ?>
  </ul>
</section>

<section>
  <h2>Stripe</h2>
  <p class="small muted" style="max-width:78ch;margin-bottom:14px">The keys live in <span class="mono">specline-config.php</span>, above the web root, where a deployment cannot overwrite them and this repository cannot leak them. The price identifiers are not secret and live here, so a price can be changed without touching that file.</p>
  <table class="ledger" style="max-width:70ch">
    <tbody>
      <tr><td>Secret key</td><td><span class="pill <?= $proc['key'] ? 'pill-pass' : 'pill-hold' ?>"><?= $proc['key'] ? 'set · ' . e($proc['mode']) . ' mode' : 'not set' ?></span></td></tr>
      <tr><td>Webhook secret</td><td><span class="pill <?= $proc['webhook'] ? 'pill-pass' : 'pill-fail' ?>"><?= $proc['webhook'] ? 'set' : 'not set — payments would be taken and never recorded' ?></span></td></tr>
      <tr><td>Webhook address</td><td class="mono small"><?= e(rtrim((string)cfg('base_url', 'https://specline.co.uk'), '/')) ?>/webhook.php</td></tr>
      <tr><td>Prices set up</td><td><span class="pill <?= $proc['prices'] === $proc['prices_total'] ? 'pill-pass' : 'pill-hold' ?>"><?= (int)$proc['prices'] ?> of <?= (int)$proc['prices_total'] ?></span></td></tr>
      <tr><td>Last event</td><td class="mono small"><?= e(setting('stripe_webhook_last', 'none yet')) ?> <?= e(setting('stripe_webhook_last_type', '')) ?></td></tr>
      <tr><td>Rejected as unsigned</td><td class="mono small"><?= e(setting('stripe_webhook_rejected', '0')) ?><?= setting('stripe_webhook_rejected_at') ? ' · last ' . e(setting('stripe_webhook_rejected_at')) : '' ?></td></tr>
      <?php /* Which code is actually answering. A deployment that silently did not happen is
               indistinguishable from a fix that did not work, and an hour went on exactly that
               confusion on 9 September 2026. The file that does the Stripe work says when the
               server last received it. */ ?>
      <tr><td>Payment code deployed</td><td class="mono small"><?= e(gmdate('Y-m-d H:i', (int)@filemtime(__DIR__ . '/../app/stripe.php'))) ?> UTC</td></tr>
    </tbody>
  </table>
  <form method="post" style="margin-top:16px"><?= csrf_field() ?><input type="hidden" name="action" value="prices">
    <p class="small muted" style="max-width:78ch">Create the products in Stripe, then paste each price identifier here. A plan with no price cannot be bought, and the subscribe page disables it rather than failing at checkout.</p>
    <table class="ledger" style="max-width:70ch"><tbody>
      <?php foreach (stripe_price_map() as $p): ?>
        <tr><td><?= e(plan_meta($p['plan'])['n']) ?> · <?= e($p['period']) ?></td>
          <td><input type="text" name="<?= e($p['key']) ?>" value="<?= e($p['id']) ?>" placeholder="price_…" style="width:100%;max-width:340px" class="mono"></td></tr>
      <?php endforeach; ?>
    </tbody></table>
    <p style="margin-top:10px"><button class="btn btn-sm btn-primary" type="submit">Save prices</button></p>
  </form>
  <?php $evs = rows('SELECT * FROM billing_events ORDER BY id DESC LIMIT 12'); if ($evs): ?>
    <h3 style="margin-top:22px">Recent events</h3>
    <table class="ledger">
      <thead><tr><th>When</th><th>Type</th><th>Practice</th><th>What this site did</th></tr></thead>
      <tbody><?php foreach ($evs as $ev): ?>
        <tr><td class="when"><?= e(substr((string)$ev['at'], 0, 16)) ?></td>
          <td class="mono small"><?= e((string)$ev['type']) ?></td>
          <td class="mono small"><?= $ev['practice_id'] ? (int)$ev['practice_id'] : '—' ?></td>
          <td class="small"><?= e((string)$ev['note']) ?></td></tr>
      <?php endforeach; ?></tbody>
    </table>
  <?php endif; ?>
</section>

<section>
  <h2>Practices <span class="count"><?= count($live) ?> entitled of <?= count($rows) ?></span></h2>
  <?php if (!$rows): ?><p class="small muted">No practices yet.</p><?php endif; ?>
  <?php foreach ($rows as $r): ?>
    <div class="doc" style="display:block;padding:14px 0">
      <div class="inline" style="justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap">
        <div>
          <b><?= e($r['practice']) ?></b>
          <span class="pill <?= $r['live'] ? 'pill-pass' : 'pill-hold' ?>"><?= e($r['live'] ? $r['plan_name'] . ' · ' . $r['status'] : 'no entitlement') ?></span>
          <?php if ($r['over'] && $r['live']): ?><span class="pill pill-fail"><?= (int)$r['seats_used'] ?> of <?= (int)$r['seats'] ?> seats</span><?php endif; ?>
          <?php if ($r['credits'] > 0): ?><span class="pill"><?= (int)$r['credits'] ?> spec credit<?= $r['credits'] === 1 ? '' : 's' ?></span><?php endif; ?>
        </div>
        <span class="small muted mono">practice <?= (int)$r['practice_id'] ?> · wants <?= e($r['intent']) ?><?= $r['ends_at'] ? ' · until ' . e(substr((string)$r['ends_at'], 0, 10)) : '' ?></span>
      </div>
      <?php if ($r['live'] && $r['note']): ?><p class="small muted" style="margin:8px 0 0"><?= e($r['note']) ?></p><?php endif; ?>
      <div class="inline" style="gap:18px;margin-top:12px;flex-wrap:wrap">
        <form method="post" class="inline" style="gap:8px"><?= csrf_field() ?>
          <input type="hidden" name="action" value="grant"><input type="hidden" name="practice_id" value="<?= (int)$r['practice_id'] ?>">
          <select name="plan" aria-label="Plan"><?php foreach ($cat as $k => $p) echo '<option value="' . e($k) . '">' . e($p['n']) . '</option>'; ?></select>
          <select name="status" aria-label="Status"><option value="active">active</option><option value="trialing">trial</option></select>
          <select name="months" aria-label="For"><option value="0">open-ended</option><option value="1">1 month</option><option value="3">3 months</option><option value="12" selected>12 months</option></select>
          <select name="source" aria-label="Why"><option value="manual">granted</option><option value="founding">founding member</option><option value="comp">complimentary</option><option value="invoice">invoiced</option></select>
          <input type="text" name="note" placeholder="note (optional)" maxlength="200" style="max-width:200px">
          <button class="btn btn-sm btn-primary" type="submit">Grant</button>
        </form>
        <form method="post" class="inline" style="gap:8px"><?= csrf_field() ?>
          <input type="hidden" name="action" value="credits"><input type="hidden" name="practice_id" value="<?= (int)$r['practice_id'] ?>">
          <input type="number" name="n" value="1" min="1" max="50" style="width:70px" aria-label="Credits">
          <input type="text" name="note" placeholder="reason" maxlength="40" style="max-width:150px">
          <button class="btn btn-sm" type="submit">Add spec credits</button>
        </form>
        <?php if ($r['live']): ?>
        <form method="post" class="inline" style="gap:8px"><?= csrf_field() ?>
          <input type="hidden" name="action" value="end"><input type="hidden" name="practice_id" value="<?= (int)$r['practice_id'] ?>">
          <input type="text" name="note" placeholder="why it ended" maxlength="200" style="max-width:180px">
          <button class="btn btn-sm btn-danger" type="submit">End</button>
        </form>
        <?php endif; ?>
      </div>
    </div>
  <?php endforeach; ?>
</section>

<section>
  <h2>Per-spec ledger</h2>
  <p class="small muted" style="max-width:78ch;margin-bottom:12px">Every credit bought, granted or spent. A specification issued by a per-spec practice spends one; the job it was spent on is named, so a balance can always be explained.</p>
  <?php if (!$ledger): ?><p class="small muted">Nothing yet.</p><?php else: ?>
  <table class="ledger">
    <thead><tr><th>When</th><th>Practice</th><th>Change</th><th>Why</th><th>Job</th><th>By</th></tr></thead>
    <tbody><?php foreach ($ledger as $l): ?>
      <tr><td class="mono small"><?= e(substr((string)$l['at'], 0, 16)) ?></td>
        <td><?= e((string)($l['name'] ?? '')) ?></td>
        <td class="mono"><?= (int)$l['delta'] > 0 ? '+' . (int)$l['delta'] : (int)$l['delta'] ?></td>
        <td class="small"><?= e((string)$l['reason']) ?></td>
        <td class="mono small"><?= e((string)$l['job_id']) ?></td>
        <td class="small muted"><?= e((string)$l['by_who']) ?></td></tr>
    <?php endforeach; ?></tbody>
  </table>
  <?php endif; ?>
</section>

<section>
  <h2>What is still to do</h2>
  <ul class="small" style="max-width:78ch;list-style:none;padding:0">
    <li><b>Choose a processor.</b> Stripe means you handle VAT yourself; a merchant of record (Paddle, Lemon Squeezy) charges and remits it for you and takes a larger cut. The questions are set out in <span class="mono">docs/TERMS-DRAFT.md</span>.</li>
    <li><b>The solicitor.</b> Terms and the privacy notice are drafted in house and say so on the page. Billing adds auto-renewal, refunds and the founding-member promise, which are the parts worth paying for advice on.</li>
    <li><b>Issuing spends a credit.</b> The server can already do it (<span class="mono">consume_spec_credit()</span>); the app has still to call it at the moment of issue, or per-spec cannot be enforced.</li>
  </ul>
</section>
<?php page_end(); ?>
