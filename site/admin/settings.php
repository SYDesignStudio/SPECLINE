<?php
require __DIR__ . '/../app/bootstrap.php';
$me = require_admin();

if (is_post()) {
    csrf_check();
    $a = (string)($_POST['action'] ?? '');
    if ($a === 'general') {
        $url = clean('app_url', 400);
        if ($url !== '' && !preg_match('#^https://#', $url)) flash('The application address has to start with https://', 'err');
        else { set_setting('app_url', $url); set_setting('opening_note', clean('opening_note', 400)); flash('Saved. Verified account holders will see the link on their account page.'); }
    } elseif ($a === 'cron') {
        set_setting('cron_token', bin2hex(random_bytes(24)));
        flash('A new cron key has been generated. Update the scheduled task with the new address.');
    } elseif ($a === 'cron-off') { set_setting('cron_token', ''); flash('Cron key cleared. The scheduled address will stop working.'); }
    audit('settings', $a);
    redirect('/admin/settings.php');
}
$token = setting('cron_token', '');
$cronUrl = $token ? cfg('base_url') . '/cron.php?k=' . $token : '';
$counts = ['users' => (int)val('SELECT COUNT(*) FROM users'), 'practices' => (int)val('SELECT COUNT(*) FROM practices'),
           'messages' => (int)val('SELECT COUNT(*) FROM messages'), 'waitlist' => (int)val('SELECT COUNT(*) FROM waitlist'),
           'events' => (int)val('SELECT COUNT(*) FROM regevents')];
$audit = rows('SELECT * FROM audit ORDER BY at DESC LIMIT 40');

page_start('Settings', ['admin' => true]);
?>
<header><div><h1>Settings</h1><p>Where the data sits, how the daily check is triggered, and what account holders see.</p></div></header>
<?php show_flash(); ?>

<section>
  <h2>What account holders see</h2>
  <form class="stack" method="post" style="max-width:640px"><?= csrf_field() ?><input type="hidden" name="action" value="general">
    <?= field('app_url', 'Address of the application', 'url', ['maxlength' => 400, 'value' => setting('app_url', ''), 'placeholder' => 'https://…']) ?>
    <p class="small muted" style="margin-top:-12px">Leave blank while Specline is closed. Once set, verified account holders get an <em>Open Specline</em> button on their account page.</p>
    <?= field('opening_note', 'What to say while it is closed', 'text', ['maxlength' => 400, 'value' => setting('opening_note', 'Specline opens to founding members first. You will be emailed when your account can open the application.')]) ?>
    <div class="actions"><button class="btn btn-primary" type="submit">Save</button></div>
  </form>
</section>

<section>
  <h2>The daily regulations check</h2>
  <p class="small muted" style="max-width:70ch;margin-bottom:14px">The check also runs by itself when this dashboard is opened and a day has passed, so it works with no cron job at all. A scheduled task is better: it notices a change on a day nobody signs in. In Hostinger's hPanel, add a cron job that runs once a day and fetches the address below.</p>
  <?php if ($cronUrl): ?>
    <p class="keyblock"><?= e($cronUrl) ?></p>
    <p class="small muted" style="margin:10px 0 14px">Keep the key private: anyone with the address can trigger a check. Regenerating it makes the old address stop working.</p>
    <div class="inline">
      <form method="post"><?= csrf_field() ?><input type="hidden" name="action" value="cron"><button class="btn btn-sm" type="submit">Generate a new key</button></form>
      <form method="post"><?= csrf_field() ?><input type="hidden" name="action" value="cron-off"><button class="btn btn-sm btn-danger" type="submit">Turn the address off</button></form>
    </div>
    <p class="small muted" style="margin-top:14px">Command form, for a cron job that runs a command rather than fetching a URL:</p>
    <p class="keyblock">php <?= e(SITE_ROOT) ?>/cron.php</p>
  <?php else: ?>
    <form method="post"><?= csrf_field() ?><input type="hidden" name="action" value="cron"><button class="btn btn-primary btn-sm" type="submit">Generate a cron address</button></form>
  <?php endif; ?>
</section>

<section>
  <h2>Where the data is</h2>
  <dl class="defs" style="max-width:760px">
    <dt>Database</dt><dd class="mono small"><?= e(DB_FILE) ?> <span class="pill <?= file_exists(DB_FILE) || db_driver() === 'mysql' ? 'pill-pass' : 'pill-fail' ?>"><?= e(db_driver()) ?></span></dd>
    <dt>Waiting list</dt><dd class="mono small"><?= e(WAITLIST_CSV) ?></dd>
    <dt>Configuration</dt><dd class="mono small"><?= e(CONFIG_FILE) ?> <?= is_readable(CONFIG_FILE) ? '<span class="pill pill-pass">in use</span>' : '<span class="pill">not present, defaults in use</span>' ?></dd>
    <dt>Notifications to</dt><dd class="mono small"><?= e(cfg('notify_to')) ?></dd>
    <dt>Holding</dt><dd class="small"><?= $counts['users'] ?> users · <?= $counts['practices'] ?> practices · <?= $counts['waitlist'] ?> waiting list · <?= $counts['messages'] ?> messages · <?= $counts['events'] ?> regulation changes</dd>
  </dl>
  <p class="small muted" style="max-width:70ch;margin-top:14px">All of it sits above <code>public_html</code>, where the web server cannot serve it and a deployment cannot overwrite it. That is deliberate: Hostinger redeploys this repository into the web root on every push, so anything kept inside it would be lost.</p>
</section>

<section>
  <h2>Recent activity</h2>
  <?php if (!$audit): ?><p class="empty">Nothing recorded yet.</p><?php else: ?>
  <div class="scroll"><table class="ledger"><tr><th>When</th><th>Who</th><th>What</th><th>Detail</th></tr>
    <?php foreach ($audit as $r): ?><tr><td class="when"><?= e(fmt_when($r['at'])) ?></td><td class="small"><?= e($r['who'] ?: '—') ?></td><td><?= e($r['what']) ?></td><td class="small muted"><?= e(mb_substr($r['detail'], 0, 120)) ?></td></tr><?php endforeach; ?>
  </table></div><?php endif; ?>
</section>

<section>
  <h2>Not built yet</h2>
  <p class="small muted" style="max-width:70ch">There is no billing here and no card is taken anywhere. There is also no separation of one practice's job data from another's, because the specification tool still runs as a single Claude artifact rather than a hosted application. Accounts, this dashboard and the regulations watch are the seams for that; the tool itself moving behind these accounts is the next build.</p>
</section>
<?php page_end(['admin' => true]);
