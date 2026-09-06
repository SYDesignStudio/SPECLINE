<?php
require __DIR__ . '/../app/bootstrap.php';
if (current_user()) redirect('/account/');
$next = (string)($_GET['next'] ?? $_POST['next'] ?? '/account/');
if (!preg_match('#^/(account|admin)(/|$)#', $next)) $next = '/account/';

$error = null;
if (is_post()) {
    csrf_check();
    $email = mb_strtolower(clean('email', 254));
    $pass  = (string)($_POST['password'] ?? '');
    if (!throttle('login-ip:' . client_ip(), 20, 900) || !throttle('login-email:' . $email, 8, 900)) {
        $error = 'Too many attempts. Wait fifteen minutes and try again, or reset your password.';
    } else {
        $u = valid_email($email) ? row('SELECT * FROM users WHERE email = ?', [$email]) : null;
        /* Verify against a real hash even when the address is unknown, so the response time
           does not say whether the account exists. */
        $ok = password_verify($pass, $u['pass_hash'] ?? '$2y$10$abcdefghijklmnopqrstuuA9Q1vY6Wc0j5s2K0fTq5eZ9vPq6T0nq6');
        if ($u && $ok) {
            if (password_needs_rehash($u['pass_hash'], PASSWORD_DEFAULT)) q('UPDATE users SET pass_hash = ? WHERE id = ?', [password_hash($pass, PASSWORD_DEFAULT), (int)$u['id']]);
            login_user($u);
            audit('login', $email);
            redirect($next);
        }
        $error = 'That email and password do not match. Check both, or reset your password below.';
        audit('login-failed', $email);
    }
}
page_start('Sign in');
?>
<div class="sheet">
  <h1>Sign in</h1>
  <p class="lede">To your practice's Specline account.</p>
  <?php show_flash(); if ($error) echo '<ul class="errs"><li>' . e($error) . '</li></ul>'; ?>
  <form class="stack" method="post" action="/account/login.php" novalidate>
    <?= csrf_field() ?>
    <input type="hidden" name="next" value="<?= e($next) ?>">
    <?= field('email', 'Email', 'email', ['required' => true, 'autocomplete' => 'email', 'autofocus' => true]) ?>
    <div class="field"><label for="f_password">Password</label><input id="f_password" type="password" name="password" required autocomplete="current-password"></div>
    <div class="actions">
      <button class="btn btn-primary" type="submit">Sign in</button>
      <a href="/account/forgot.php">Forgotten your password?</a>
    </div>
  </form>
  <hr>
  <p class="small muted">No account yet? <a href="/account/signup.php">Create one</a>. It takes a minute and there is nothing to pay.</p>
</div>
<?php page_end();
