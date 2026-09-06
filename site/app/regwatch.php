<?php
/* Regulations watch.
 *
 * Watches the gov.uk publication page of every Approved Document and records when one
 * changes. It does NOT edit the specification library, and it never will: a change on
 * gov.uk says that a document moved, not what the new clause should say. The first
 * non-negotiable in CLAUDE.md is "never invent a figure", and an automatic rewrite would
 * be exactly that at scale. What this module does instead is the part a machine can do
 * honestly — notice the change, and list every clause in every project type that cites
 * the document, so a person has the review checklist and the audit trail.
 *
 * How a change is detected. A gov.uk publication page lists its attachments as links into
 * assets.publishing.service.gov.uk, and every replaced file gets a new address there. The
 * page also carries its "last updated" history as <time> elements. The fingerprint is the
 * sorted set of attachment addresses plus the latest update date; if it moves, something
 * was published. One GET per document, once a day, with an honest User-Agent.
 */

declare(strict_types=1);

if (!defined('DATA_DIR')) { http_response_code(404); exit("Not found\n"); }   /* include only */

/* The nineteen Approved Documents. page_url verified 6 September 2026 against the gov.uk
   collection page. `held` is the edition the library was written against where FACTS.md
   records it; blank means "not recorded", which the dashboard says out loud. `cites` is
   the pattern that finds a clause citing the document. */
const REGDOCS = [
 ['A',  'Approved Document A: structure',                                  'structure-approved-document-a',                                                     '',                                             'Approved Document A\b|\bPart A\b|Requirement A\d|\(A\d\)'],
 ['B',  'Approved Document B: fire safety',                                'fire-safety-approved-document-b',                                                   'Vol 1 2019 edition incorporating 2020 and 2022 amendments', 'Approved Document B\b|\bPart B\b|Requirement B\d|\(B\d\)'],
 ['C',  'Approved Document C: site preparation and moisture',              'site-preparation-and-resistance-to-contaminates-and-moisture-approved-document-c',  '',                                             'Approved Document C\b|\bPart C\b|Requirement C\d|\(C\d\)'],
 ['D',  'Approved Document D: toxic substances',                           'toxic-substances-approved-document-d',                                              '',                                             'Approved Document D\b|\bPart D\b|Requirement D\d|\(D\d\)'],
 ['E',  'Approved Document E: resistance to sound',                        'resistance-to-sound-approved-document-e',                                           '',                                             'Approved Document E\b|\bPart E\b|Requirement E\d|\(E\d\)'],
 ['F',  'Approved Document F: ventilation',                                'ventilation-approved-document-f',                                                   'Vol 1 and Vol 2, 2021 editions',              'Approved Document F\b|\bPart F\b|Requirement F\d|\(F\d\)'],
 ['G',  'Approved Document G: sanitation, hot water and water efficiency', 'sanitation-hot-water-safety-and-water-efficiency-approved-document-g',              '',                                             'Approved Document G\b|\bPart G\b|Requirement G\d|\(G\d\)'],
 ['H',  'Approved Document H: drainage and waste disposal',                'drainage-and-waste-disposal-approved-document-h',                                   '',                                             'Approved Document H\b|\bPart H\b|Requirement H\d|\(H\d\)'],
 ['J',  'Approved Document J: combustion appliances and fuel storage',     'combustion-appliances-and-fuel-storage-systems-approved-document-j',                '',                                             'Approved Document J\b|\bPart J\b|Requirement J\d|\(J\d\)'],
 ['K',  'Approved Document K: protection from falling, collision and impact','protection-from-falling-collision-and-impact-approved-document-k',                 '',                                             'Approved Document K\b|\bPart K\b|Requirement K\d|\(K\d\)'],
 ['L',  'Approved Document L: conservation of fuel and power',             'conservation-of-fuel-and-power-approved-document-l',                                'Vol 1 2021 edition as amended 2023',          'Approved Document L\b|\bPart L\b|Requirement L\d|\(L\d\)'],
 ['M',  'Approved Document M: access to and use of buildings',             'access-to-and-use-of-buildings-approved-document-m',                                '',                                             'Approved Document M\b|\bPart M\b|Requirement M\d|\(M\d\)'],
 ['O',  'Approved Document O: overheating',                                'overheating-approved-document-o',                                                   '',                                             'Approved Document O\b|\bPart O\b|Requirement O\d|\(O\d\)'],
 ['P',  'Approved Document P: electrical safety',                          'electrical-safety-approved-document-p',                                             '',                                             'Approved Document P\b|\bPart P\b|Requirement P\d|\(P\d\)'],
 ['Q',  'Approved Document Q: security in dwellings',                      'security-in-dwellings-approved-document-q',                                         '',                                             'Approved Document Q\b|\bPart Q\b|Requirement Q\d|\(Q\d\)'],
 ['R',  'Approved Document R: infrastructure for electronic communications','infrastructure-for-electronic-communications-approved-document-r',                 '',                                             'Approved Document R\b|\bPart R\b|Requirement R\d|\(R\d\)'],
 ['S',  'Approved Document S: infrastructure for charging electric vehicles','infrastructure-for-charging-electric-vehicles-approved-document-s',                '',                                             'Approved Document S\b|\bPart S\b|Requirement S\d|\(S\d\)'],
 ['T',  'Approved Document T: toilet accommodation',                       'toilet-accommodation-approved-document-t',                                          '',                                             'Approved Document T\b|\bPart T\b|Requirement T\d|\(T\d\)'],
 ['7',  'Approved Document 7: material and workmanship',                   'material-and-workmanship-approved-document-7',                                      '',                                             'Approved Document 7\b|Regulation 7\b'],
];
const REG_UA = 'Specline regulations watch (+https://specline.co.uk)';
const REG_INTERVAL = 86400;   // seconds between automatic checks

function regwatch_seed(): void {
    foreach (REGDOCS as [$code, $title, $slug, $held, $cites]) {
        $url = 'https://www.gov.uk/government/publications/' . $slug;
        if (row('SELECT id FROM regdocs WHERE code = ?', [$code])) {
            q('UPDATE regdocs SET title = ?, cites = ? WHERE code = ?', [$title, $cites, $code]);   // derived from code, always refreshed
            q('UPDATE regdocs SET held = ? WHERE code = ? AND held = ?', [$held, $code, '']);
        } else {
            q('INSERT INTO regdocs (code, title, page_url, held, cites) VALUES (?, ?, ?, ?, ?)', [$code, $title, $url, $held, $cites]);
        }
    }
}

/* ---------- the library, read from disk: which clauses cite which document ---------- */
function library_types(): array {
    static $types = null;
    if ($types !== null) return $types;
    $types = [];
    foreach (glob(REPO_ROOT . '/data/specdata_*.js') ?: [] as $f) {
        $s = (string)file_get_contents($f);
        if (!preg_match_all('/name:\s*"([^"]+)",\s*region:/', $s, $m, PREG_OFFSET_CAPTURE)) continue;
        $n = count($m[0]);
        for ($i = 0; $i < $n; $i++) {
            $start = $m[0][$i][1];
            $end = $i + 1 < $n ? $m[0][$i + 1][1] : strlen($s);
            $types[$m[1][$i][0]] = substr($s, $start, $end - $start);
        }
    }
    return $types;
}
/* Count, per project type, the clauses (paragraph strings) citing a document. */
function citations(string $pattern): array {
    $out = [];
    if ($pattern === '') return $out;
    foreach (library_types() as $type => $text) {
        $n = 0;
        if (preg_match_all('/"((?:[^"\\\\]|\\\\.)*)"/s', $text, $strings)) {
            foreach ($strings[1] as $para) if (strlen($para) > 40 && preg_match('/' . $pattern . '/', $para)) $n++;
        }
        $out[$type] = $n;
    }
    return $out;
}
/* The citing clauses themselves, for the review list: [type => [title => [snippets]]] */
function citing_clauses(string $pattern, int $limitPerType = 40): array {
    $out = [];
    foreach (library_types() as $type => $text) {
        $items = [];
        if (preg_match_all('/t:\s*"((?:[^"\\\\]|\\\\.)*)"[^\[]*\bp:\s*\[((?:[^\]]|\](?!\s*\}))*)\]/s', $text, $blocks, PREG_SET_ORDER)) {
            foreach ($blocks as $b) {
                if (!preg_match('/' . $pattern . '/', $b[2])) continue;
                $items[] = $b[1];
                if (count($items) >= $limitPerType) break;
            }
        }
        if ($items) $out[$type] = $items;
    }
    return $out;
}

/* ---------- fetching and parsing gov.uk ---------- */
function reg_fetch(string $url): ?string {
    if (function_exists('curl_init')) {
        $c = curl_init($url);
        curl_setopt_array($c, [CURLOPT_RETURNTRANSFER => true, CURLOPT_FOLLOWLOCATION => true, CURLOPT_MAXREDIRS => 4,
            CURLOPT_TIMEOUT => 25, CURLOPT_CONNECTTIMEOUT => 10, CURLOPT_USERAGENT => REG_UA, CURLOPT_SSL_VERIFYPEER => true]);
        $body = curl_exec($c);
        $code = (int)curl_getinfo($c, CURLINFO_RESPONSE_CODE);
        curl_close($c);
        return ($body !== false && $code === 200) ? (string)$body : null;
    }
    $ctx = stream_context_create(['http' => ['timeout' => 25, 'user_agent' => REG_UA, 'follow_location' => 1]]);
    $body = @file_get_contents($url, false, $ctx);
    return $body === false ? null : $body;
}
function reg_parse(string $html): array {
    $dates = [];
    if (preg_match_all('/<time[^>]*class="[^"]*gem-c-published-dates__change-date[^"]*"[^>]*datetime="([^"]+)"/', $html, $m)) $dates = $m[1];
    if (!$dates && preg_match('/<meta[^>]*name="govuk:updated-at"[^>]*content="([^"]+)"/', $html, $m)) $dates = [$m[1]];
    if (!$dates && preg_match('/<meta[^>]*name="govuk:first-published-at"[^>]*content="([^"]+)"/', $html, $m)) $dates = [$m[1]];
    $latest = '';
    foreach ($dates as $d) { $t = strtotime($d); if ($t && (!$latest || $t > strtotime($latest))) $latest = gmdate('c', $t); }

    $titles = [];
    if (preg_match_all('/gem-c-attachment__title[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>\s*([^<]+?)\s*<\/a>/s', $html, $m, PREG_SET_ORDER))
        foreach ($m as $a) $titles[html_entity_decode($a[1])] = trim(html_entity_decode($a[2]));
    $files = [];
    if (preg_match_all('/href="(https:\/\/assets\.publishing\.service\.gov\.uk\/[^"]+\.pdf)"/', $html, $m))
        foreach (array_unique($m[1]) as $u) $files[$u] = $titles[$u] ?? basename($u);
    ksort($files);

    $note = '';
    if (preg_match('/gem-c-published-dates__change-note[^>]*>\s*([^<]+?)\s*</s', $html, $m)) $note = trim(html_entity_decode($m[1]));
    $fp = hash('sha256', implode("\n", array_keys($files)) . "\n" . $latest);
    return ['latest' => $latest, 'files' => $files, 'note' => $note, 'fingerprint' => $fp];
}

/* ---------- one document ---------- */
function regwatch_check_doc(array $doc): string {
    $html = reg_fetch($doc['page_url']);
    if ($html === null) {
        q('UPDATE regdocs SET last_checked = ?, error = ?, status = CASE WHEN status = ? THEN status ELSE ? END WHERE id = ?',
          [now(), 'Could not fetch the publication page (not 200). The address may have changed: check it on gov.uk and update it here.', 'changed', 'error', (int)$doc['id']]);
        return 'error';
    }
    $p = reg_parse($html);
    if (!$p['files'] && !$p['latest']) {
        q('UPDATE regdocs SET last_checked = ?, error = ?, status = CASE WHEN status = ? THEN status ELSE ? END WHERE id = ?',
          [now(), 'The page was fetched but no attachments or dates were found on it. gov.uk may have changed its markup; the parser needs looking at.', 'changed', 'error', (int)$doc['id']]);
        return 'error';
    }
    $filesJson = json_encode($p['files'], JSON_UNESCAPED_SLASHES);
    if (!$doc['fingerprint']) {
        q('UPDATE regdocs SET last_checked = ?, fingerprint = ?, files = ?, page_updated = ?, latest_note = ?, status = ?, error = NULL WHERE id = ?',
          [now(), $p['fingerprint'], $filesJson, $p['latest'], $p['note'], 'current', (int)$doc['id']]);
        return 'baseline';
    }
    if ($p['fingerprint'] === $doc['fingerprint']) {
        q('UPDATE regdocs SET last_checked = ?, error = NULL, status = CASE WHEN status = ? THEN status ELSE ? END WHERE id = ?',
          [now(), 'changed', 'current', (int)$doc['id']]);
        return 'same';
    }
    $before = json_decode((string)$doc['files'], true) ?: [];
    $added = array_diff_key($p['files'], $before);
    $removed = array_diff_key($before, $p['files']);
    $parts = ['gov.uk publication page updated ' . ($p['latest'] ? gmdate('j M Y', strtotime($p['latest'])) : '(date not shown)') . '.'];
    if ($p['note']) $parts[] = 'gov.uk says: "' . $p['note'] . '"';
    if ($added) $parts[] = 'Added: ' . implode('; ', array_values($added)) . '.';
    if ($removed) $parts[] = 'Removed: ' . implode('; ', array_values($removed)) . '.';
    if (!$added && !$removed) $parts[] = 'The attachment list is unchanged, so the change is to the page itself.';
    q('INSERT INTO regevents (doc_id, at, summary, before_files, after_files) VALUES (?, ?, ?, ?, ?)',
      [(int)$doc['id'], now(), implode(' ', $parts), json_encode($before, JSON_UNESCAPED_SLASHES), $filesJson]);
    q('UPDATE regdocs SET last_checked = ?, last_changed = ?, fingerprint = ?, files = ?, page_updated = ?, latest_note = ?, status = ?, error = NULL WHERE id = ?',
      [now(), now(), $p['fingerprint'], $filesJson, $p['latest'], $p['note'], 'changed', (int)$doc['id']]);
    return 'changed';
}

/* ---------- all documents ---------- */
function regwatch_run(string $trigger = 'manual'): array {
    regwatch_seed();
    $tally = ['baseline' => 0, 'same' => 0, 'changed' => 0, 'error' => 0];
    $changed = [];
    foreach (rows('SELECT * FROM regdocs ORDER BY id') as $doc) {
        $r = regwatch_check_doc($doc);
        $tally[$r]++;
        if ($r === 'changed') $changed[] = $doc['code'];
    }
    set_setting('regwatch_last_run', now());
    set_setting('regwatch_last_trigger', $trigger);
    audit('regwatch', $trigger . ': ' . json_encode($tally));
    if ($changed) {
        notify_studio('Specline: Approved Document ' . implode(', ', $changed) . ' changed on gov.uk',
            "The regulations watch found a change to Approved Document " . implode(', ', $changed) . ".\n\n"
          . "Review it here: " . cfg('base_url') . "/admin/regs.php\n\n"
          . "Nothing in the library has been changed. The dashboard lists the clauses that cite the document.\n");
    }
    return $tally;
}
function regwatch_due(): bool {
    $last = setting('regwatch_last_run');
    return !$last || (time() - strtotime($last)) > REG_INTERVAL;
}
