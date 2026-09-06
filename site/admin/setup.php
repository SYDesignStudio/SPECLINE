<?php
/* Claiming the administrator role.
 *
 * There is no default password and no hard-coded administrator. The first time this page is
 * opened it writes a random key to the domain directory ABOVE public_html — a place only
 * someone with SFTP or File Manager access can read, and which no deployment touches. Enter
 * that key while signed in and your account becomes the owner. After that this page is closed.
 */
require __DIR__ . '/../app/bootstrap.php';
$u = require_login();

if (admin_exists()) {
    page_start('Setup');
    echo '<div class="sheet"><h1>Already set up</h1><p class="lede">An administrator account exists, so this page is closed. If you need administrator access, ask the person who holds it.</p><p><a href="/account/">Back to your account</a></p></div>';
    page_end(); exit;
}

if (!is_readable(SETUP_KEY_FILE)) {
    $key = bin2hex(random_bytes(16));
    @file_put_contents(SETUP_KEY_FILE, $key . "\n");
    @chmod(SETUP_KEY_FILE, 0600);
}
$error = null;
if (is_post()) {
    csrf_check();
    if (!throttle('setup:' . client_ip(), 10, 3600)) $error = 'Too many attempts. Wait an hour.';
    else {
        $given = preg_replace('/[^0-9a-f]/', '', strtolower((string)($_POST['key'] ?? '')));
        $want  = trim((string)@file_get_contents(SETUP_KEY_FILE));
        if ($want !== '' && hash_equals($want, (string)$given)) {
            q("UPDATE users SET role = 'owner', verified_at = COALESCE(verified_at, ?) WHERE id = ?", [now(), (int)$u['id']]);
            @unlink(SETUP_KEY_FILE);
            audit('admin-claimed', $u['email']);
            flash('You are now the Specline administrator.');
            redirect('/admin/');
        }
        $error = 'That key does not match the one in the file.';
    }
}
page_start('Set up administration');
?>
<div class="sheet">
  <h1>Claim administration</h1>
  <p class="lede">A key has been written to a file on the server, outside the public web root. Read it over SFTP or in Hostinger's File Manager and paste it below. Doing so makes <span class="mono"><?= e($u['email']) ?></span> the administrator, and closes this page for good.</p>
  <p class="keyblock"><?= e(SETUP_KEY_FILE) ?></p>
  <?php if ($error) echo '<ul class="errs"><li>' . e($error) . '</li></ul>'; ?>
  <form class="stack" method="post" action="/admin/setup.php" novalidate>
    <?= csrf_field() ?>
    <?= field('key', 'Setup key', 'text', ['required' => true, 'autocomplete' => 'off', 'spellcheck' => 'false', 'autofocus' => true]) ?>
    <div class="actions"><button class="btn btn-primary" type="submit">Claim administration</button><a href="/account/">Cancel</a></div>
  </form>
</div>
<?php page_end();
