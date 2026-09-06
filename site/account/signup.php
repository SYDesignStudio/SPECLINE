<?php
require __DIR__ . '/../app/bootstrap.php';
if (current_user()) redirect('/account/');

/* Closed before launch. The form is not rendered and a POST is refused, so this cannot be
   walked past by sending the form directly. The waiting list stays open, which is the whole
   reason for having one. */
if (site_locked()) {
    http_response_code(403);
    page_start('Not open yet');
    ?>
    <div class="sheet">
      <h1>Specline is not open yet</h1>
      <p class="lede">Accounts are closed while the first release is finished. Join the waiting list and you will be emailed when Specline opens to your practice.</p>
      <p class="actions"><a class="btn btn-primary" href="/#join">Join the waiting list</a><a href="/account/login.php">I already have an account</a></p>
      <hr>
      <p class="small muted">Specline drafts Building Regulations specifications for building control across eight residential project types in England, issued under your own practice's name. There is nothing to pay to join the list.</p>
    </div>
    <?php
    page_end();
    exit;
}

$errors = [];
if (is_post()) {
    csrf_check();
    if (trim((string)($_POST['website'] ?? '')) !== '') redirect('/account/login.php');   // honeypot
    $practice = clean('practice', 150);
    $name     = clean('name', 120);
    $email    = mb_strtolower(clean('email', 254));
    $pass     = (string)($_POST['password'] ?? '');
    $plan     = in_array($_POST['plan'] ?? '', ['solo', 'practice', 'payg', 'undecided'], true) ? $_POST['plan'] : 'undecided';
    $agree    = ($_POST['agree'] ?? '') === 'yes';

    if ($practice === '') $errors[] = 'Enter the practice name. It is what goes on your specifications.';
    if ($name === '')     $errors[] = 'Enter your name.';
    if (!valid_email($email)) $errors[] = 'That email address does not look right.';
    if ($p = password_problem($pass, $email)) $errors[] = $p;
    if (!$agree)          $errors[] = 'Please confirm you have read the terms and the privacy notice.';
    if (!$errors && !throttle('signup:' . client_ip(), 5, 3600)) $errors[] = 'Several accounts have been created from this connection in the last hour. Try again later.';
    if (!$errors && row('SELECT id FROM users WHERE email = ?', [$email])) {
        /* Say the same thing whether or not the address is taken, so the form cannot be used to
           test addresses. The existing owner gets an email telling them what happened. */
        $u = row('SELECT * FROM users WHERE email = ?', [$email]);
        send_mail($email, 'Specline: an account already exists for this address',
            "Someone tried to create a Specline account with this email address, which already has one.\n\nIf this was you, sign in at " . cfg('base_url') . "/account/login.php or reset your password at " . cfg('base_url') . "/account/forgot.php\n\nIf it was not you, no action is needed.\n");
        flash('Check your email to verify the address and finish creating the account.');
        redirect('/account/login.php');
    }
    if (!$errors) {
        $pdo = db(); $pdo->beginTransaction();
        try {
            q('INSERT INTO practices (name, plan, created_at) VALUES (?, ?, ?)', [$practice, $plan, now()]);
            $pid = (int)$pdo->lastInsertId();
            q('INSERT INTO users (practice_id, email, name, pass_hash, role, created_at, source) VALUES (?, ?, ?, ?, ?, ?, ?)',
              [$pid, $email, $name, password_hash($pass, PASSWORD_DEFAULT), 'member', now(), 'site']);
            $uid = (int)$pdo->lastInsertId();
            $pdo->commit();
        } catch (Throwable $t) { $pdo->rollBack(); error_log('signup: ' . $t->getMessage()); $errors[] = 'Something went wrong at our end. Please try again, or email info@specline.co.uk.'; }
    }
    if (!$errors) {
        $tok = issue_token($uid, 'verify', 86400);
        send_mail($email, 'Verify your Specline account',
            "Hello {$name},\n\nConfirm this email address to finish setting up the Specline account for {$practice}:\n\n" . cfg('base_url') . "/account/verify.php?t={$tok}\n\nThe link works for 24 hours.\n\nSpecline drafts specifications; the named designer remains responsible for them. This account is your place in the queue for the first release — there is nothing to pay today.\n");
        notify_studio('Specline sign-up: ' . $practice, "New account\n\nPractice: {$practice}\nName:     {$name}\nEmail:    {$email}\nPlan:     {$plan}\nWhen:     " . now() . "\n\n" . cfg('base_url') . "/admin/signups.php\n", $email);
        audit('signup', $email);
        login_user(row('SELECT * FROM users WHERE id = ?', [$uid]));
        flash('Your account is created. We have sent a link to ' . $email . ' to verify the address.');
        redirect('/account/');
    }
}

page_start('Create an account');
?>
<div class="sheet">
  <h1>Create an account</h1>
  <p class="lede">An account is your practice's identity on Specline and its place in the queue for the first release. There is nothing to pay today, and no card is asked for.</p>
  <?php if ($errors): ?><ul class="errs"><?php foreach ($errors as $x) echo '<li>' . e($x) . '</li>'; ?></ul><?php endif; ?>
  <form class="stack" method="post" action="/account/signup.php" novalidate>
    <?= csrf_field() ?>
    <?= field('practice', 'Practice name', 'text', ['required' => true, 'autocomplete' => 'organization', 'maxlength' => 150]) ?>
    <div class="row2">
      <?= field('name', 'Your name', 'text', ['required' => true, 'autocomplete' => 'name', 'maxlength' => 120]) ?>
      <?= field('email', 'Email', 'email', ['required' => true, 'autocomplete' => 'email', 'maxlength' => 254]) ?>
    </div>
    <div class="field">
      <label for="f_password">Password</label>
      <input id="f_password" type="password" name="password" required autocomplete="new-password" minlength="12" maxlength="200">
      <span class="hint">At least 12 characters. A short sentence you will remember is stronger than a word with numbers.</span>
    </div>
    <div class="field">
      <label for="f_plan">Plan you have in mind</label>
      <select id="f_plan" name="plan">
        <?php $cur = $_POST['plan'] ?? 'undecided';
        foreach (['undecided' => 'Not decided yet', 'solo' => 'Solo — 1 user, £39 a month', 'practice' => 'Practice — up to 5 users, £89 a month', 'payg' => 'Per specification — £25 each'] as $k => $v)
            echo '<option value="' . $k . '"' . ($cur === $k ? ' selected' : '') . '>' . e($v) . '</option>'; ?>
      </select>
      <span class="hint">Prices ex VAT. Nothing is charged until Specline opens and you choose to subscribe.</span>
    </div>
    <label class="check"><input type="checkbox" name="agree" value="yes" <?= ($_POST['agree'] ?? '') === 'yes' ? 'checked' : '' ?>><span>I have read the <a href="/terms.html" target="_blank" rel="noopener">terms</a> and the <a href="/privacy.html" target="_blank" rel="noopener">privacy notice</a>, and I understand that Specline drafts specifications and does not certify compliance.</span></label>
    <div style="position:absolute;left:-9999px" aria-hidden="true"><label>Website<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
    <div class="actions">
      <button class="btn btn-primary" type="submit">Create account</button>
      <a href="/account/login.php">I already have one</a>
    </div>
  </form>
</div>
<?php page_end();
