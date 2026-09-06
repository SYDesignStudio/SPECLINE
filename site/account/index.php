<?php
require __DIR__ . '/../app/bootstrap.php';
$u = require_login();
$practice = row('SELECT * FROM practices WHERE id = ?', [(int)$u['practice_id']]);
$errors = [];

if (is_post()) {
    csrf_check();
    $action = (string)($_POST['action'] ?? '');
    if ($action === 'resend' && empty($u['verified_at'])) {
        if (throttle('resend:' . $u['id'], 3, 3600)) {
            $tok = issue_token((int)$u['id'], 'verify', 86400);
            send_mail($u['email'], 'Verify your Specline account', "Hello {$u['name']},\n\nConfirm this email address:\n\n" . cfg('base_url') . "/account/verify.php?t={$tok}\n\nThe link works for 24 hours.\n");
            flash('A new verification link is on its way to ' . $u['email'] . '.');
        } else flash('Three links have already been sent in the last hour. Check your spam folder before asking again.', 'hold');
        redirect('/account/');
    }
    if ($action === 'profile') {
        $name = clean('practice', 150); $designer = clean('designer', 120); $address = clean('address', 400); $phone = clean('phone', 40);
        $contact = mb_strtolower(clean('contact_email', 254));
        $plan = in_array($_POST['plan'] ?? '', ['solo', 'practice', 'payg', 'undecided'], true) ? $_POST['plan'] : 'undecided';
        $seats = max(1, min(50, (int)($_POST['seats'] ?? 1)));
        if ($name === '') $errors[] = 'The practice needs a name; it is what goes on the specification.';
        if ($contact !== '' && !valid_email($contact)) $errors[] = 'That contact email address does not look right.';
        if (!$errors) {
            q('UPDATE practices SET name = ?, designer = ?, address = ?, phone = ?, plan = ?, seats = ?, contact_email = ? WHERE id = ?', [$name, $designer, $address, $phone, $plan, $seats, $contact, (int)$practice['id']]);
            audit('profile', $u['email']);
            flash('Practice details saved.');
            redirect('/account/');
        }
    }
    if ($action === 'password') {
        $cur = (string)($_POST['current'] ?? ''); $new = (string)($_POST['password'] ?? '');
        if (!password_verify($cur, $u['pass_hash'])) $errors[] = 'The current password is not right.';
        elseif ($p = password_problem($new, $u['email'])) $errors[] = $p;
        else { q('UPDATE users SET pass_hash = ? WHERE id = ?', [password_hash($new, PASSWORD_DEFAULT), (int)$u['id']]); audit('password-changed', $u['email']); flash('Password changed.'); redirect('/account/'); }
    }
}
$opening = setting('opening_note', 'Specline opens to founding members first. You will be emailed when your account can open the application.');
$canOpen = app_access($u);
$jobCount = (int)val('SELECT COUNT(*) FROM jobs WHERE practice_id = ?', [(int)$practice['id']]);
page_start('Your account');
?>
<div class="sheet">
  <h1><?= e($practice['name']) ?></h1>
  <p class="lede">Signed in as <?= e($u['name']) ?> · <span class="mono"><?= e($u['email']) ?></span></p>
  <?php show_flash(); if ($errors): ?><ul class="errs"><?php foreach ($errors as $x) echo '<li>' . e($x) . '</li>'; ?></ul><?php endif; ?>

  <?php if (empty($u['verified_at'])): ?>
    <form method="post" action="/account/" class="notice notice-hold" style="display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap">
      <?= csrf_field() ?><input type="hidden" name="action" value="resend">
      <span>Your email address is not verified yet. The link we sent works for 24 hours.</span>
      <button class="btn btn-sm" type="submit">Send it again</button>
    </form>
  <?php endif; ?>

  <div class="status-line">
    <?php if ($canOpen): ?>
      <a class="btn btn-primary" href="/app.php">Open the specification tool</a>
      <span class="small muted"><?= $jobCount ? 'Your practice has ' . $jobCount . ' saved job' . ($jobCount === 1 ? '' : 's') . '. They are stored here, not in the browser.' : 'Nothing saved yet. Jobs you start are stored against your practice.' ?></span>
    <?php else: ?>
      <span class="pill pill-petrol">Founding member queue</span>
      <span class="small muted"><?= empty($u['verified_at']) ? 'Verify your email address and the tool opens on this page.' : e($opening) ?></span>
    <?php endif; ?>
  </div>

  <dl class="defs">
    <dt>Plan in mind</dt><dd><?= e(['solo' => 'Solo · £39 a month', 'practice' => 'Practice · £89 a month', 'payg' => 'Per specification · £25', 'undecided' => 'Not decided'][$practice['plan']] ?? $practice['plan']) ?></dd>
    <dt>Seats</dt><dd class="mono"><?= (int)$practice['seats'] ?></dd>
    <dt>Account created</dt><dd class="mono"><?= e(fmt_when($u['created_at'])) ?></dd>
    <dt>Billing</dt><dd>None yet. Nothing is charged until Specline opens and you choose a plan.</dd>
  </dl>

  <hr>
  <h2>Practice details</h2>
  <p class="small muted" style="margin:6px 0 18px">These go on the cover, the running footer and the responsibility statement of every specification you issue. Specline's name never appears on them.</p>
  <form class="stack" method="post" action="/account/" novalidate>
    <?= csrf_field() ?><input type="hidden" name="action" value="profile">
    <?= field('practice', 'Practice name', 'text', ['required' => true, 'maxlength' => 150, 'value' => $practice['name']]) ?>
    <div class="row2">
      <?= field('designer', 'Named designer', 'text', ['maxlength' => 120, 'value' => $practice['designer']]) ?>
      <?= field('phone', 'Phone', 'text', ['maxlength' => 40, 'value' => $practice['phone']]) ?>
    </div>
    <div class="field">
      <label for="f_contact_email">Contact email on the specification</label>
      <input id="f_contact_email" type="email" name="contact_email" maxlength="254" value="<?= e($practice['contact_email'] ?? '') ?>" placeholder="<?= e($u['email']) ?>">
      <span class="hint">What a building control officer reads on the cover and replies to. Separate from your sign-in address, so a second person in the practice does not change it. Left blank, your sign-in address is used.</span>
    </div>
    <?= field('address', 'Address', 'textarea', ['maxlength' => 400, 'value' => $practice['address'], 'style' => 'min-height:80px']) ?>
    <div class="row2">
      <div class="field"><label for="f_plan">Plan in mind</label><select id="f_plan" name="plan">
        <?php foreach (['undecided' => 'Not decided yet', 'solo' => 'Solo — 1 user', 'practice' => 'Practice — up to 5 users', 'payg' => 'Per specification'] as $k => $v) echo '<option value="' . $k . '"' . ($practice['plan'] === $k ? ' selected' : '') . '>' . e($v) . '</option>'; ?>
      </select></div>
      <?= field('seats', 'Seats you expect to need', 'number', ['min' => 1, 'max' => 50, 'value' => (string)$practice['seats']]) ?>
    </div>
    <div class="actions"><button class="btn btn-primary" type="submit">Save details</button></div>
  </form>

  <hr>
  <h2>Change password</h2>
  <form class="stack" method="post" action="/account/" novalidate style="margin-top:14px">
    <?= csrf_field() ?><input type="hidden" name="action" value="password">
    <div class="row2">
      <div class="field"><label for="f_current">Current password</label><input id="f_current" type="password" name="current" autocomplete="current-password"></div>
      <div class="field"><label for="f_newpass">New password</label><input id="f_newpass" type="password" name="password" autocomplete="new-password" minlength="12"></div>
    </div>
    <div class="actions"><button class="btn" type="submit">Change password</button></div>
  </form>
</div>
<?php page_end();
