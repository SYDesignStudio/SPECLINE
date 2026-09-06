<?php
require __DIR__ . '/../app/bootstrap.php';
$done = false;
if (is_post()) {
    csrf_check();
    $email = mb_strtolower(clean('email', 254));
    if (throttle('forgot:' . client_ip(), 5, 3600) && valid_email($email)) {
        if ($u = row('SELECT * FROM users WHERE email = ?', [$email])) {
            $tok = issue_token((int)$u['id'], 'reset', 3600);
            send_mail($email, 'Reset your Specline password',
                "Hello {$u['name']},\n\nUse this link to choose a new password. It works for one hour and once only:\n\n" . cfg('base_url') . "/account/reset.php?t={$tok}\n\nIf you did not ask for this, ignore it; your password has not changed.\n");
            audit('reset-requested', $email);
        }
    }
    $done = true;   /* the same answer whether or not the address exists */
}
page_start('Reset your password');
?>
<div class="sheet">
  <h1>Reset your password</h1>
  <?php if ($done): ?>
    <p class="lede">If that address has an account, an email with a reset link is on its way. The link works for one hour.</p>
    <p><a href="/account/login.php">Back to sign in</a></p>
  <?php else: ?>
    <p class="lede">Enter the email address on the account and we will send a link to choose a new password.</p>
    <form class="stack" method="post" action="/account/forgot.php" novalidate>
      <?= csrf_field() ?>
      <?= field('email', 'Email', 'email', ['required' => true, 'autocomplete' => 'email', 'autofocus' => true]) ?>
      <div class="actions"><button class="btn btn-primary" type="submit">Send the link</button><a href="/account/login.php">Back to sign in</a></div>
    </form>
  <?php endif; ?>
</div>
<?php page_end();
