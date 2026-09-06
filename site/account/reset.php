<?php
require __DIR__ . '/../app/bootstrap.php';
$raw = (string)($_POST['t'] ?? $_GET['t'] ?? '');
$errors = [];
if (is_post()) {
    csrf_check();
    $pass = (string)($_POST['password'] ?? '');
    $again = (string)($_POST['again'] ?? '');
    $peek = preg_match('/^[0-9a-f]{64}$/', $raw) ? row('SELECT u.* FROM tokens t JOIN users u ON u.id = t.user_id WHERE t.hash = ? AND t.kind = ? AND t.used_at IS NULL', [hash('sha256', $raw), 'reset']) : null;
    if (!$peek) $errors[] = 'This reset link has expired or was already used. Ask for a new one.';
    elseif ($p = password_problem($pass, $peek['email'])) $errors[] = $p;
    elseif ($pass !== $again) $errors[] = 'The two passwords do not match.';
    if (!$errors) {
        $u = consume_token($raw, 'reset');
        if (!$u) $errors[] = 'This reset link has expired or was already used. Ask for a new one.';
        else {
            q('UPDATE users SET pass_hash = ? WHERE id = ?', [password_hash($pass, PASSWORD_DEFAULT), (int)$u['id']]);
            audit('reset-done', $u['email']);
            /* The new password is saved either way; the lock only decides whether the reset
               also signs them in. It used to sign anyone in, straight past the lock. */
            if (login_user($u)) {
                flash('Your password is changed and you are signed in.');
                redirect('/account/');
            }
            flash('Your password is changed. ' . LOCKED_MESSAGE, 'hold');
            redirect('/account/login.php');
        }
    }
}
page_start('Choose a new password');
?>
<div class="sheet">
  <h1>Choose a new password</h1>
  <?php if ($errors): ?><ul class="errs"><?php foreach ($errors as $x) echo '<li>' . e($x) . '</li>'; ?></ul><?php endif; ?>
  <form class="stack" method="post" action="/account/reset.php" novalidate>
    <?= csrf_field() ?>
    <input type="hidden" name="t" value="<?= e($raw) ?>">
    <div class="field"><label for="f_password">New password</label><input id="f_password" type="password" name="password" required autocomplete="new-password" minlength="12" maxlength="200" autofocus><span class="hint">At least 12 characters.</span></div>
    <div class="field"><label for="f_again">The same again</label><input id="f_again" type="password" name="again" required autocomplete="new-password"></div>
    <div class="actions"><button class="btn btn-primary" type="submit">Save the new password</button><a href="/account/forgot.php">Ask for a new link</a></div>
  </form>
</div>
<?php page_end();
