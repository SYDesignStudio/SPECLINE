<?php
require __DIR__ . '/../app/bootstrap.php';
$me = require_admin();

if (is_post()) {
    csrf_check();
    $id = (int)($_POST['id'] ?? 0);
    $action = (string)($_POST['action'] ?? '');
    if ($id && in_array($action, ['read', 'replied', 'closed', 'new'], true)) {
        q('UPDATE messages SET status = ? WHERE id = ?', [$action, $id]);
        audit('message-' . $action, '#' . $id);
    }
    if ($id && $action === 'note') q('UPDATE messages SET note = ? WHERE id = ?', [clean('note', 1000), $id]);
    redirect('/admin/messages.php?show=' . e((string)($_POST['show'] ?? 'open')) . '#m' . $id);
}
$show = in_array($_GET['show'] ?? 'open', ['open', 'all'], true) ? $_GET['show'] : 'open';
$list = $show === 'all'
    ? rows('SELECT * FROM messages ORDER BY at DESC LIMIT 300')
    : rows("SELECT * FROM messages WHERE status IN ('new','read') ORDER BY at DESC LIMIT 300");
$counts = ['new' => (int)val("SELECT COUNT(*) FROM messages WHERE status = 'new'"), 'all' => (int)val('SELECT COUNT(*) FROM messages')];

page_start('Messages', ['admin' => true]);
?>
<header>
  <div><h1>Messages</h1><p>Sent through the contact form on the site. Each one is emailed to Specline as well, with the sender on Reply-To, so replying by email reaches the person. This page is the record and the state.</p></div>
  <div class="headact">
    <a class="btn btn-sm<?= $show === 'open' ? ' btn-primary' : '' ?>" href="/admin/messages.php?show=open">Open (<?= $counts['new'] ?> new)</a>
    <a class="btn btn-sm<?= $show === 'all' ? ' btn-primary' : '' ?>" href="/admin/messages.php?show=all">All (<?= $counts['all'] ?>)</a>
  </div>
</header>
<?php show_flash(); ?>
<p class="small muted" style="margin-bottom:20px">This shows messages people send through the contact form, and emails a copy to <span class="mono">info@specline.co.uk</span> with the sender on Reply-To. It is not an inbox: mail sent straight to that address is read in the mailbox, not here.</p>
<?php if (!$list): ?>
  <p class="empty"><?= $show === 'open' ? 'Nothing open. Every message has been dealt with.' : 'No messages yet. The contact form writes here.' ?></p>
<?php else: foreach ($list as $m): ?>
  <div class="msg<?= $m['status'] === 'new' ? ' new' : '' ?>" id="m<?= (int)$m['id'] ?>">
    <header>
      <span><strong><?= e($m['name']) ?></strong> <a class="mono small" href="mailto:<?= e($m['email']) ?>"><?= e($m['email']) ?></a><?= $m['practice'] ? ' · ' . e($m['practice']) : '' ?>
        <?php if ($m['user_id']) echo ' <span class="pill pill-petrol">Has an account</span>'; ?>
        <span class="pill <?= ['new' => 'pill-hold', 'read' => '', 'replied' => 'pill-pass', 'closed' => ''][$m['status']] ?? '' ?>"><?= e($m['status']) ?></span></span>
      <span class="when"><?= e(fmt_when($m['at'])) ?></span>
    </header>
    <?php if ($m['subject']) echo '<strong>' . e($m['subject']) . '</strong>'; ?>
    <div class="body"><?= e($m['body']) ?></div>
    <?php if ($m['note']) echo '<p class="small muted">Note: ' . e($m['note']) . '</p>'; ?>
    <div class="inline">
      <a class="btn btn-sm btn-primary" href="mailto:<?= e($m['email']) ?>?subject=<?= rawurlencode('Re: ' . ($m['subject'] ?: 'your message to Specline')) ?>">Reply by email</a>
      <?php foreach ([['read', 'Mark read'], ['replied', 'Mark replied'], ['closed', 'Close'], ['new', 'Reopen']] as [$a, $label]): if ($m['status'] === $a) continue; ?>
        <form method="post" style="display:inline"><?= csrf_field() ?><input type="hidden" name="id" value="<?= (int)$m['id'] ?>"><input type="hidden" name="show" value="<?= e($show) ?>"><input type="hidden" name="action" value="<?= $a ?>"><button class="btn btn-sm" type="submit"><?= e($label) ?></button></form>
      <?php endforeach; ?>
      <form method="post" class="inline"><?= csrf_field() ?><input type="hidden" name="id" value="<?= (int)$m['id'] ?>"><input type="hidden" name="show" value="<?= e($show) ?>"><input type="hidden" name="action" value="note">
        <input type="text" name="note" value="<?= e($m['note']) ?>" placeholder="internal note" maxlength="1000" aria-label="Internal note"><button class="btn btn-sm" type="submit">Save note</button></form>
    </div>
  </div>
<?php endforeach; endif; ?>
<?php page_end(['admin' => true]);
