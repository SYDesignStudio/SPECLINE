<?php
/* Specline waiting list.
 *
 * Accepts a POST from the form on the home page, records it, and notifies the studio.
 * There is no database: the list is a CSV written OUTSIDE the web root.
 *
 * This file sits at public_html/site/, because Hostinger deploys the repository into
 * public_html. Two levels up is the domain directory ABOVE public_html, which the web
 * server never serves and a deployment never touches — so the list survives every push
 * and cannot be fetched over HTTP.
 *
 * Deliberately narrow: it only ever emails a fixed address, so it cannot be used as a
 * relay, and it stores only what the privacy notice says it stores.
 */

declare(strict_types=1);

const NOTIFY_TO   = 'info@sydesignstudio.co.uk';
const NOTIFY_FROM = 'no-reply@specline.co.uk';   // must be a real mailbox on this domain
const STORE       = __DIR__ . '/../../specline-waitlist.csv';
const RATE_DIR    = __DIR__ . '/../../specline-ratelimit';
const RATE_MAX    = 5;      // submissions per IP
const RATE_WINDOW = 3600;   // per hour

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');

function out(int $code, string $message, bool $ok = false): never {
    http_response_code($code);
    echo json_encode(['ok' => $ok, 'message' => $message], JSON_UNESCAPED_SLASHES);
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    out(405, 'Send this form by POST.');
}

/* Honeypot: a field hidden from people, irresistible to bots. Answer as though it worked,
   so the bot has nothing to learn, but record nothing. */
if (trim((string)($_POST['website'] ?? '')) !== '') {
    out(200, 'Thank you. You are on the list.', true);
}

$email    = trim((string)($_POST['email'] ?? ''));
$name     = trim((string)($_POST['name'] ?? ''));
$practice = trim((string)($_POST['practice'] ?? ''));
$consent  = ($_POST['consent'] ?? '') === 'yes';

if ($email === '')                                   out(422, 'Please enter your email address.');
if (!filter_var($email, FILTER_VALIDATE_EMAIL))      out(422, 'That email address does not look right. Please check it.');
if (strlen($email) > 254)                            out(422, 'That email address is too long.');
if (!$consent)                                       out(422, 'Please tick the box so we know we may email you.');
if (strlen($name) > 100 || strlen($practice) > 150)  out(422, 'That is longer than the form allows. Please shorten it.');

/* Reject anything with a line break: cheap protection against header injection. */
foreach ([$email, $name, $practice] as $field) {
    if (preg_match('/[\r\n]/', $field)) out(422, 'Please remove line breaks from the form.');
}

$ip = (string)($_SERVER['REMOTE_ADDR'] ?? '');

/* Rate limit per IP, stored as one file per IP holding recent timestamps. */
if ($ip !== '') {
    if (!is_dir(RATE_DIR)) @mkdir(RATE_DIR, 0700, true);
    $bucket = RATE_DIR . '/' . hash('sha256', $ip) . '.txt';
    $now    = time();
    $hits   = [];
    if (is_readable($bucket)) {
        foreach (explode("\n", (string)file_get_contents($bucket)) as $t) {
            $t = (int)trim($t);
            if ($t > 0 && $now - $t < RATE_WINDOW) $hits[] = $t;
        }
    }
    if (count($hits) >= RATE_MAX) {
        out(429, 'That is several submissions in a short time. Please try again later, or email us directly.');
    }
    $hits[] = $now;
    @file_put_contents($bucket, implode("\n", $hits), LOCK_EX);
}

/* Record it. The header is written once, on first use. */
$new = !file_exists(STORE);
$fh  = @fopen(STORE, 'a');
if ($fh === false) {
    error_log('specline waitlist: cannot open ' . STORE);
    out(500, 'Something went wrong at our end. Please email info@sydesignstudio.co.uk instead.');
}
if (flock($fh, LOCK_EX)) {
    if ($new) fputcsv($fh, ['timestamp_utc', 'email', 'name', 'practice', 'consent', 'ip']);
    fputcsv($fh, [gmdate('c'), $email, $name, $practice, 'yes', $ip]);
    fflush($fh);
    flock($fh, LOCK_UN);
}
fclose($fh);
@chmod(STORE, 0600);

/* Notify the studio. A failure here must not lose the signup, which is already stored. */
$body = "New Specline waiting list signup\n\n"
      . "Email:    {$email}\n"
      . "Name:     " . ($name !== '' ? $name : '—') . "\n"
      . "Practice: " . ($practice !== '' ? $practice : '—') . "\n"
      . "When:     " . gmdate('c') . " UTC\n"
      . "IP:       " . ($ip !== '' ? $ip : '—') . "\n";
@mail(
    NOTIFY_TO,
    'Specline waiting list: ' . $email,
    $body,
    "From: Specline <" . NOTIFY_FROM . ">\r\nReply-To: " . $email . "\r\nContent-Type: text/plain; charset=utf-8"
);

out(200, 'Thank you. You are on the list and we will be in touch when Specline opens.', true);
