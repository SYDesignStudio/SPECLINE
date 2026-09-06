<?php
/* Confirming a change of sign-in address.
 *
 * The address moves HERE and nowhere else: asking for the change only sends a link to the
 * proposed address, so the change completes only if the person asking can read that mailbox.
 * If the mail never arrives, nothing happens and the old address still works — which is the
 * behaviour you want, because the alternative is locking someone out of their own account.
 */
require __DIR__ . '/../app/bootstrap.php';

$payload = null;
$u = consume_token((string)($_GET['t'] ?? ''), 'email', $payload);
$new = mb_strtolower(trim((string)$payload));

if ($u && valid_email($new)) {
    $taken = row('SELECT id FROM users WHERE email = ? AND id <> ?', [$new, (int)$u['id']]);
    if ($taken) {
        page_start('Change your sign-in address');
        echo '<div class="sheet"><h1>That address is now in use</h1><p class="lede">Another account was created with ' . e($new) . ' after you asked for this change, so it cannot be moved. Your sign-in address is unchanged.</p><p><a class="btn btn-primary" href="/account/">Back to your account</a></p></div>';
        page_end();
        exit;
    }
    $old = (string)$u['email'];
    q('UPDATE users SET email = ?, verified_at = ? WHERE id = ?', [$new, now(), (int)$u['id']]);
    audit('email-changed', $old . ' -> ' . $new);
    /* Tell the old address too. If the change was not asked for, that is how it gets noticed. */
    send_mail($old, 'Your Specline sign-in address has changed',
        "The sign-in address on your Specline account has been changed from {$old} to {$new}.\n\n"
      . "If you did not do this, reply to this message straight away.\n");
    if (!current_user()) login_user(row('SELECT * FROM users WHERE id = ?', [(int)$u['id']]));
    flash('Your sign-in address is now ' . $new . '. Use it next time you sign in.');
    redirect('/account/');
}

page_start('Change your sign-in address');
?>
<div class="sheet">
  <h1>That link has expired</h1>
  <p class="lede">Confirmation links work for one hour and once only. Your sign-in address has not changed. Ask for a new one from your account page.</p>
  <p><a class="btn btn-primary" href="/account/">Back to your account</a></p>
</div>
<?php page_end();
