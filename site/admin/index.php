<?php
require __DIR__ . '/../app/bootstrap.php';
require __DIR__ . '/../app/regwatch.php';
$me = require_admin();
regwatch_seed();

/* Pull the waiting list CSV into the database once, so the dashboard shows the whole history. */
if (is_readable(WAITLIST_CSV) && (int)val('SELECT COUNT(*) FROM waitlist') === 0) {
    if (($fh = fopen(WAITLIST_CSV, 'r')) !== false) {
        fgetcsv($fh);
        while (($r = fgetcsv($fh)) !== false) {
            if (count($r) < 2 || !filter_var($r[1], FILTER_VALIDATE_EMAIL)) continue;
            try { q('INSERT INTO waitlist (at, email, name, practice, ip) VALUES (?, ?, ?, ?, ?)', [$r[0], mb_strtolower($r[1]), $r[2] ?? '', $r[3] ?? '', $r[5] ?? '']); } catch (Throwable $t) {}
        }
        fclose($fh);
    }
}
/* A daily check happens when the dashboard is opened, so it runs even before a cron job is set up. */
$ran = null;
if (regwatch_due() && throttle('regwatch-inline', 1, 3600)) { set_time_limit(150); $ran = regwatch_run('dashboard'); }

$n = fn(string $sql, array $a = []) => (int)val($sql, $a);
$week = gmdate('c', time() - 7 * 86400);
$f = [
  'accounts'   => $n('SELECT COUNT(*) FROM users'),
  'accounts_w' => $n('SELECT COUNT(*) FROM users WHERE created_at >= ?', [$week]),
  'verified'   => $n('SELECT COUNT(*) FROM users WHERE verified_at IS NOT NULL'),
  'waitlist'   => $n('SELECT COUNT(DISTINCT email) FROM waitlist'),
  'messages'   => $n("SELECT COUNT(*) FROM messages WHERE status = 'new'"),
  'seats'      => $n('SELECT COALESCE(SUM(seats),0) FROM practices'),
  'changed'    => $n("SELECT COUNT(*) FROM regdocs WHERE status = 'changed'"),
  'errors'     => $n("SELECT COUNT(*) FROM regdocs WHERE status = 'error'"),
];
$plans = rows('SELECT plan, COUNT(*) AS c FROM practices GROUP BY plan ORDER BY c DESC');
$recent = rows('SELECT u.*, p.name AS practice, p.plan FROM users u JOIN practices p ON p.id = u.practice_id ORDER BY u.created_at DESC LIMIT 8');
$msgs = rows("SELECT * FROM messages WHERE status = 'new' ORDER BY at DESC LIMIT 5");
$lastRun = setting('regwatch_last_run');
$changedDocs = rows("SELECT * FROM regdocs WHERE status IN ('changed','error') ORDER BY status, code");

page_start('Overview', ['admin' => true]);
?>
<header>
  <div><h1>Overview</h1><p><?= e(gmdate('l j F Y')) ?>. What has come in, and whether anything in the Approved Documents has moved.</p></div>
</header>
<?php if ($ran) echo '<p class="notice notice-ok">Regulations check ran just now: ' . (int)$ran['changed'] . ' changed, ' . (int)$ran['same'] . ' unchanged, ' . (int)$ran['baseline'] . ' baselined, ' . (int)$ran['error'] . ' could not be read.</p><br>'; ?>

<div class="figures">
  <div class="figure"><b><?= $f['accounts'] ?></b><small>Accounts</small><span class="sub"><?= $f['accounts_w'] ?> this week · <?= $f['verified'] ?> verified</span></div>
  <div class="figure"><b><?= $f['seats'] ?></b><small>Seats expected</small><span class="sub"><?= e(implode(' · ', array_map(fn($p) => $p['plan'] . ' ' . (int)$p['c'], $plans))) ?></span></div>
  <div class="figure"><b><?= $f['waitlist'] ?></b><small>Waiting list</small><span class="sub">distinct addresses</span></div>
  <div class="figure"><b><?= $f['messages'] ?></b><small>Unread messages</small><span class="sub"><a href="/admin/messages.php">open</a></span></div>
  <div class="figure"><b><?= $f['changed'] ?></b><small>Documents changed</small><span class="sub"><?= $lastRun ? 'checked ' . e(ago($lastRun)) : 'never checked' ?><?= $f['errors'] ? ' · ' . $f['errors'] . ' unreadable' : '' ?></span></div>
</div>

<?php if ($changedDocs): ?>
<section>
  <h2>Needs a decision</h2>
  <?php foreach ($changedDocs as $d): ?>
    <div class="event<?= $d['status'] === 'error' ? '' : '' ?>">
      <div><strong>Approved Document <?= e($d['code']) ?></strong> — <?= $d['status'] === 'error' ? e($d['error']) : 'changed on gov.uk ' . e(ago($d['last_changed'])) . '. Nothing in the library has been altered.' ?></div>
      <div><a href="/admin/regs.php#doc-<?= e($d['code']) ?>">Review the clauses that cite it</a></div>
    </div>
  <?php endforeach; ?>
</section>
<?php endif; ?>

<section>
  <h2>Latest sign-ups</h2>
  <?php if (!$recent): ?><p class="empty">No accounts yet. The first sign-up appears here with its practice, plan and verification state.</p>
  <?php else: ?><div class="scroll"><table class="ledger">
    <tr><th>When</th><th>Practice</th><th>Name</th><th>Email</th><th>Plan</th><th>Verified</th><th class="r">Logins</th></tr>
    <?php foreach ($recent as $r): ?>
      <tr><td class="when"><?= e(ago($r['created_at'])) ?></td><td><?= e($r['practice']) ?></td><td><?= e($r['name']) ?></td><td class="mono small"><?= e($r['email']) ?></td><td><?= e($r['plan']) ?></td>
      <td><?= $r['verified_at'] ? '<span class="pill pill-pass">Verified</span>' : '<span class="pill pill-hold">Unverified</span>' ?></td><td class="num"><?= (int)$r['login_count'] ?></td></tr>
    <?php endforeach; ?>
  </table></div><p class="small" style="margin-top:10px"><a href="/admin/signups.php">All sign-ups</a></p><?php endif; ?>
</section>

<section>
  <h2>Unread messages</h2>
  <?php if (!$msgs): ?><p class="empty">Nothing waiting. Messages sent through the contact form land here and by email.</p>
  <?php else: foreach ($msgs as $m): ?>
    <div class="msg new"><header><span><strong><?= e($m['name']) ?></strong> <span class="mono small"><?= e($m['email']) ?></span><?= $m['practice'] ? ' · ' . e($m['practice']) : '' ?></span><span class="when"><?= e(ago($m['at'])) ?></span></header>
    <?php if ($m['subject']) echo '<strong>' . e($m['subject']) . '</strong>'; ?><div class="body"><?= e(mb_substr($m['body'], 0, 400)) ?><?= mb_strlen($m['body']) > 400 ? '…' : '' ?></div>
    <div><a href="/admin/messages.php#m<?= (int)$m['id'] ?>">Open</a></div></div>
  <?php endforeach; endif; ?>
</section>
<?php page_end(['admin' => true]);
