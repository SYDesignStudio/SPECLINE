<?php
require __DIR__ . '/../app/bootstrap.php';
require __DIR__ . '/../app/regwatch.php';
$me = require_admin();
regwatch_seed();

$ran = null;
if (is_post()) {
    csrf_check();
    $action = (string)($_POST['action'] ?? '');
    if ($action === 'check-all') { set_time_limit(300); $ran = regwatch_run('manual'); flash('Checked ' . array_sum($ran) . ' documents: ' . (int)$ran['changed'] . ' changed, ' . (int)$ran['same'] . ' unchanged, ' . (int)$ran['baseline'] . ' baselined, ' . (int)$ran['error'] . ' could not be read.'); }
    elseif ($action === 'check-one' && ($d = row('SELECT * FROM regdocs WHERE id = ?', [(int)($_POST['id'] ?? 0)]))) { $r = regwatch_check_doc($d); flash('Approved Document ' . $d['code'] . ': ' . ['baseline' => 'baseline recorded', 'same' => 'no change', 'changed' => 'CHANGED — review it below', 'error' => 'could not be read'][$r], $r === 'changed' ? 'hold' : 'ok'); }
    elseif ($action === 'resolve' && ($ev = row('SELECT * FROM regevents WHERE id = ?', [(int)($_POST['ev'] ?? 0)]))) {
        q('UPDATE regevents SET reviewed_at = ?, reviewed_by = ?, outcome = ? WHERE id = ?', [now(), $me['name'], clean('outcome', 1000), (int)$ev['id']]);
        if (!(int)val('SELECT COUNT(*) FROM regevents WHERE doc_id = ? AND reviewed_at IS NULL', [(int)$ev['doc_id']]))
            q("UPDATE regdocs SET status = 'current' WHERE id = ?", [(int)$ev['doc_id']]);
        audit('regs-reviewed', 'event #' . $ev['id']);
        flash('Recorded. The library is unchanged — make any wording change in data/ and commit it.');
    }
    elseif ($action === 'held' && ($d = row('SELECT * FROM regdocs WHERE id = ?', [(int)($_POST['id'] ?? 0)]))) {
        q('UPDATE regdocs SET held = ? WHERE id = ?', [clean('held', 200), (int)$d['id']]);
        flash('Recorded which edition the library is written against.');
    }
    elseif ($action === 'url' && ($d = row('SELECT * FROM regdocs WHERE id = ?', [(int)($_POST['id'] ?? 0)]))) {
        $url = clean('page_url', 400);
        if (preg_match('#^https://www\.gov\.uk/#', $url)) { q('UPDATE regdocs SET page_url = ?, fingerprint = NULL, error = NULL, status = ? WHERE id = ?', [$url, 'unchecked', (int)$d['id']]); flash('Address updated. Check it to take a new baseline.'); }
        else flash('The address has to be a www.gov.uk one.', 'err');
    }
    if (!$ran) redirect('/admin/regs.php');
}

$docs = rows('SELECT * FROM regdocs ORDER BY CASE status WHEN \'changed\' THEN 0 WHEN \'error\' THEN 1 ELSE 2 END, id');
$types = array_keys(library_types());
$lastRun = setting('regwatch_last_run');
$open = rows('SELECT e.*, d.code FROM regevents e JOIN regdocs d ON d.id = e.doc_id WHERE e.reviewed_at IS NULL ORDER BY e.at DESC');
$doneRecent = rows('SELECT e.*, d.code FROM regevents e JOIN regdocs d ON d.id = e.doc_id WHERE e.reviewed_at IS NOT NULL ORDER BY e.reviewed_at DESC LIMIT 6');

page_start('Regulations watch', ['admin' => true]);
?>
<header>
  <div><h1>Regulations watch</h1>
    <p>Watches the gov.uk publication page of every Approved Document once a day and records when one moves. It does not edit the library, and it is not meant to: a change on gov.uk says a document was replaced, not what the clause should now say. What it gives you is the alert and the list of clauses that cite the document, so the review has a checklist and an audit trail.</p></div>
  <div class="headact">
    <form method="post"><?= csrf_field() ?><input type="hidden" name="action" value="check-all"><button class="btn btn-primary btn-sm" type="submit">Check all now</button></form>
  </div>
</header>
<?php show_flash(); ?>
<div class="figures">
  <div class="figure"><b><?= count($docs) ?></b><small>Documents watched</small><span class="sub">every Approved Document in force</span></div>
  <div class="figure"><b><?= count($open) ?></b><small>Awaiting review</small><span class="sub"><?= count($open) ? 'the library is unchanged' : 'nothing outstanding' ?></span></div>
  <div class="figure"><b><?= (int)val("SELECT COUNT(*) FROM regdocs WHERE status = 'error'") ?></b><small>Could not be read</small><span class="sub">address or markup changed</span></div>
  <div class="figure"><b class="small" style="font-size:15px"><?= $lastRun ? e(ago($lastRun)) : 'never' ?></b><small>Last checked</small><span class="sub"><?= e(setting('regwatch_last_trigger', '—')) ?><?= setting('cron_token') ? '' : ' · no cron set up' ?></span></div>
</div>

<?php if ($open): ?>
<section>
  <h2>Changes awaiting review</h2>
  <?php foreach ($open as $ev): $doc = row('SELECT * FROM regdocs WHERE id = ?', [(int)$ev['doc_id']]); $clauses = citing_clauses($doc['cites']); ?>
    <div class="event">
      <div><strong>Approved Document <?= e($ev['code']) ?></strong> · <?= e(fmt_when($ev['at'])) ?></div>
      <div><?= e($ev['summary']) ?></div>
      <div class="who">The library holds: <?= e($doc['held'] ?: 'not recorded') ?>. Nothing has been changed automatically.</div>
      <?php if ($clauses): ?>
        <details><summary>Clauses that cite Approved Document <?= e($ev['code']) ?> (<?= array_sum(array_map('count', $clauses)) ?>)</summary>
          <div class="review"><?php foreach ($clauses as $type => $items): ?>
            <h4><?= e($type) ?></h4><ul><?php foreach ($items as $t) echo '<li>' . e($t) . '</li>'; ?></ul>
          <?php endforeach; ?></div>
        </details>
      <?php endif; ?>
      <div><a href="/admin/proposals.php">Draft the edits that follow from this</a></div>
      <form method="post" class="inline"><?= csrf_field() ?><input type="hidden" name="action" value="resolve"><input type="hidden" name="ev" value="<?= (int)$ev['id'] ?>">
        <input type="text" name="outcome" placeholder="what you decided, e.g. amendment affects Part L only, no wording change" maxlength="1000" style="min-width:min(420px,60vw)" aria-label="What you decided">
        <button class="btn btn-sm btn-primary" type="submit">Record the decision</button></form>
    </div>
  <?php endforeach; ?>
</section>
<?php endif; ?>

<section>
  <h2>The documents</h2>
  <p class="small muted" style="margin-bottom:12px;max-width:78ch">The strip under each document counts the clauses that <em>name</em> it, in each project type: <?= e(implode(' · ', $types)) ?>. That count is the size of the review if the document changes. It is a floor, not a total: a clause can be governed by a document without citing it — the damp proof course clauses answer to Approved Document C whether or not they say so — and a zero means the library never names that document, not that the subject is absent.</p>
  <?php foreach ($docs as $d):
      $cites = citations($d['cites']);
      $files = json_decode((string)$d['files'], true) ?: [];
      $max = max(1, max($cites ?: [1])); ?>
    <div class="doc" id="doc-<?= e($d['code']) ?>">
      <div>
        <h3><a href="<?= e($d['page_url']) ?>" target="_blank" rel="noopener noreferrer"><?= e($d['title']) ?></a></h3>
        <div class="meta">
          <span>Library holds: <?= e($d['held'] ?: 'not recorded') ?></span>
          <span>Checked <?= e(ago($d['last_checked'])) ?></span>
          <?php if ($d['page_updated']) echo '<span>gov.uk updated ' . e(gmdate('j M Y', strtotime($d['page_updated']))) . '</span>'; ?>
          <span><?= count($files) ?> file<?= count($files) === 1 ? '' : 's' ?></span>
        </div>
        <?php if ($d['error']) echo '<p class="small" style="color:var(--fail);margin-top:6px">' . e($d['error']) . '</p>'; ?>
        <?php if ($cites): ?>
          <div class="cites" style="margin-top:10px">
            <?php foreach ($cites as $type => $n) { $c = $n === 0 ? 'c0' : ($n >= $max * .66 ? 'c3' : ($n >= $max * .33 ? 'c2' : 'c1'));
              echo '<div class="cell ' . $c . '" title="' . e($type) . ': ' . $n . ' clauses"><b>' . e(mb_substr($type, 0, 4)) . '</b><span>' . $n . '</span></div>'; } ?>
          </div>
        <?php endif; ?>
        <details style="margin-top:10px"><summary class="small">Edition held, address, files</summary>
          <div style="margin-top:10px;display:grid;gap:8px">
            <form method="post" class="inline"><?= csrf_field() ?><input type="hidden" name="action" value="held"><input type="hidden" name="id" value="<?= (int)$d['id'] ?>">
              <input type="text" name="held" value="<?= e($d['held']) ?>" placeholder="edition the library is written against" maxlength="200" style="min-width:min(360px,60vw)" aria-label="Edition held"><button class="btn btn-sm" type="submit">Save</button></form>
            <form method="post" class="inline"><?= csrf_field() ?><input type="hidden" name="action" value="url"><input type="hidden" name="id" value="<?= (int)$d['id'] ?>">
              <input type="url" name="page_url" value="<?= e($d['page_url']) ?>" maxlength="400" style="min-width:min(460px,70vw)" aria-label="gov.uk address"><button class="btn btn-sm" type="submit">Save address</button></form>
            <?php if ($files): ?><ul class="small" style="margin:4px 0 0;padding-left:18px"><?php foreach ($files as $u => $t) echo '<li><a href="' . e($u) . '" target="_blank" rel="noopener noreferrer">' . e($t) . '</a></li>'; ?></ul><?php endif; ?>
          </div>
        </details>
      </div>
      <div class="docstate">
        <span class="pill <?= ['current' => 'pill-pass', 'changed' => 'pill-hold', 'error' => 'pill-fail', 'unchecked' => ''][$d['status']] ?? '' ?>">
          <?= ['current' => 'No change', 'changed' => 'Changed', 'error' => 'Unreadable', 'unchecked' => 'Not checked'][$d['status']] ?? e($d['status']) ?></span>
        <form method="post"><?= csrf_field() ?><input type="hidden" name="action" value="check-one"><input type="hidden" name="id" value="<?= (int)$d['id'] ?>"><button class="btn btn-sm" type="submit">Check</button></form>
      </div>
    </div>
  <?php endforeach; ?>
</section>

<?php if ($doneRecent): ?>
<section>
  <h2>Reviewed</h2>
  <?php foreach ($doneRecent as $ev): ?>
    <div class="event done"><div><strong>Approved Document <?= e($ev['code']) ?></strong> · changed <?= e(gmdate('j M Y', strtotime($ev['at']))) ?></div>
      <div><?= e($ev['summary']) ?></div>
      <div class="who">Reviewed by <?= e($ev['reviewed_by']) ?> on <?= e(gmdate('j M Y', strtotime($ev['reviewed_at']))) ?><?= $ev['outcome'] ? ' — ' . e($ev['outcome']) : '' ?></div></div>
  <?php endforeach; ?>
</section>
<?php endif; ?>

<section>
  <h2>Why this does not edit the library</h2>
  <p class="small muted" style="max-width:70ch">The first rule in this repository is never to invent a figure: every dimension, U-value, fire period and percentage has to come from the Approved Document, a British Standard or a manufacturer. A watcher can see that a PDF was replaced. It cannot read the amendment and know that a limiting value moved from 0.18 to 0.16, and a program that guessed would put an invented number into a document going to building control. So the machine does the part it can do honestly — notice the change, name the clauses at risk, keep the record of what was decided — and a person writes the wording in <code>data/</code>.</p>
</section>
<?php page_end(['admin' => true]);
