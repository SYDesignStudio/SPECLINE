<?php
require __DIR__ . '/../app/bootstrap.php';
$u = consume_token((string)($_GET['t'] ?? ''), 'verify');
if ($u) {
    if (empty($u['verified_at'])) q('UPDATE users SET verified_at = ? WHERE id = ?', [now(), (int)$u['id']]);
    audit('verified', $u['email']);
    /* Verifying still records the address while the site is locked; it just does not sign
       anyone in past the lock. */
    if (current_user() || login_user($u)) {
        flash('Thank you — ' . $u['email'] . ' is verified.');
        redirect('/account/');
    }
    flash('Thank you — ' . $u['email'] . ' is verified. ' . LOCKED_MESSAGE, 'hold');
    redirect('/account/login.php');
}
page_start('Verify your email');
?>
<div class="sheet">
  <h1>That link has expired</h1>
  <p class="lede">Verification links work for 24 hours and once only. Sign in and ask for a new one from your account page.</p>
  <p><a class="btn btn-primary" href="/account/login.php">Sign in</a></p>
</div>
<?php page_end();
