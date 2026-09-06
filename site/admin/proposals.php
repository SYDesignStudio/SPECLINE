<?php
require __DIR__ . '/../app/bootstrap.php';
require __DIR__ . '/../app/regwatch.php';
require __DIR__ . '/../app/proposals.php';
$me = require_admin();

if (is_post()) {
    csrf_check();
    $a = (string)($_POST['action'] ?? '');
    if ($a === 'draft' && ($d = row('SELECT * FROM regdocs WHERE id = ?', [(int)($_POST['id'] ?? 0)]))) {
        $ev = row('SELECT id FROM regevents WHERE doc_id = ? ORDER BY at DESC LIMIT 1', [(int)$d['id']]);
        $t = draft_proposals($d, $ev ? (int)$ev['id'] : null);
        flash('Approved Document ' . $d['code'] . ': ' . $t['edition'] . ' edit' . ($t['edition'] === 1 ? '' : 's') . ' drafted, ' . $t['review'] . ' clause' . ($t['review'] === 1 ? '' : 's') . ' listed for reading'
            . ($t['skipped'] ? ', ' . $t['skipped'] . ' skipped because the same wording appears more than once in the file' : '') . '.',
            $t['edition'] ? 'ok' : 'hold');
    } elseif (in_array($a, ['approve', 'reject'], true) && ($p = row('SELECT * FROM proposals WHERE id = ?', [(int)($_POST['id'] ?? 0)]))) {
        if ($a === 'approve' && $p['kind'] !== 'edition') flash('Only a drafted edit can be approved. A clause listed for reading has no proposed wording to accept.', 'err');
        else {
            q('UPDATE proposals SET status = ?, decided_at = ?, decided_by = ?, note = ? WHERE id = ?',
              [$a === 'approve' ? 'approved' : 'rejected', now(), $me['name'], clean('note', 500), (int)$p['id']]);
            audit('proposal-' . $a, '#' . $p['id'] . ' ' . $p['clause_title']);
        }
    } elseif ($a === 'read' && ($p = row('SELECT * FROM proposals WHERE id = ?', [(int)($_POST['id'] ?? 0)]))) {
        q("UPDATE proposals SET status = 'read', decided_at = ?, decided_by = ?, note = ? WHERE id = ?", [now(), $me['name'], clean('note', 500), (int)$p['id']]);
        audit('proposal-read', '#' . $p['id']);
    } elseif ($a === 'clear') {
        q("DELETE FROM proposals WHERE status IN ('draft','read','rejected')");
        flash('Cleared everything not approved.');
    }
    redirect('/admin/proposals.php');
}

if (($_GET['export'] ?? '') === 'py') {
    $rows = rows("SELECT * FROM proposals WHERE status = 'approved' AND kind = 'edition' ORDER BY file_rel, id");
    if (!$rows) { flash('Nothing is approved yet, so there is nothing to export.', 'hold'); redirect('/admin/proposals.php'); }
    header('Content-Type: text/x-python; charset=utf-8');
    header('Content-Disposition: attachment; filename="specline-approved-edits-' . gmdate('Y-m-d') . '.py"');
    echo export_script($rows);
    audit('proposals-exported', count($rows) . ' edits');
    exit;
}

$docs = rows("SELECT * FROM regdocs ORDER BY CASE status WHEN 'changed' THEN 0 ELSE 1 END, id");
$edits   = rows("SELECT p.*, d.code FROM proposals p JOIN regdocs d ON d.id = p.doc_id WHERE p.kind = 'edition' AND p.status = 'draft' ORDER BY p.file_rel, p.id");
$reads   = rows("SELECT p.*, d.code FROM proposals p JOIN regdocs d ON d.id = p.doc_id WHERE p.kind = 'review' AND p.status = 'draft' ORDER BY p.type_name, p.id");
$decided = rows("SELECT p.*, d.code FROM proposals p JOIN regdocs d ON d.id = p.doc_id WHERE p.status <> 'draft' ORDER BY p.decided_at DESC LIMIT 40");
$approved = (int)val("SELECT COUNT(*) FROM proposals WHERE status = 'approved'");

page_start('Proposed edits', ['admin' => true]);
?>
<header>
  <div><h1>Proposed edits</h1>
    <p>Drafts the library changes that follow from a document moving, for you to accept or refuse. It drafts only what it can ground in something it has actually read, which today means the edition a clause names. It never drafts a figure, and approving here does not change the library: it produces a script to run in the working copy, so the build and the tests still get their say.</p></div>
  <div class="headact">
    <?php if ($approved): ?><a class="btn btn-primary btn-sm" href="/admin/proposals.php?export=py">Export <?= $approved ?> approved edit<?= $approved === 1 ? '' : 's' ?></a><?php endif; ?>
  </div>
</header>
<?php show_flash(); ?>

<section>
  <h2>Draft from a document</h2>
  <div class="inline" style="gap:12px;flex-wrap:wrap">
    <?php foreach ($docs as $d): $pub = published_edition($d); ?>
      <form method="post" class="inline" style="gap:6px">
        <?= csrf_field() ?><input type="hidden" name="action" value="draft"><input type="hidden" name="id" value="<?= (int)$d['id'] ?>">
        <button class="btn btn-sm<?= $d['status'] === 'changed' ? ' btn-primary' : '' ?>" type="submit" title="<?= e($d['title']) ?><?= $pub ? ' — gov.uk publishes a ' . $pub['year'] . ' edition' : '' ?>">
          AD <?= e($d['code']) ?><?= $pub ? ' · ' . $pub['year'] : '' ?></button>
      </form>
    <?php endforeach; ?>
  </div>
  <p class="small muted" style="margin-top:12px;max-width:78ch">The year beside a document is the newest edition gov.uk attaches to its publication page. <strong>Published is not in force.</strong> The 2026 editions of L1 and F1 were published on 24 March 2026 and do not apply until 24 March 2027, so confirm the commencement date before approving an edition change.</p>
</section>

<?php if ($edits): ?>
<section>
  <h2>Drafted edits — <?= count($edits) ?> awaiting your decision</h2>
  <?php foreach ($edits as $p): $frag = diff_fragment($p['find_text'], $p['replace_text']); ?>
    <div class="prop">
      <header>
        <span><strong><?= e($p['type_name']) ?></strong> · <?= e($p['clause_title']) ?></span>
        <span class="when"><code><?= e($p['file_rel']) ?></code> · AD <?= e($p['code']) ?></span>
      </header>
      <div class="change">
        <p class="was"><span class="tag">Now</span> <?= e($frag['a']['pre']) ?><mark class="cut"><?= e($frag['a']['mid']) ?></mark><?= e($frag['a']['post']) ?></p>
        <p class="now"><span class="tag">Proposed</span> <?= e($frag['b']['pre']) ?><mark class="add"><?= e($frag['b']['mid']) ?></mark><?= e($frag['b']['post']) ?></p>
        <p class="small muted">The only difference is <code><?= e($frag['from']) ?></code> becoming <code><?= e($frag['to']) ?></code>. Everything else in the clause is untouched.</p>
      </div>
      <p class="small muted"><?= e($p['evidence']) ?></p>
      <?php $figs = json_decode((string)$p['figures'], true) ?: []; if ($figs): ?>
        <p class="small"><span class="tag">Figures in this clause, unchanged by this edit</span> <?= e(implode(' · ', $figs)) ?></p>
      <?php endif; ?>
      <div class="inline">
        <form method="post" class="inline"><?= csrf_field() ?><input type="hidden" name="id" value="<?= (int)$p['id'] ?>">
          <input type="text" name="note" placeholder="note, e.g. confirmed in force from 24 March 2027" maxlength="500" style="min-width:min(380px,55vw)" aria-label="Note">
          <button class="btn btn-sm btn-primary" type="submit" name="action" value="approve">Approve</button>
          <button class="btn btn-sm" type="submit" name="action" value="reject">Refuse</button>
        </form>
      </div>
    </div>
  <?php endforeach; ?>
</section>
<?php endif; ?>

<?php if ($reads): ?>
<section>
  <h2>Clauses to read — <?= count($reads) ?></h2>
  <p class="small muted" style="max-width:78ch;margin-bottom:14px">No wording is proposed for these. Each states figures the document governs, and a figure can only be changed by reading the amendment. The figures are pulled out so you know what to check; mark one read when you have.</p>
  <div class="scroll"><table class="ledger">
    <tr><th>Project type</th><th>Clause</th><th>AD</th><th>Figures it states</th><th></th></tr>
    <?php foreach ($reads as $p): $figs = json_decode((string)$p['figures'], true) ?: []; ?>
      <tr>
        <td><?= e($p['type_name']) ?></td>
        <td><?= e($p['clause_title']) ?></td>
        <td class="mono"><?= e($p['code']) ?></td>
        <td class="small muted"><?= e(implode(' · ', array_slice($figs, 0, 6))) ?></td>
        <td><form method="post"><?= csrf_field() ?><input type="hidden" name="action" value="read"><input type="hidden" name="id" value="<?= (int)$p['id'] ?>"><button class="btn btn-sm" type="submit">Mark read</button></form></td>
      </tr>
    <?php endforeach; ?>
  </table></div>
</section>
<?php endif; ?>

<?php if (!$edits && !$reads): ?>
  <p class="empty">Nothing drafted. Pick a document above — the ones highlighted have changed since they were last reviewed.</p>
<?php endif; ?>

<?php if ($approved): ?>
<section>
  <h2>Applying what you approve</h2>
  <p class="small muted" style="max-width:78ch">Approving does not change the library. This server holds a deployed copy of <code>data/</code> and the next push overwrites it, so an edit written here would vanish without ever reaching git, the structural check or the 185 assertions. The export is a Python script for the working copy instead, with every replacement asserted, so a clause that has moved on since the proposal was drafted stops the script rather than being silently missed.</p>
  <p class="keyblock">python specline-approved-edits-<?= gmdate('Y-m-d') ?>.py<br>python build.py --test<br>git add -A &amp;&amp; git commit</p>
  <p><a class="btn btn-primary btn-sm" href="/admin/proposals.php?export=py">Export <?= $approved ?> approved edit<?= $approved === 1 ? '' : 's' ?></a></p>
</section>
<?php endif; ?>

<?php if ($decided): ?>
<section>
  <h2>Decided</h2>
  <div class="scroll"><table class="ledger">
    <tr><th>When</th><th>By</th><th>Outcome</th><th>Project type</th><th>Clause</th><th>Note</th></tr>
    <?php foreach ($decided as $p): ?>
      <tr><td class="when"><?= e(ago($p['decided_at'])) ?></td><td class="small"><?= e($p['decided_by']) ?></td>
        <td><span class="pill <?= ['approved' => 'pill-pass', 'rejected' => 'pill-fail', 'read' => ''][$p['status']] ?? '' ?>"><?= e($p['status']) ?></span></td>
        <td class="small"><?= e($p['type_name']) ?></td><td class="small"><?= e($p['clause_title']) ?></td><td class="small muted"><?= e($p['note']) ?></td></tr>
    <?php endforeach; ?>
  </table></div>
  <form method="post" style="margin-top:12px"><?= csrf_field() ?><input type="hidden" name="action" value="clear"><button class="btn btn-sm" type="submit">Clear everything not approved</button></form>
</section>
<?php endif; ?>

<section>
  <h2>What this will not do</h2>
  <p class="small muted" style="max-width:78ch">It will not draft a figure. A U-value, a fire period, a ventilation rate or a percentage can only be changed by reading the amendment, and this module cannot read the amendment: the Approved Documents are PDFs whose text sits behind subsetted font encodings that PHP on shared hosting has no reliable way through. Inferring a figure from a filename or a change note would be inventing it, which is the one thing this repository forbids outright, and the invented number would travel into a document going to building control. So it drafts the mechanical edit, quotes its evidence, lists the clauses a person has to read, and stops.</p>
</section>
<?php page_end(['admin' => true]);
