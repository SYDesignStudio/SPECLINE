<?php
require __DIR__ . '/../app/bootstrap.php';
$me = require_admin();

/* The CSV above public_html is still the record of truth for the waiting list; this page
   reads it in so the two views agree, and never writes back to it. */
$imported = 0;
if (is_readable(WAITLIST_CSV) && ($fh = fopen(WAITLIST_CSV, 'r')) !== false) {
    fgetcsv($fh);
    while (($r = fgetcsv($fh)) !== false) {
        if (count($r) < 2 || !filter_var($r[1] ?? '', FILTER_VALIDATE_EMAIL)) continue;
        $email = mb_strtolower($r[1]);
        if (row('SELECT id FROM waitlist WHERE at = ? AND email = ?', [$r[0], $email])) continue;
        try { q('INSERT INTO waitlist (at, email, name, practice, ip) VALUES (?, ?, ?, ?, ?)', [$r[0], $email, $r[2] ?? '', $r[3] ?? '', $r[5] ?? '']); $imported++; } catch (Throwable $t) {}
    }
    fclose($fh);
}
if (($_GET['export'] ?? '') === 'csv') {
    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename="specline-waitlist-' . gmdate('Y-m-d') . '.csv"');
    $out = fopen('php://output', 'w');
    fputcsv($out, ['at_utc', 'email', 'name', 'practice', 'has_account']);
    foreach (rows('SELECT * FROM waitlist ORDER BY at') as $r)
        fputcsv($out, [$r['at'], $r['email'], $r['name'], $r['practice'], val('SELECT COUNT(*) FROM users WHERE email = ?', [$r['email']]) ? 'yes' : 'no']);
    exit;
}
$list = rows('SELECT * FROM waitlist ORDER BY at DESC LIMIT 500');
$total = (int)val('SELECT COUNT(DISTINCT email) FROM waitlist');
$converted = (int)val('SELECT COUNT(DISTINCT w.email) FROM waitlist w JOIN users u ON u.email = w.email');
$fileState = is_readable(WAITLIST_CSV) ? 'read from ' . WAITLIST_CSV : 'no CSV found at ' . WAITLIST_CSV . ' — the list is empty until someone signs up';

page_start('Waiting list', ['admin' => true]);
?>
<header>
  <div><h1>Waiting list</h1><p>People who asked to be told when Specline opens, from the form on the home page. The list itself lives in a CSV above the web root, so a deployment never touches it; this page mirrors it.</p></div>
  <div class="headact"><a class="btn btn-sm" href="/admin/waitlist.php?export=csv">Export CSV</a></div>
</header>
<div class="figures">
  <div class="figure"><b><?= $total ?></b><small>On the list</small><span class="sub">distinct addresses</span></div>
  <div class="figure"><b><?= $converted ?></b><small>Since signed up</small><span class="sub"><?= $total ? round($converted / $total * 100) : 0 ?>% of the list</span></div>
  <div class="figure"><b><?= $imported ?></b><small>New this visit</small><span class="sub">picked up from the CSV</span></div>
</div>
<p class="small muted" style="margin-bottom:22px"><?= e($fileState) ?></p>
<?php if (!$list): ?>
  <p class="empty">Nobody on the list yet. The form on the home page writes here.</p>
<?php else: ?>
<div class="scroll"><table class="ledger">
  <tr><th>When</th><th>Email</th><th>Name</th><th>Practice</th><th>Account</th><th></th></tr>
  <?php foreach ($list as $r): $has = (int)val('SELECT COUNT(*) FROM users WHERE email = ?', [$r['email']]); ?>
  <tr><td class="when"><?= e(gmdate('j M Y', strtotime($r['at']))) ?></td>
    <td class="mono small"><a href="mailto:<?= e($r['email']) ?>"><?= e($r['email']) ?></a></td>
    <td><?= e($r['name'] ?: '—') ?></td><td><?= e($r['practice'] ?: '—') ?></td>
    <td><?= $has ? '<span class="pill pill-pass">Signed up</span>' : '<span class="pill">Waiting</span>' ?></td>
    <td><a href="mailto:<?= e($r['email']) ?>?subject=Specline%20is%20opening">Invite</a></td></tr>
  <?php endforeach; ?>
</table></div>
<?php endif; ?>
<?php page_end(['admin' => true]);
