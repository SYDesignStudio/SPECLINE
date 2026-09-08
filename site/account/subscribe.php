<?php
/* Choosing a plan, and paying for it.
 *
 * The page never touches a card: it asks Stripe for a Checkout Session and sends the browser
 * there, and Stripe sends the browser back. Nothing on this site stores a card number, and the
 * entitlement is not written here either — it is written when Stripe's webhook says the money
 * arrived. A page that granted access on the way back from checkout would grant it to anyone who
 * could guess the return address.
 */
require __DIR__ . '/../app/bootstrap.php';
$u = require_login();
$practice = row('SELECT * FROM practices WHERE id = ?', [(int)$u['practice_id']]);
$pid = (int)$practice['id'];
$proc = processor_status();
$cat = plan_catalogue();
$ent = entitlement($pid);
$base = rtrim((string)cfg('base_url', ''), '/') ?: (( !empty($_SERVER['HTTPS']) ? 'https' : 'http') . '://' . ($_SERVER['HTTP_HOST'] ?? 'localhost'));

if (is_post()) {
    csrf_check();
    $a = (string)($_POST['action'] ?? '');
    if (!$proc['connected']) {
        flash('Payment is not connected yet, so nothing can be bought. Nothing was charged.', 'hold');
        redirect('/account/subscribe.php');
    }
    /* A limit on how often we may ask Stripe to open a checkout, not on how often someone may
       change their mind. Twelve an hour blocked a first evening of testing, so: thirty, and the
       message says what to do rather than telling someone off. The key is versioned because
       raising the limit does nothing for a window that has already filled. */
    if (!throttle('checkout2:' . $u['id'], 30, 3600)) {
        flash('Thirty checkouts have been opened from this account in the last hour, so this one was not. Nothing is charged for an abandoned checkout. Wait an hour, or ask us and we will clear it.', 'hold');
        redirect('/account/subscribe.php');
    }
    if ($a === 'subscribe') {
        $plan   = in_array($_POST['plan'] ?? '', ['solo', 'practice'], true) ? (string)$_POST['plan'] : 'solo';
        $period = ($_POST['period'] ?? '') === 'year' ? 'year' : 'month';
        $r = stripe_checkout($pid, $plan, $period, 1, (string)($practice['contact_email'] ?: $u['email']), $base);
        if ($r['ok'] && $r['url']) redirect($r['url']);
        flash($r['error'] ?? 'Stripe would not open a checkout.', 'err');
    } elseif ($a === 'credits') {
        $n = max(1, min(20, (int)($_POST['n'] ?? 1)));
        $r = stripe_checkout($pid, 'payg', 'each', $n, (string)($practice['contact_email'] ?: $u['email']), $base);
        if ($r['ok'] && $r['url']) redirect($r['url']);
        flash($r['error'] ?? 'Stripe would not open a checkout.', 'err');
    } elseif ($a === 'portal') {
        $r = stripe_portal($pid, $base);
        if ($r['ok'] && $r['url']) redirect($r['url']);
        flash($r['error'] ?? 'Stripe would not open the billing portal.', 'err');
    }
    redirect('/account/subscribe.php');
}

page_start('Plans');
?>
<div class="sheet">
  <h1>Plans</h1>
  <?php if (isset($_GET['done'])): ?>
    <p class="notice notice-ok">Payment received. Stripe confirms it to us separately, which usually takes a moment — this page and your account will show the subscription as soon as it does.</p>
  <?php elseif (isset($_GET['cancelled'])): ?>
    <p class="notice notice-hold">Checkout cancelled. Nothing was charged.</p>
  <?php endif; ?>
  <?php show_flash(); ?>

  <p class="lede">Prices exclude VAT. Annual is ten months. Every plan carries your own practice’s name, logo and address on the specifications it produces — white-labelling is not an upgrade.</p>

  <?php if ($ent['live']): ?>
    <p class="notice <?= $ent['status'] === 'past_due' ? 'notice-hold' : 'notice-ok' ?>">
      <b>Your subscription:</b> <?= e($ent['plan_name']) ?><?= $ent['status'] === 'trialing' ? ' (trial)' : '' ?><?= $ent['ends_at'] ? ', renewing ' . e(substr((string)$ent['ends_at'], 0, 10)) : '' ?>.
      <?php if ($ent['status'] === 'past_due'): ?>
        The last payment did not go through. The tool stays open while the card is retried — update it below before the subscription ends.
      <?php endif; ?>
    </p>
  <?php endif; ?>

  <?php if (!$proc['connected']): ?>
    <p class="notice notice-hold"><b>Payment is not connected yet.</b> <?= e($proc['note']) ?> Nothing on this page can charge you.</p>
  <?php elseif ($proc['mode'] === 'test'): ?>
    <p class="notice notice-hold"><b>Test mode.</b> Cards are not really charged. Use Stripe’s test card 4242 4242 4242 4242 with any future date.</p>
  <?php endif; ?>

  <div class="plans">
    <?php foreach (['solo', 'practice'] as $k): $p = $cat[$k]; ?>
      <div class="plan">
        <h2><?= e($p['n']) ?></h2>
        <p class="mono" style="font-size:22px;margin:6px 0">£<?= (int)$p['month'] ?><span class="small muted"> a month</span></p>
        <p class="small muted">or £<?= (int)$p['year'] ?> a year — ten months</p>
        <p class="small"><?= e($p['what']) ?></p>
        <form method="post" class="inline" style="gap:8px;margin-top:10px"><?= csrf_field() ?>
          <input type="hidden" name="action" value="subscribe"><input type="hidden" name="plan" value="<?= e($k) ?>">
          <button class="btn btn-primary btn-sm" name="period" value="month" <?= $proc['connected'] ? '' : 'disabled' ?>>Monthly</button>
          <button class="btn btn-sm" name="period" value="year" <?= $proc['connected'] ? '' : 'disabled' ?>>Annual</button>
        </form>
      </div>
    <?php endforeach; ?>
  </div>

  <div class="plan" style="margin-top:16px">
    <h2><?= e($cat['payg']['n']) ?></h2>
    <p class="mono" style="font-size:22px;margin:6px 0">£<?= (int)$cat['payg']['each'] ?><span class="small muted"> each</span></p>
    <p class="small"><?= e($cat['payg']['what']) ?> One credit is spent when you issue a specification; drafting costs nothing.</p>
    <?php if ($ent['credits'] > 0): ?><p class="small"><b><?= (int)$ent['credits'] ?></b> credit<?= $ent['credits'] === 1 ? '' : 's' ?> in hand.</p><?php endif; ?>
    <form method="post" class="inline" style="gap:8px;margin-top:10px"><?= csrf_field() ?>
      <input type="hidden" name="action" value="credits">
      <label class="small" for="n">How many</label>
      <input id="n" type="number" name="n" value="1" min="1" max="20" style="width:80px">
      <button class="btn btn-sm" type="submit" <?= $proc['connected'] ? '' : 'disabled' ?>>Buy credits</button>
    </form>
  </div>

  <?php if (!empty($practice['stripe_customer_id'])): ?>
    <hr>
    <h2>Manage billing</h2>
    <p class="small muted">Change the card, download invoices or cancel. Stripe handles it; cancelling leaves every job exactly where it is.</p>
    <form method="post"><?= csrf_field() ?><input type="hidden" name="action" value="portal">
      <button class="btn btn-sm" type="submit">Open the billing portal</button>
    </form>
  <?php endif; ?>

  <hr>
  <p class="small muted">Terms are at <a href="/terms.html">specline.co.uk/terms.html</a>. They are drafted in house and say so; a solicitor has not reviewed them yet, and that is stated on the page rather than hidden.</p>
  <p><a href="/account/">Back to your account</a></p>
</div>
<script>
/* The button posts here, this page asks Stripe for a checkout, and only then does the browser
   move — a second or two in which the page looks untouched and invites another click. Twelve
   sessions were opened in thirty-six seconds that way on the first evening of testing. So the
   buttons say what is happening and refuse a second press; the form still works without this
   script, it just goes back to being silent. */
document.querySelectorAll('form').forEach(function (f) {
  f.addEventListener('submit', function () {
    var pressed = f.querySelector('button:focus') || f.querySelector('button');
    f.querySelectorAll('button').forEach(function (b) { b.disabled = true; });
    if (pressed) { pressed.dataset.was = pressed.textContent; pressed.textContent = 'Opening Stripe…'; }
    /* If the redirect never comes — a network drop, Stripe refusing — give the page back rather
       than leaving a dead form behind. */
    setTimeout(function () {
      f.querySelectorAll('button').forEach(function (b) { b.disabled = false; });
      if (pressed && pressed.dataset.was) pressed.textContent = pressed.dataset.was;
    }, 12000);
  });
});
</script>
<?php page_end(); ?>
