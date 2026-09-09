<?php
/* The specification tool, behind the practice login.
 *
 * The app itself is site/app/spec.html, which .htaccess denies to the web. This file is the
 * only way to it: it checks the session first and reads the file second, so an unauthenticated
 * request never receives a byte of the tool. build.py writes that file; never edit it by hand.
 *
 * What gets injected is the practice on the session and a CSRF token. The tool then stores its
 * jobs through /api.php, which scopes every row by that practice — which is the whole point of
 * moving it here. As a Claude artifact it had no idea who was looking at it, so one practice's
 * jobs could not be kept apart from another's.
 */

declare(strict_types=1);
require __DIR__ . '/app/bootstrap.php';

$u = require_login();

/* Shut by default: see app_open_mode() in bootstrap.php. Deploying the tool must not by itself
   hand it to everyone who has signed up. */
if (!app_access($u)) {
    http_response_code(403);
    page_start('Specline');
    $mode = app_open_mode();
    echo '<div class="sheet"><h1>Not open to your account yet</h1>';
    if ($mode === 'closed') {
        echo '<p class="lede">The specification tool is closed to everyone while it is being worked on. Nothing is lost — any job you have saved is still here.</p>';
    } elseif (empty($u['verified_at'])) {
        echo '<p class="lede">Verify your email address first. The link was sent to <span class="mono">' . e($u['email']) . '</span> when you created the account, and your account page can send it again.</p>';
    } else {
        echo '<p class="lede">Specline opens to founding members in turn. Your account is on the list and you will be emailed when it can open the tool.</p>';
    }
    echo '<p><a class="btn btn-primary" href="/account/">Back to your account</a></p></div>';
    page_end();
    exit;
}

/* Billing, once it is enforced. Separate from app_access() above on purpose: that answers
   "is this account allowed in at all", this answers "is this practice paid up". Off until the
   administrator switches it on, so deploying billing does not shut anyone out. */
$refusal = open_refusal($u);
if ($refusal !== '') {
    http_response_code(402);
    page_start('Specline');
    $e = entitlement((int)$u['practice_id']);
    echo '<div class="sheet"><h1>The tool is not open for this practice</h1>';
    echo '<p class="lede">' . e($refusal) . '</p>';
    if ($e['credits'] > 0) echo '<p class="small">You hold ' . (int)$e['credits'] . ' specification credit' . ($e['credits'] === 1 ? '' : 's') . '.</p>';
    echo '<p class="small muted">Nothing has been deleted. Every job, and the practice profile that prints on the cover, is exactly as you left it.</p>';
    echo '<p><a class="btn btn-primary" href="/account/">Your account</a> <a class="btn" href="/contact.php">Ask us</a></p></div>';
    page_end();
    exit;
}

/* The practice as the app knows it: the profile the tool last saved, over the account details.
   Everything the cover page prints comes from here — the name, the address, the logo, the accent
   colour and the named designer in the responsibility statement.
   THERE IS NO THIRD FALLBACK, and that is the point. The app used to carry SY Design Studio Ltd
   compiled in as the seed profile, logo included, so any practice that had not filled the profile
   in issued specifications under the vendor's name. Now an unset field prints [Practice name] and
   asks to be filled: a blank cover gets corrected before issue, another firm's name might not. */
$practice = row('SELECT * FROM practices WHERE id = ?', [(int)$u['practice_id']]);
$stored   = row('SELECT payload FROM practice_profile WHERE practice_id = ?', [(int)$u['practice_id']]);
$profile  = [
    'name'     => (string)$practice['name'],
    'designer' => (string)$practice['designer'],
    'addr'     => (string)$practice['address'],
    /* The practice's own contact address, not the signed-in user's login. It is what a
       building control officer reads on the cover and replies to. Falls back to the login
       only until the practice has set one. */
    'email'    => (string)($practice['contact_email'] ?: $u['email']),
    'phone'    => (string)$practice['phone'],
    'plan'     => (string)$practice['plan'],
    'seats'    => (int)$practice['seats'],
];
if ($stored) {
    $j = json_decode($stored['payload'], true);
    if (is_array($j)) $profile = array_merge($profile, array_filter($j, fn($v) => $v !== null && $v !== ''));
}

$boot = [
    'api'      => '/api.php',
    'csrf'     => csrf_token(),
    'user'     => ['name' => (string)$u['name'], 'email' => (string)$u['email'], 'role' => (string)$u['role']],
    'practice' => $profile,
    /* what this practice may do, so the tool can say so rather than fail at the last step */
    'billing'  => ['enforced' => billing_enforced(), 'issue' => entitled_to_issue((int)$u['practice_id']),
                   'credits' => spec_credit_balance((int)$u['practice_id']),
                   /* Whether a draft download carries the DRAFT mark. Settled here at page load,
                      so a practice that subscribes in another tab has to reopen the tool for its
                      drafts to come out clean — which is the safe way round. */
                   'mark_drafts' => drafts_are_marked($u)],
    'account'  => '/account/',
    'signout'  => '/account/logout.php',
];

$file = __DIR__ . '/app/spec.html';
if (!is_readable($file)) {
    http_response_code(503);
    page_start('Specline');
    echo '<div class="sheet"><h1>The tool is not built</h1><p class="lede">site/app/spec.html is missing. Run <code>python build.py</code> and commit what it writes: the file is generated, and only what is committed reaches the server.</p></div>';
    page_end();
    exit;
}

/* No CSP header here: the built page carries the whole app inline, and the policy in
   .htaccess already allows inline script and style for the site. */
header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-store, private');
header('X-Robots-Tag: noindex, nofollow');

$html = (string)file_get_contents($file);
$inject = '<script>window.SPECLINE = ' . json_encode($boot, JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) . ';</script>';
$marker = '<!-- SPECLINE_BOOTSTRAP -->';
echo str_contains($html, $marker) ? str_replace($marker, $inject, $html) : $inject . $html;
