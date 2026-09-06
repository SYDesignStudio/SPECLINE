<?php
/* Drafting proposed edits to the library.
 *
 * The watch notices that a document moved. This drafts the edits that follow from it, for a
 * person to approve. What it may draft is deliberately narrow, and the narrowness is the point.
 *
 * IT DRAFTS ONLY EDITS IT CAN GROUND IN SOMETHING IT HAS ACTUALLY READ. Today that is the
 * edition a clause names. gov.uk gives us the titles of the files attached to a publication
 * page, and those titles carry the edition year: "Approved Document F: Volume 1 2026 edition".
 * If a clause in the library names an older edition of that same document, the replacement is
 * mechanical — one year for another, with every other word untouched — and the evidence is the
 * attachment title, quoted on the proposal.
 *
 * IT NEVER DRAFTS A FIGURE. A U-value, a fire period, a ventilation rate or a percentage can
 * only be changed by reading the amendment, and this code cannot read the amendment: the
 * Approved Documents are PDFs whose text sits behind subsetted font encodings, and PHP on
 * shared hosting has no reliable way through them. Guessing would breach the first rule in
 * CLAUDE.md and put an invented number into a building control document. So clauses that state
 * figures are listed for a person to read, with the figures they assert pulled out so the
 * reviewer knows exactly what to check, and no wording is proposed for them.
 *
 * PUBLISHED IS NOT IN FORCE. A new edition on gov.uk is not the standard yet: the 2026 editions
 * of L1 and F1 were published on 24 March 2026 and come into force on 24 March 2027. Every
 * edition proposal carries that warning and none of them is approved by default.
 *
 * APPROVAL DOES NOT WRITE TO THE LIBRARY. This server holds a deployed copy of data/, and the
 * next push overwrites it, so a change written here would vanish and never reach git, the
 * structural check or the tests. Approved proposals are exported as an assert-based Python
 * script — the same shape as the edit scripts this repository already uses — to run in the
 * working copy, where build.py and the 185 assertions can have their say before anything is
 * committed.
 */

declare(strict_types=1);

if (!defined('DATA_DIR')) { http_response_code(404); exit("Not found\n"); }   /* include only */

/* ---------- reading the library off disk ---------- */

/** Every data file, as [path => source]. */
function library_files(): array {
    static $f = null;
    if ($f !== null) return $f;
    $f = [];
    foreach (glob(REPO_ROOT . '/data/specdata_*.js') ?: [] as $p) $f[$p] = (string)file_get_contents($p);
    return $f;
}

/**
 * Every clause paragraph in the library, with enough context to place it.
 * Returns [['file'=>…, 'rel'=>…, 'type'=>…, 'title'=>…, 'text'=>…], …]
 * `text` is the paragraph exactly as it appears in the file, escapes and all, so it can be
 * used as the search term of a replacement without any re-encoding.
 */
function library_clauses(): array {
    static $out = null;
    if ($out !== null) return $out;
    $out = [];
    foreach (library_files() as $path => $src) {
        $rel = 'data/' . basename($path);
        /* type boundaries, so each clause can be attributed to a project type */
        $bounds = [];
        if (preg_match_all('/name:\s*"([^"]+)",\s*region:/', $src, $m, PREG_OFFSET_CAPTURE)) {
            $n = count($m[0]);
            for ($i = 0; $i < $n; $i++) {
                $bounds[] = ['name' => $m[1][$i][0], 'start' => $m[0][$i][1],
                             'end' => $i + 1 < $n ? $m[0][$i + 1][1] : strlen($src)];
            }
        }
        $typeAt = function (int $pos) use ($bounds) {
            foreach ($bounds as $b) if ($pos >= $b['start'] && $pos < $b['end']) return $b['name'];
            return '?';
        };
        /* the nearest preceding t:"…" is the clause this paragraph belongs to */
        $titles = [];
        if (preg_match_all('/\bt:\s*"((?:[^"\\\\]|\\\\.)*)"/', $src, $tm, PREG_OFFSET_CAPTURE))
            foreach ($tm[1] as $i => $t) $titles[] = ['title' => $t[0], 'at' => $tm[0][$i][1]];
        $titleAt = function (int $pos) use ($titles) {
            $best = '';
            foreach ($titles as $t) { if ($t['at'] < $pos) $best = $t['title']; else break; }
            return $best;
        };
        /* the paragraphs themselves: long double-quoted strings */
        if (preg_match_all('/"((?:[^"\\\\]|\\\\.){60,})"/', $src, $pm, PREG_OFFSET_CAPTURE)) {
            foreach ($pm[1] as $p) {
                $out[] = ['file' => $path, 'rel' => $rel, 'type' => $typeAt($p[1]),
                          'title' => $titleAt($p[1]), 'text' => $p[0]];
            }
        }
    }
    return $out;
}

/* ---------- what edition does gov.uk now publish? ---------- */

/**
 * The newest edition year visible in the attachment titles of a watched document, with the
 * title it came from as evidence. Returns null when the titles carry no year.
 */
function published_edition(array $doc): ?array {
    $files = json_decode((string)$doc['files'], true) ?: [];
    $best = null;
    foreach ($files as $url => $title) {
        /* A year in the title, or in the file name as a fallback. Not \b: the year in
           ADL1_2026.pdf follows an underscore, which is a word character, so \b never
           matches there and every new-edition file would be missed. */
        $hay = $title . ' ' . basename((string)$url);
        if (!preg_match_all('/(?<![0-9])(?:19|20)\d{2}(?![0-9])/', $hay, $m)) continue;
        foreach ($m[0] as $y) {
            $y = (int)$y;
            if ($y < 1990 || $y > (int)gmdate('Y') + 2) continue;
            if ($best === null || $y > $best['year']) $best = ['year' => $y, 'title' => $title, 'url' => (string)$url];
        }
    }
    return $best;
}

/* ---------- drafting ---------- */

/**
 * Does the library itself say when an edition comes into force? If a clause states it, quote
 * it: it is our own recorded text, not an inference, and it is exactly what the reviewer needs
 * before accepting an edition change. Returns null when nothing in the library says.
 */
function commencement_hint(int $year): ?string {
    foreach (library_clauses() as $c) {
        if (strpos($c['text'], (string)$year) === false) continue;
        if (!preg_match('/[^.]*\b(?:in force|come into force|comes into force)[^.]*\./iu', $c['text'], $m)) continue;
        if (strpos($m[0], (string)$year) === false && strpos($c['text'], (string)$year . ' edition') === false) continue;
        return trim(preg_replace('/\s+/', ' ', $m[0]));
    }
    return null;
}

/** The figures a clause asserts, so a reviewer knows what to check against the new document. */
function clause_figures(string $text): array {
    $out = [];
    $pats = [
        '/\b\d\.\d{2}\s*W\/m/u'                        => 'U-value',
        '/\b\d{1,3}\s*(?:minutes|min)\b/u'             => 'fire period',
        '/\bREI\s?\d{2,3}|EI\s?\d{2,3}|E\s?\d{2,3}\b/u'=> 'fire classification',
        '/\b\d{1,3}\s*dB\b/u'                          => 'sound',
        '/\b\d{1,4}\s*(?:l\/s|litres per second)/u'    => 'ventilation rate',
        '/\b\d{1,3}\s*per cent|\b\d{1,3}%/u'           => 'percentage',
        '/\b\d{2,5}\s*mm\b/u'                          => 'dimension',
        '/\b\d{1,3}\s*°C/u'                            => 'temperature',
    ];
    foreach ($pats as $re => $kind) {
        if (preg_match_all($re, $text, $m)) {
            foreach (array_slice(array_unique($m[0]), 0, 6) as $v) $out[] = trim($v) . ' (' . $kind . ')';
        }
    }
    return array_slice(array_unique($out), 0, 10);
}

/** Is this exact string unique in its file? A replacement is only safe when it is. */
function unique_in_file(string $file, string $needle): bool {
    $src = library_files()[$file] ?? '';
    return substr_count($src, $needle) === 1;
}

/**
 * Draft the proposals that follow from one document's change.
 * Writes rows into `proposals` and returns a tally.
 */
function draft_proposals(array $doc, ?int $eventId = null): array {
    $tally = ['edition' => 0, 'review' => 0, 'skipped' => 0];
    $code = (string)$doc['code'];
    $pub = published_edition($doc);
    $cites = (string)$doc['cites'];
    if ($cites === '') return $tally;

    /* clear anything still undecided for this document, so re-drafting does not pile up */
    q("DELETE FROM proposals WHERE doc_id = ? AND status = 'draft'", [(int)$doc['id']]);

    /* the phrase we are willing to rewrite: an edition year sitting near this document's name */
    $near = '(?:Approved Document ' . preg_quote($code, '/') . '\b|\bPart ' . preg_quote($code, '/') . '\b)';
    $commence = $pub ? commencement_hint($pub['year']) : null;

    foreach (library_clauses() as $c) {
        if (!preg_match('/' . $cites . '/', $c['text'])) continue;

        $made = false;
        if ($pub) {
            /* "…Approved Document L Volume 1, 2021 edition…" — the year within 120 characters
               of the document's own name, so a year belonging to some other citation is left
               alone. Only the four digits change. */
            $re = '/(' . $near . '.{0,120}?)\b((?:19|20)\d{2})(\s*edition)/su';
            if (preg_match($re, $c['text'], $m) && (int)$m[2] < $pub['year']) {
                $new = preg_replace_callback($re, function ($x) use ($pub) {
                    return $x[1] . $pub['year'] . $x[3];
                }, $c['text'], 1);
                if ($new !== null && $new !== $c['text']) {
                    if (unique_in_file($c['file'], $c['text'])) {
                        q('INSERT INTO proposals (doc_id, event_id, kind, type_name, clause_title, file_rel, find_text, replace_text, evidence, figures, status, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                          [(int)$doc['id'], $eventId, 'edition', $c['type'], $c['title'], $c['rel'], $c['text'], $new,
                           'The clause names the ' . $m[2] . ' edition. gov.uk now attaches "' . $pub['title'] . '" to the publication page for this document, so a ' . $pub['year'] . ' edition is published. Only the four digits of the year are changed; every other word is untouched.'
                           . ($commence ? ' The library already records when it applies: "' . $commence . '" Do not approve this until that date has passed.'
                                        : ' Nothing in the library records when the ' . $pub['year'] . ' edition comes into force. Confirm the commencement date on gov.uk before approving, because a published edition is not the standard until it is in force.'),
                           json_encode(clause_figures($c['text'])), 'draft', now()]);
                        $tally['edition']++; $made = true;
                    } else {
                        $tally['skipped']++; $made = true;   /* identical text twice: not safely replaceable */
                    }
                }
            }
        }
        if (!$made) {
            $figs = clause_figures($c['text']);
            if ($figs) {
                q('INSERT INTO proposals (doc_id, event_id, kind, type_name, clause_title, file_rel, find_text, replace_text, evidence, figures, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  [(int)$doc['id'], $eventId, 'review', $c['type'], $c['title'], $c['rel'], $c['text'], '',
                   'This clause states figures that Approved Document ' . $code . ' governs. No wording is proposed: a figure can only be changed by reading the amendment, which this module does not do. Read the passages listed and decide.',
                   json_encode($figs), 'draft', now()]);
                $tally['review']++;
            }
        }
    }
    audit('proposals-drafted', 'AD ' . $code . ': ' . json_encode($tally));
    return $tally;
}

/* ---------- export ---------- */

/**
 * The approved edits as a Python script for the working copy: every replacement asserted, so a
 * clause that has moved on since the proposal was drafted stops the script instead of being
 * silently missed. Same shape as the edit scripts already in this repository.
 */
function export_script(array $rows): string {
    $py  = "# Approved library edits, exported from the Specline regulations watch\n";
    $py .= "# " . gmdate('c') . "\n#\n";
    $py .= "# Run from the repository root, then:  python build.py --test\n";
    $py .= "# Every replacement is asserted, so a clause that has changed since the proposal was\n";
    $py .= "# drafted stops the script rather than being silently skipped. Nothing here was\n";
    $py .= "# invented: each edit changes an edition year, and the evidence is quoted above it.\n";
    $py .= "import io, sys\n\nEDITS = {\n";
    $byFile = [];
    foreach ($rows as $r) $byFile[$r['file_rel']][] = $r;
    foreach ($byFile as $file => $items) {
        $py .= "  " . py_str($file) . ": [\n";
        foreach ($items as $r) {
            $py .= "    # " . str_replace("\n", "\n    # ", wordwrap(
                    $r['type_name'] . ' — ' . $r['clause_title'] . "\n" . $r['evidence'], 92, "\n", false)) . "\n";
            $py .= "    (" . py_str($r['find_text']) . ",\n     " . py_str($r['replace_text']) . "),\n";
        }
        $py .= "  ],\n";
    }
    $py .= "}\n\n";
    /* Two phases on purpose. Checking and writing in one pass would leave the earlier files
       already rewritten when a later one fails, so a stale proposal would half-apply. */
    $py .= "pending, problems = {}, []\n";
    $py .= "for f, pairs in EDITS.items():\n";
    $py .= "    s = io.open(f, encoding='utf-8').read()\n";
    $py .= "    for old, new in pairs:\n";
    $py .= "        n = s.count(old)\n";
    $py .= "        if n != 1:\n";
    $py .= "            problems.append('%d matches (expected 1) in %s for: %s...' % (n, f, old[:80]))\n";
    $py .= "            continue\n";
    $py .= "        s = s.replace(old, new)\n";
    $py .= "    pending[f] = s\n";
    $py .= "if problems:\n";
    $py .= "    print('Nothing was written. The library has moved on since these were drafted:\\n')\n";
    $py .= "    for p in problems: print('  ' + p)\n";
    $py .= "    print('\\nRe-draft them in the dashboard against the current library.')\n";
    $py .= "    sys.exit(1)\n";
    $py .= "for f, s in pending.items():\n";
    $py .= "    io.open(f, 'w', encoding='utf-8', newline='').write(s)\n";
    $py .= "    print('%-28s %d edits' % (f.split('/')[-1], len(EDITS[f])))\n";
    $py .= "print('%d edits applied. Now run: python build.py --test' % sum(len(v) for v in EDITS.values()))\n";
    return $py;
}

/** A Python string literal, quoted safely whatever the clause contains. */
function py_str(string $s): string {
    $out = '"';
    $len = strlen($s);
    for ($i = 0; $i < $len; $i++) {
        $ch = $s[$i]; $o = ord($ch);
        if ($ch === '"' || $ch === '\\') $out .= '\\' . $ch;
        elseif ($ch === "\n") $out .= '\\n';
        elseif ($ch === "\r") $out .= '\\r';
        elseif ($ch === "\t") $out .= '\\t';
        elseif ($o < 32) $out .= sprintf('\\x%02x', $o);
        else $out .= $ch;
    }
    return $out . '"';
}

/** Where the two strings differ, as a short before/after for the screen. */
function diff_fragment(string $a, string $b, int $pad = 70): array {
    $n = min(strlen($a), strlen($b));
    $i = 0; while ($i < $n && $a[$i] === $b[$i]) $i++;
    $j = 0; while ($j < $n - $i && $a[strlen($a) - 1 - $j] === $b[strlen($b) - 1 - $j]) $j++;
    /* Widen to whole words. 2021 and 2026 differ in one character, and reporting the change
       as "1 becoming 6" tells the reader nothing; "2021 becoming 2026" is the real edit. */
    while ($i > 0 && ctype_alnum($a[$i - 1]) && ctype_alnum($b[$i - 1] ?? ' ')) $i--;
    while ($j > 0 && ctype_alnum($a[strlen($a) - $j] ?? ' ') && ctype_alnum($b[strlen($b) - $j] ?? ' ')) $j--;
    $start = max(0, $i - $pad);
    /* Split each side into the text before the change, the change itself, and the text after,
       so the page can mark the one thing that moved instead of showing two near-identical
       lines and leaving the reader to hunt for the difference. */
    $side = function (string $s, int $endOfCommonTail) use ($i, $start, $pad) {
        $midLen = max(0, strlen($s) - $endOfCommonTail - $i);
        $tail = substr($s, $i + $midLen, $pad);
        return [
            'pre'  => ($start > 0 ? '…' : '') . substr($s, $start, $i - $start),
            'mid'  => substr($s, $i, $midLen),
            'post' => $tail . ($i + $midLen + $pad < strlen($s) ? '…' : ''),
        ];
    };
    return [
        'a'    => $side($a, $j),
        'b'    => $side($b, $j),
        'from' => substr($a, $i, max(0, strlen($a) - $j - $i)),
        'to'   => substr($b, $i, max(0, strlen($b) - $j - $i)),
    ];
}
