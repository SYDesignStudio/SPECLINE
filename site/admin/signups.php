<?php
require __DIR__ . '/../app/bootstrap.php';
$me = require_admin();

if (is_post()) {
    csrf_check();
    $id = (int)($_POST['id'] ?? 0);
    if (($_POST['action'] ?? '') === 'verify' && $id) { q('UPDATE users SET verified_at = COALESCE(verified_at, ?) WHERE id = ?', [now(), $id]); audit('admin-verified', (string)val('SELECT email FROM users WHERE id = ?', [$id])); flash('Marked as verified.'); }
    redirect('/admin/signups.php');
}
if (($_GET['export'] ?? '') === 'csv') {
    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename="specline-signups-' . gmdate('Y-m-d') . '.csv"');
    $out = fopen('php://output', 'w');
    fputcsv($out, ['created_utc', 'practice', 'name', 'email', 'plan', 'seats', 'verified_utc', 'last_login_utc', 'logins']);
    foreach (rows('SELECT u.*, p.name AS practice, p.plan, p.seats FROM users u JOIN practices p ON p.id = u.practice_id ORDER BY u.created_at') as $r)
        fputcsv($out, [$r['created_at'], $r['practice'], $r['name'], $r['email'], $r['plan'], $r['seats'], $r['verified_at'], $r['last_login_at'], $r['login_count']]);
    exit;
}
$qs = trim((string)($_GET['q'] ?? ''));
$where = ''; $args = [];
if ($qs !== '') { $where = 'WHERE u.email LIKE ? OR u.name LIKE ? OR p.name LIKE ?'; $like = '%' . $qs . '%'; $args = [$like, $like, $like]; }
$list = rows("SELECT u.*, p.name AS practice, p.plan, p.seats FROM users u JOIN practices p ON p.id = u.practice_id $where ORDER BY u.created_at DESC LIMIT 400", $args);
$total = (int)val('SELECT COUNT(*) FROM users');

page_start('Sign-ups', ['admin' => true]);
?>
<header>
  <div><h1>Sign-ups</h1><p><span class="mono"><?= $total ?></span> account<?= $total === 1 ? '' : 's' ?>, newest first. An account is a practice and its first user; seats and plan are what they told us, not what they have paid for.</p></div>
  <div class="headact">
    <form method="get" action="/admin/signups.php" class="inline"><input type="search" name="q" value="<?= e($qs) ?>" placeholder="email, name or practice" aria-label="Search sign-ups"><button class="btn btn-sm" type="submit">Search</button></form>
    <a class="btn btn-sm" href="/admin/signups.php?export=csv">Export CSV</a>
  </div>
</header>
<?php show_flash(); ?>
<?php if (!$list): ?>
  <p class="empty"><?= $qs !== '' ? 'Nothing matches that search.' : 'No accounts yet. Sign-ups from the site appear here as soon as they are made.' ?></p>
<?php else: ?>
<div class="scroll"><table class="ledger">
  <tr><th>Created</th><th>Practice</th><th>Name</th><th>Email</th><th>Plan</th><th class="r">Seats</th><th>Email verified</th><th>Last seen</th><th class="r">Logins</th><th></th></tr>
  <?php foreach ($list as $r): ?>
  <tr>
    <td class="when"><?= e(gmdate('j M Y', strtotime($r['created_at']))) ?></td>
    <td><?= e($r['practice']) ?></td>
    <td><?= e($r['name']) ?><?= $r['role'] === 'owner' ? ' <span class="pill pill-petrol">Admin</span>' : '' ?></td>
    <td class="mono small"><a href="mailto:<?= e($r['email']) ?>"><?= e($r['email']) ?></a></td>
    <td><?= e($r['plan']) ?></td>
    <td class="num"><?= (int)$r['seats'] ?></td>
    <td><?php if ($r['verified_at']) echo '<span class="pill pill-pass">' . e(gmdate('j M', strtotime($r['verified_at']))) . '</span>';
        else { ?><form method="post" style="display:inline"><?= csrf_field() ?><input type="hidden" name="action" value="verify"><input type="hidden" name="id" value="<?= (int)$r['id'] ?>"><button class="btn btn-sm" type="submit">Mark verified</button></form><?php } ?></td>
    <td class="when"><?= e(ago($r['last_login_at'])) ?></td>
    <td class="num"><?= (int)$r['login_count'] ?></td>
    <td><a href="mailto:<?= e($r['email']) ?>?subject=Specline">Email</a></td>
  </tr>
  <?php endforeach; ?>
</table></div>
<?php endif; ?>
<?php page_end(['admin' => true]);
