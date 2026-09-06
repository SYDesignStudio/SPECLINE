<?php
require __DIR__ . '/app/bootstrap.php';
$u = current_user();
$errors = []; $sent = false;
if (is_post()) {
    csrf_check();
    if (trim((string)($_POST['website'] ?? '')) !== '') { $sent = true; }   // honeypot: pretend
    else {
        $name = clean('name', 120); $email = mb_strtolower(clean('email', 254)); $practice = clean('practice', 150);
        $subject = clean('subject', 200); $body = clean('body', 5000);
        if ($name === '') $errors[] = 'Enter your name.';
        if (!valid_email($email)) $errors[] = 'That email address does not look right.';
        if (mb_strlen($body) < 10) $errors[] = 'Write a little more so we can help.';
        if (!$errors && !throttle('contact:' . client_ip(), 5, 3600)) $errors[] = 'Several messages have been sent from this connection in the last hour. Try again later, or email info@specline.co.uk.';
        if (!$errors) {
            q('INSERT INTO messages (at, name, email, practice, subject, body, ip, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
              [now(), $name, $email, $practice, $subject, $body, client_ip(), $u ? (int)$u['id'] : null]);
            notify_studio('Specline message: ' . ($subject !== '' ? $subject : 'from ' . $name),
                "From:     {$name} <{$email}>\nPractice: " . ($practice ?: '—') . "\nWhen:     " . now() . "\n\n{$body}\n\n" . cfg('base_url') . "/admin/messages.php\n", $email);
            $sent = true;
        }
    }
}
page_start('Contact');
?>
<div class="sheet">
  <h1>Contact Specline</h1>
  <?php if ($sent): ?>
    <p class="lede">Thank you. Your message is with the studio and we reply by email, usually within a working day.</p>
    <p><a href="/">Back to the home page</a></p>
  <?php else: ?>
    <p class="lede">Questions about the product, the library, the pricing, or a clause you think is wrong. That last one is the message we most want.</p>
    <?php if ($errors): ?><ul class="errs"><?php foreach ($errors as $x) echo '<li>' . e($x) . '</li>'; ?></ul><?php endif; ?>
    <form class="stack" method="post" action="/contact.php" novalidate>
      <?= csrf_field() ?>
      <div class="row2">
        <?= field('name', 'Your name', 'text', ['required' => true, 'autocomplete' => 'name', 'value' => $u['name'] ?? '']) ?>
        <?= field('email', 'Email', 'email', ['required' => true, 'autocomplete' => 'email', 'value' => $u['email'] ?? '']) ?>
      </div>
      <?= field('practice', 'Practice', 'text', ['autocomplete' => 'organization', 'value' => $u['practice_name'] ?? '']) ?>
      <?= field('subject', 'Subject', 'text', ['maxlength' => 200]) ?>
      <?= field('body', 'Message', 'textarea', ['required' => true, 'maxlength' => 5000]) ?>
      <div style="position:absolute;left:-9999px" aria-hidden="true"><label>Website<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
      <div class="actions"><button class="btn btn-primary" type="submit">Send message</button><span class="small muted">Or email <a href="mailto:info@specline.co.uk">info@specline.co.uk</a></span></div>
    </form>
  <?php endif; ?>
</div>
<?php page_end();
