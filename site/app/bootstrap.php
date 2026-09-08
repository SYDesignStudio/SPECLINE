<?php
/* Specline accounts and administration — shared bootstrap.
 *
 * Every page under account/, admin/, contact.php and cron.php starts with
 *     require __DIR__ . '/../app/bootstrap.php';
 * and gets: configuration, the database (with its schema), the session, CSRF tokens,
 * rate limiting, mail, the page layout and the guards.
 *
 * WHERE THE DATA LIVES. Hostinger deploys the repository into public_html on every push,
 * so nothing inside the web root survives a deployment. The database, the optional config
 * file and the setup key therefore live in the domain directory ABOVE public_html — the
 * same place the waiting list CSV has always been written. Nothing there is web-served.
 *
 * WHAT THIS IS NOT. There is no billing here and no access to the specification tool.
 * An account is the practice's identity and its place in the queue for the first release.
 * Nothing on these pages certifies, approves or guarantees anything about a building.
 */

declare(strict_types=1);

/* Nothing in app/ is a page. site/app/.htaccess denies it at the web server, and this
   is the same rule in the file itself, so a server that ignores .htaccess still cannot
   fetch the configuration by asking for it directly. */
if (PHP_SAPI !== 'cli' && realpath((string)($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) {
    http_response_code(404); exit("Not found\n");
}

/* ---------- paths ---------- */
define('SITE_ROOT', dirname(__DIR__));                       // .../site
define('REPO_ROOT', dirname(SITE_ROOT));                     // the repository = public_html
define('DATA_DIR',  getenv('SPECLINE_DATA_DIR') ?: dirname(REPO_ROOT));   // above public_html
define('DB_FILE',   DATA_DIR . '/specline.sqlite');
define('CONFIG_FILE', DATA_DIR . '/specline-config.php');
define('SETUP_KEY_FILE', DATA_DIR . '/specline-setup-key.txt');
define('WAITLIST_CSV', DATA_DIR . '/specline-waitlist.csv');

/* ---------- configuration (optional file above the web root) ----------
 * <?php return ['notify_to' => 'x@y', 'base_url' => 'https://specline.co.uk', 'mysql' => [...]];
 */
$CFG = [
    'notify_to' => 'info@specline.co.uk',
    'base_url'  => 'https://specline.co.uk',
    'mysql'     => null,                          // ['dsn'=>..., 'user'=>..., 'pass'=>...] if SQLite is unavailable
    'session_hours' => 24 * 14,
];
if (is_readable(CONFIG_FILE)) {
    $override = include CONFIG_FILE;
    if (is_array($override)) $CFG = array_merge($CFG, $override);
}
if (PHP_SAPI === 'cli-server' || (isset($_SERVER['HTTP_HOST']) && str_starts_with($_SERVER['HTTP_HOST'], 'localhost'))) {
    $CFG['base_url'] = 'http://' . ($_SERVER['HTTP_HOST'] ?? 'localhost');
}
function cfg(string $k, $default = null) { global $CFG; return $CFG[$k] ?? $default; }

/* ---------- errors: never on screen ---------- */
ini_set('display_errors', '0');
ini_set('log_errors', '1');
error_reporting(E_ALL);
date_default_timezone_set('UTC');

/* ---------- headers ---------- */
if (PHP_SAPI !== 'cli') {
    header('X-Content-Type-Options: nosniff');
    header('X-Frame-Options: DENY');
    header('Referrer-Policy: strict-origin-when-cross-origin');
    /* form-action must name Stripe. Chrome and Safari apply this directive to the WHOLE redirect
       chain of a form submission, not just its action: with 'self' alone, posting to a page that
       answers 302 https://checkout.stripe.com is blocked, silently, after the request has already
       been made. Twelve checkout sessions were created that way in thirty-six seconds before the
       console gave it away. checkout.stripe.com is the till; billing.stripe.com is the portal
       where a subscriber changes a card or cancels. */
    header("Content-Security-Policy: default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; script-src 'self' 'unsafe-inline'; form-action 'self' https://checkout.stripe.com https://billing.stripe.com; frame-ancestors 'none'; base-uri 'self'");
    header('Cache-Control: no-store');
}

/* ---------- database ---------- */
function db(): PDO {
    static $pdo = null;
    if ($pdo) return $pdo;
    $mysql = cfg('mysql');
    if (is_array($mysql) && !empty($mysql['dsn'])) {
        $pdo = new PDO($mysql['dsn'], $mysql['user'] ?? '', $mysql['pass'] ?? '', [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
        $GLOBALS['DB_DRIVER'] = 'mysql';
    } else {
        if (!in_array('sqlite', PDO::getAvailableDrivers(), true)) {
            throw new RuntimeException('Neither SQLite nor a MySQL configuration is available.');
        }
        $new = !file_exists(DB_FILE);
        $pdo = new PDO('sqlite:' . DB_FILE, null, null, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
        if ($new) @chmod(DB_FILE, 0600);
        $pdo->exec('PRAGMA journal_mode=WAL');
        $pdo->exec('PRAGMA foreign_keys=ON');
        $pdo->exec('PRAGMA busy_timeout=5000');
        $GLOBALS['DB_DRIVER'] = 'sqlite';
    }
    /* Run the schema statements only when the code has moved past what the database was
       built to. The home page opens this on every visit, and issuing a dozen CREATE TABLE
       statements to answer "is the site locked" would be silly. Bump SCHEMA_VERSION whenever
       migrate() changes, or the new table will not appear. */
    $have = null;
    try { $st = $pdo->query("SELECT v FROM settings WHERE k = 'schema_v'"); $have = $st ? $st->fetchColumn() : null; }
    catch (Throwable $t) { $have = null; }
    if ((string)$have !== (string)SCHEMA_VERSION) {
        migrate($pdo);
        $pdo->prepare('DELETE FROM settings WHERE k = ?')->execute(['schema_v']);
        $pdo->prepare('INSERT INTO settings (k, v) VALUES (?, ?)')->execute(['schema_v', (string)SCHEMA_VERSION]);
    }
    return $pdo;
}
const SCHEMA_VERSION = 7;
function db_driver(): string { db(); return $GLOBALS['DB_DRIVER'] ?? '?'; }

function migrate(PDO $pdo): void {
    $ai = ($GLOBALS['DB_DRIVER'] ?? 'sqlite') === 'mysql' ? 'INTEGER PRIMARY KEY AUTO_INCREMENT' : 'INTEGER PRIMARY KEY AUTOINCREMENT';
    $stmts = [
     "CREATE TABLE IF NOT EXISTS settings (k VARCHAR(64) PRIMARY KEY, v TEXT NOT NULL)",
     /* contact_email is the address printed on the specification, and it belongs to the
        practice, not to whoever happens to be signed in. Taking it from the user's login
        meant a second person in the same practice changed the cover of every document. */
     "CREATE TABLE IF NOT EXISTS practices (id $ai, name VARCHAR(150) NOT NULL, address TEXT NOT NULL DEFAULT '',
        designer VARCHAR(120) NOT NULL DEFAULT '', phone VARCHAR(40) NOT NULL DEFAULT '', plan VARCHAR(20) NOT NULL DEFAULT 'undecided',
        seats INTEGER NOT NULL DEFAULT 1, contact_email VARCHAR(254) NOT NULL DEFAULT '', created_at VARCHAR(32) NOT NULL)",
     "CREATE TABLE IF NOT EXISTS users (id $ai, practice_id INTEGER NOT NULL, email VARCHAR(254) NOT NULL UNIQUE,
        name VARCHAR(120) NOT NULL, pass_hash VARCHAR(255) NOT NULL, role VARCHAR(20) NOT NULL DEFAULT 'member',
        verified_at VARCHAR(32), created_at VARCHAR(32) NOT NULL, last_login_at VARCHAR(32), login_count INTEGER NOT NULL DEFAULT 0,
        source VARCHAR(20) NOT NULL DEFAULT 'site')",
     "CREATE TABLE IF NOT EXISTS tokens (id $ai, user_id INTEGER NOT NULL, kind VARCHAR(20) NOT NULL, hash VARCHAR(64) NOT NULL UNIQUE,
        expires_at VARCHAR(32) NOT NULL, used_at VARCHAR(32), payload TEXT NOT NULL DEFAULT '')",
     "CREATE TABLE IF NOT EXISTS throttle (k VARCHAR(80) PRIMARY KEY, hits TEXT NOT NULL)",
     "CREATE TABLE IF NOT EXISTS waitlist (id $ai, at VARCHAR(32) NOT NULL, email VARCHAR(254) NOT NULL, name VARCHAR(120) NOT NULL DEFAULT '',
        practice VARCHAR(150) NOT NULL DEFAULT '', ip VARCHAR(64) NOT NULL DEFAULT '', UNIQUE (at, email))",
     "CREATE TABLE IF NOT EXISTS messages (id $ai, at VARCHAR(32) NOT NULL, name VARCHAR(120) NOT NULL DEFAULT '', email VARCHAR(254) NOT NULL,
        practice VARCHAR(150) NOT NULL DEFAULT '', subject VARCHAR(200) NOT NULL DEFAULT '', body TEXT NOT NULL, ip VARCHAR(64) NOT NULL DEFAULT '',
        user_id INTEGER, status VARCHAR(20) NOT NULL DEFAULT 'new', note TEXT NOT NULL DEFAULT '')",
     "CREATE TABLE IF NOT EXISTS regdocs (id $ai, code VARCHAR(16) NOT NULL UNIQUE, title VARCHAR(200) NOT NULL, page_url VARCHAR(400) NOT NULL,
        held VARCHAR(200) NOT NULL DEFAULT '', cites VARCHAR(200) NOT NULL DEFAULT '', last_checked VARCHAR(32), last_changed VARCHAR(32),
        fingerprint VARCHAR(64), files TEXT, page_updated VARCHAR(32), latest_note TEXT, status VARCHAR(20) NOT NULL DEFAULT 'unchecked', error TEXT)",
     "CREATE TABLE IF NOT EXISTS regevents (id $ai, doc_id INTEGER NOT NULL, at VARCHAR(32) NOT NULL, summary TEXT NOT NULL,
        before_files TEXT, after_files TEXT, reviewed_at VARCHAR(32), reviewed_by VARCHAR(120), outcome TEXT)",
     "CREATE TABLE IF NOT EXISTS audit (id $ai, at VARCHAR(32) NOT NULL, who VARCHAR(254) NOT NULL DEFAULT '', what VARCHAR(80) NOT NULL, detail TEXT NOT NULL DEFAULT '')",
     /* One row per specification job. `payload` is the app's own snapshot, stored whole so the
        app stays the authority on its shape; the columns beside it exist only so this side can
        list and count jobs without parsing it. practice_id is what separates one practice's
        work from another's, and it is always taken from the session, never from the client. */
     "CREATE TABLE IF NOT EXISTS jobs (id VARCHAR(48) PRIMARY KEY, practice_id INTEGER NOT NULL, user_id INTEGER,
        type VARCHAR(24) NOT NULL DEFAULT '', job_no VARCHAR(80) NOT NULL DEFAULT '', title VARCHAR(240) NOT NULL DEFAULT '',
        rev VARCHAR(12) NOT NULL DEFAULT '', payload TEXT NOT NULL, created_at VARCHAR(32) NOT NULL, updated_at VARCHAR(32) NOT NULL)",
     "CREATE TABLE IF NOT EXISTS practice_profile (practice_id INTEGER PRIMARY KEY, payload TEXT NOT NULL, updated_at VARCHAR(32) NOT NULL)",
     /* Entitlement is NOT practices.plan: that column is what a practice says it wants, typed
        on its own account page. This is what it may actually use, written only by the owner or
        (later) a payment processor. One live row per practice; the rest is history. */
     "CREATE TABLE IF NOT EXISTS entitlements (id $ai, practice_id INTEGER NOT NULL, plan VARCHAR(20) NOT NULL,
        seats INTEGER NOT NULL DEFAULT 1, status VARCHAR(20) NOT NULL DEFAULT 'active', source VARCHAR(24) NOT NULL DEFAULT 'manual',
        note TEXT NOT NULL DEFAULT '', ref VARCHAR(120) NOT NULL DEFAULT '', started_at VARCHAR(32) NOT NULL,
        ends_at VARCHAR(32), ended_at VARCHAR(32), created_at VARCHAR(32) NOT NULL, created_by VARCHAR(254) NOT NULL DEFAULT '')",
     /* Per-spec purchases as a ledger rather than a counter: a balance you cannot explain is a
        balance nobody will trust. Positive rows are bought or granted, negative rows are issued. */
     "CREATE TABLE IF NOT EXISTS spec_credits (id $ai, practice_id INTEGER NOT NULL, delta INTEGER NOT NULL,
        reason VARCHAR(40) NOT NULL DEFAULT '', ref VARCHAR(120) NOT NULL DEFAULT '', job_id VARCHAR(48) NOT NULL DEFAULT '',
        at VARCHAR(32) NOT NULL, by_who VARCHAR(254) NOT NULL DEFAULT '')",
     /* Every webhook event, stored before it is acted on and keyed on the processor's own event
        id, so a replay — and Stripe replays — is recorded and ignored rather than granting twice. */
     "CREATE TABLE IF NOT EXISTS billing_events (id $ai, event_id VARCHAR(80) NOT NULL UNIQUE, type VARCHAR(60) NOT NULL,
        practice_id INTEGER, at VARCHAR(32) NOT NULL, payload TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '')",
     "CREATE TABLE IF NOT EXISTS proposals (id $ai, doc_id INTEGER NOT NULL, event_id INTEGER, kind VARCHAR(20) NOT NULL,
        type_name VARCHAR(80) NOT NULL DEFAULT '', clause_title VARCHAR(300) NOT NULL DEFAULT '', file_rel VARCHAR(120) NOT NULL DEFAULT '',
        find_text TEXT NOT NULL, replace_text TEXT NOT NULL DEFAULT '', evidence TEXT NOT NULL DEFAULT '', figures TEXT,
        status VARCHAR(20) NOT NULL DEFAULT 'draft', created_at VARCHAR(32) NOT NULL, decided_at VARCHAR(32), decided_by VARCHAR(120), note TEXT NOT NULL DEFAULT '')",
    ];
    foreach ($stmts as $s) $pdo->exec($s);

    /* CREATE TABLE IF NOT EXISTS does nothing to a table that already exists, so a column
       added after a database was built needs its own step. Ask for the column and add it
       only if the query fails; that works the same on SQLite and MySQL. */
    foreach ([['practices', 'contact_email', "VARCHAR(254) NOT NULL DEFAULT ''"],
              ['practices', 'stripe_customer_id', "VARCHAR(80) NOT NULL DEFAULT ''"],
              ['entitlements', 'ref', "VARCHAR(120) NOT NULL DEFAULT ''"],
              ['tokens',    'payload',       "TEXT NOT NULL DEFAULT ''"]] as [$table, $col, $type]) {
        try { $pdo->query("SELECT $col FROM $table LIMIT 1"); }
        catch (Throwable $t) { try { $pdo->exec("ALTER TABLE $table ADD COLUMN $col $type"); } catch (Throwable $t2) {} }
    }
}

require_once __DIR__ . '/billing.php';
require_once __DIR__ . '/stripe.php';

function q(string $sql, array $args = []): PDOStatement {
    $st = db()->prepare($sql); $st->execute($args); return $st;
}
function row(string $sql, array $args = []): ?array { $r = q($sql, $args)->fetch(); return $r === false ? null : $r; }
function rows(string $sql, array $args = []): array { return q($sql, $args)->fetchAll(); }
function val(string $sql, array $args = []) { $r = q($sql, $args)->fetch(PDO::FETCH_NUM); return $r === false ? null : $r[0]; }

function setting(string $k, ?string $default = null): ?string {
    $v = val('SELECT v FROM settings WHERE k = ?', [$k]);
    return $v === null ? $default : (string)$v;
}
function set_setting(string $k, string $v): void {
    if (db_driver() === 'mysql') q('INSERT INTO settings (k, v) VALUES (?, ?) ON DUPLICATE KEY UPDATE v = VALUES(v)', [$k, $v]);
    else q('INSERT INTO settings (k, v) VALUES (?, ?) ON CONFLICT(k) DO UPDATE SET v = excluded.v', [$k, $v]);
}
function now(): string { return gmdate('c'); }
function audit(string $what, string $detail = ''): void {
    q('INSERT INTO audit (at, who, what, detail) VALUES (?, ?, ?, ?)', [now(), current_user()['email'] ?? '', $what, $detail]);
}

/* ---------- session ---------- */
function session_start_secure(): void {
    if (session_status() === PHP_SESSION_ACTIVE) return;
    $secure = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off');
    session_name('specline');
    session_set_cookie_params(['lifetime' => 0, 'path' => '/', 'secure' => $secure, 'httponly' => true, 'samesite' => 'Lax']);
    ini_set('session.use_strict_mode', '1');
    ini_set('session.gc_maxlifetime', (string)(cfg('session_hours') * 3600));
    session_start();
    if (!empty($_SESSION['uid'])) {
        $idle = time() - (int)($_SESSION['seen'] ?? 0);
        if ($idle > cfg('session_hours') * 3600) { session_unset(); session_destroy(); session_start(); }
    }
    $_SESSION['seen'] = time();
}

function current_user(): ?array {
    static $u = false;
    if ($u !== false) return $u;
    if (PHP_SAPI === 'cli') return $u = null;
    session_start_secure();
    if (empty($_SESSION['uid'])) return $u = null;
    $u = row('SELECT u.*, p.name AS practice_name, p.plan, p.seats FROM users u JOIN practices p ON p.id = u.practice_id WHERE u.id = ?', [(int)$_SESSION['uid']]);
    return $u;
}
/* The only place a session is created. Three paths reach it — signing in, verifying an
 * address and completing a password reset — and the before-launch lock is enforced HERE
 * rather than at each of them, because it was originally checked only in login.php and a
 * password reset signed a non-owner straight in past it. Returns false and creates nothing
 * when the caller must refuse.
 */
function login_user(array $user): bool {
    if (site_locked() && ($user['role'] ?? '') !== 'owner') {
        audit('login-locked', (string)($user['email'] ?? ''));
        return false;
    }
    session_start_secure();
    session_regenerate_id(true);
    $_SESSION['uid'] = (int)$user['id'];
    $_SESSION['seen'] = time();
    q('UPDATE users SET last_login_at = ?, login_count = login_count + 1 WHERE id = ?', [now(), (int)$user['id']]);
    return true;
}
const LOCKED_MESSAGE = 'Specline is not open yet. Your account and your work are safe, and you will be emailed when it opens.';
function logout_user(): void {
    session_start_secure();
    $_SESSION = [];
    if (ini_get('session.use_cookies')) {
        $p = session_get_cookie_params();
        setcookie(session_name(), '', ['expires' => time() - 42000, 'path' => $p['path'], 'secure' => $p['secure'], 'httponly' => true, 'samesite' => 'Lax']);
    }
    session_destroy();
}
function require_login(): array {
    $u = current_user();
    if (!$u) { header('Location: /account/login.php?next=' . rawurlencode($_SERVER['REQUEST_URI'] ?? '/account/')); exit; }
    return $u;
}
function require_admin(): array {
    $u = require_login();
    if ($u['role'] !== 'owner' || empty($u['verified_at'])) { http_response_code(403); page_start('Not available'); echo '<div class="sheet"><h1>Not available</h1><p>This area is for the Specline administrator.</p><p><a href="/account/">Back to your account</a></p></div>'; page_end(); exit; }
    return $u;
}
function admin_exists(): bool { return (int)val("SELECT COUNT(*) FROM users WHERE role = 'owner'") > 0; }

/* ---------- before launch ----------
 * Locked means two things at once, because they are the same intention: nobody new may create
 * an account, and nobody but the owner may sign in. It is one switch rather than two so that
 * "the site is not open yet" cannot end up half true.
 *
 * What it does NOT do is touch the waiting list, which is the point of being closed: a practice
 * that finds the site can still ask to be told when it opens.
 */
function site_locked(): bool { return setting('site_lock', '0') === '1'; }

/* ---------- who may open the specification tool ----------
 * Deliberately shut by default. Deploying the tool must not, by itself, hand it to everyone
 * who has ever signed up: the administrator opens it when the practice is ready to be let in.
 *   admin     only the owner (the default, and what a fresh install gets)
 *   verified  any account whose email address is verified
 *   closed    nobody, including the owner
 */
function app_open_mode(): string {
    $m = setting('app_open', 'admin');
    return in_array($m, ['admin', 'verified', 'closed'], true) ? $m : 'admin';
}
function app_access(?array $u = null): bool {
    $u = $u ?? current_user();
    if (!$u) return false;
    return match (app_open_mode()) {
        'verified' => !empty($u['verified_at']),
        'admin'    => $u['role'] === 'owner',
        default    => false,
    };
}

/* ---------- CSRF ---------- */
function csrf_token(): string {
    session_start_secure();
    if (empty($_SESSION['csrf'])) $_SESSION['csrf'] = bin2hex(random_bytes(32));
    return $_SESSION['csrf'];
}
function csrf_field(): string { return '<input type="hidden" name="csrf" value="' . e(csrf_token()) . '">'; }
function csrf_check(): void {
    $sent = (string)($_POST['csrf'] ?? '');
    if ($sent === '' || !hash_equals(csrf_token(), $sent)) { http_response_code(400); exit('The form has expired. Go back and try again.'); }
}
function is_post(): bool { return ($_SERVER['REQUEST_METHOD'] ?? '') === 'POST'; }

/* ---------- rate limiting: a sliding window per key ---------- */
function throttle(string $key, int $max, int $windowSeconds): bool {
    $k = hash('sha256', $key);
    $now = time();
    $r = row('SELECT hits FROM throttle WHERE k = ?', [$k]);
    $hits = array_values(array_filter(array_map('intval', $r ? explode(',', $r['hits']) : []), fn($t) => $now - $t < $windowSeconds));
    if (count($hits) >= $max) return false;
    $hits[] = $now;
    $csv = implode(',', $hits);
    if ($r) q('UPDATE throttle SET hits = ? WHERE k = ?', [$csv, $k]);
    else q('INSERT INTO throttle (k, hits) VALUES (?, ?)', [$k, $csv]);
    return true;
}
function client_ip(): string { return (string)($_SERVER['REMOTE_ADDR'] ?? ''); }

/* ---------- tokens (verification, password reset): stored hashed ---------- */
/* `payload` carries whatever the token is for — today, the new address a change of sign-in
   is waiting on. It is deliberately NOT applied when the token is issued: the address only
   moves when the link sent to it is opened, which is what proves the person asking can read
   the new mailbox. */
function issue_token(int $userId, string $kind, int $ttlSeconds, string $payload = ''): string {
    $raw = bin2hex(random_bytes(32));
    q('DELETE FROM tokens WHERE user_id = ? AND kind = ?', [$userId, $kind]);
    q('INSERT INTO tokens (user_id, kind, hash, expires_at, payload) VALUES (?, ?, ?, ?, ?)',
      [$userId, $kind, hash('sha256', $raw), gmdate('c', time() + $ttlSeconds), $payload]);
    return $raw;
}
function consume_token(string $raw, string $kind, ?string &$payload = null): ?array {
    $payload = null;
    if (!preg_match('/^[0-9a-f]{64}$/', $raw)) return null;
    $t = row('SELECT * FROM tokens WHERE hash = ? AND kind = ? AND used_at IS NULL', [hash('sha256', $raw), $kind]);
    if (!$t || strtotime($t['expires_at']) < time()) return null;
    q('UPDATE tokens SET used_at = ? WHERE id = ?', [now(), (int)$t['id']]);
    $payload = (string)($t['payload'] ?? '');
    return row('SELECT * FROM users WHERE id = ?', [(int)$t['user_id']]);
}

/* ---------- mail ----------
 * A real mailbox now exists at info@specline.co.uk, so mail is sent FROM it. Until 6 September
 * 2026 no From header was set at all, deliberately: there was no mailbox on the domain, and
 * mail claiming to come from an address that does not exist is commonly dropped. That cost us
 * the account verification emails, which is what gates a new practice getting in.
 *
 * This only works while the domain's SPF record authorises the host that sends it. The mailbox
 * is on the same hosting, so it does, but if verification mail starts bouncing check SPF and
 * DKIM for specline.co.uk before changing anything here.
 */
function mail_from(): string { return (string)cfg('mail_from', cfg('notify_to')); }
function send_mail(string $to, string $subject, string $body, ?string $replyTo = null): bool {
    if (preg_match('/[\r\n]/', $to . $subject . (string)$replyTo)) return false;
    $from = mail_from();
    $headers = "From: Specline <" . $from . ">\r\nContent-Type: text/plain; charset=utf-8\r\nX-Mailer: Specline";
    if ($replyTo && filter_var($replyTo, FILTER_VALIDATE_EMAIL)) $headers .= "\r\nReply-To: " . $replyTo;
    if (PHP_SAPI === 'cli-server') { @file_put_contents(DATA_DIR . '/specline-mail.log', "TO: $to\nSUBJECT: $subject\n$body\n----\n", FILE_APPEND); return true; }
    /* -f sets the envelope sender as well as the header, so bounces come back to the mailbox
       and SPF is checked against an address that exists. */
    return @mail($to, $subject, $body, $headers, '-f' . $from);
}
function notify_studio(string $subject, string $body, ?string $replyTo = null): void { send_mail(cfg('notify_to'), $subject, $body, $replyTo); }

/* ---------- validation helpers ---------- */
function e(?string $s): string { return htmlspecialchars((string)$s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }
function clean(string $k, int $max = 200): string {
    $v = trim((string)($_POST[$k] ?? ''));
    $v = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F]/', '', $v) ?? '';
    return mb_substr($v, 0, $max);
}
function valid_email(string $s): bool { return $s !== '' && strlen($s) <= 254 && filter_var($s, FILTER_VALIDATE_EMAIL) !== false && !preg_match('/[\r\n]/', $s); }
function password_problem(string $p, string $email): ?string {
    if (strlen($p) < 12) return 'Use at least 12 characters. A short sentence works well.';
    if (strlen($p) > 200) return 'That is longer than 200 characters.';
    if (strcasecmp($p, $email) === 0) return 'Your password cannot be your email address.';
    if (preg_match('/^(.)\1+$/', $p) || in_array(strtolower($p), ['password1234', 'specline2026', '123456789012'], true)) return 'That password is too easy to guess.';
    return null;
}
function ago(?string $iso): string {
    if (!$iso) return '—';
    $d = time() - strtotime($iso);
    if ($d < 60) return 'just now';
    if ($d < 3600) return intdiv($d, 60) . ' min ago';
    if ($d < 86400) return intdiv($d, 3600) . ' h ago';
    if ($d < 86400 * 30) return intdiv($d, 86400) . ' d ago';
    return gmdate('j M Y', strtotime($iso));
}
function fmt_when(?string $iso): string { return $iso ? gmdate('j M Y, H:i', strtotime($iso)) . ' UTC' : '—'; }
function redirect(string $to): never { header('Location: ' . $to); exit; }

/* ---------- layout ---------- */
function lockup(string $href = '/'): string {
    return '<a class="lockup" href="' . e($href) . '" aria-label="Specline"><svg viewBox="0 0 6.7 28" aria-hidden="true"><path d="M5.7 1H1V27H5.7" fill="none" stroke="var(--bracket)" stroke-width="2"/></svg><b aria-hidden="true">Specline</b><svg viewBox="0 0 6.7 28" aria-hidden="true"><path d="M1 1H5.7V27H1" fill="none" stroke="var(--bracket)" stroke-width="2"/></svg></a>';
}
function page_start(string $title, array $o = []): void {
    $u = current_user();
    echo '<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">';
    echo '<title>' . e($title) . ' · Specline</title><meta name="robots" content="noindex,nofollow">';
    echo '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 32 32\'%3E%3Crect width=\'32\' height=\'32\' rx=\'6\' fill=\'%230E6E85\'/%3E%3Cpath d=\'M13.5 7.5H8V24.5H13.5M18.5 7.5H24V24.5H18.5\' fill=\'none\' stroke=\'%23FBFAF8\' stroke-width=\'3\'/%3E%3C/svg%3E">';
    echo '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>';
    echo '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">';
    echo '<link rel="stylesheet" href="/static/ui.css"></head><body class="' . e($o['body'] ?? '') . '">';
    if (!empty($o['admin'])) {
        $here = basename($_SERVER['SCRIPT_NAME'] ?? '');
        $nav = [['index.php', 'Overview'], ['signups.php', 'Sign-ups'], ['waitlist.php', 'Waiting list'], ['messages.php', 'Messages'], ['regs.php', 'Regulations watch'], ['proposals.php', 'Proposed edits'], ['billing.php', 'Billing'], ['settings.php', 'Settings']];
        echo '<div class="admin"><aside class="rail">' . lockup('/admin/') . '<p class="railtag">Administration</p><nav aria-label="Administration">';
        foreach ($nav as [$f, $label]) {
            $n = match ($f) {
                'messages.php'  => (int)val("SELECT COUNT(*) FROM messages WHERE status = 'new'"),
                'regs.php'      => (int)val("SELECT COUNT(*) FROM regdocs WHERE status = 'changed'"),
                'proposals.php' => (int)val("SELECT COUNT(*) FROM proposals WHERE status = 'draft'"),
                default         => 0,
            };
            echo '<a href="/admin/' . $f . '"' . ($here === $f ? ' aria-current="page"' : '') . '>' . e($label) . ($n ? ' <span class="count">' . $n . '</span>' : '') . '</a>';
        }
        echo '</nav><div class="railfoot"><span>' . e($u['name'] ?? '') . '</span><a href="/account/">Account</a><a href="/account/logout.php">Sign out</a></div></aside><main class="main">';
    } else {
        echo '<header class="top">' . lockup() . '<nav aria-label="Account">';
        if ($u) echo '<a href="/account/">' . e($u['name']) . '</a>' . ($u['role'] === 'owner' ? '<a href="/admin/">Administration</a>' : '') . '<a href="/account/logout.php">Sign out</a>';
        elseif (site_locked()) echo '<a href="/account/login.php">Sign in</a><a class="btn btn-primary btn-sm" href="/#join">Join the waiting list</a>';
        else echo '<a href="/account/login.php">Sign in</a><a class="btn btn-primary btn-sm" href="/account/signup.php">Create an account</a>';
        echo '</nav></header><main class="wrap">';
    }
}
function page_end(array $o = []): void {
    if (!empty($o['admin'])) echo '</main></div>';
    else echo '</main><footer class="foot"><p>Specline drafts the specification. The named designer remains responsible for its suitability, and compliance of the work is determined by the building control body. Nothing here is a certificate, an approval or a plan check.</p><p><a href="/terms.html">Terms</a> · <a href="/privacy.html">Privacy</a> · <a href="/contact.php">Contact</a> · Specline, a trading name of SY Design Studio Ltd</p></footer>';
    echo '</body></html>';
}
function flash(?string $set = null, string $kind = 'ok'): ?array {
    session_start_secure();
    if ($set !== null) { $_SESSION['flash'] = [$kind, $set]; return null; }
    $f = $_SESSION['flash'] ?? null; unset($_SESSION['flash']); return $f;
}
function show_flash(): void {
    if ($f = flash()) echo '<p class="notice notice-' . e($f[0]) . '" role="status">' . e($f[1]) . '</p>';
}
function field(string $name, string $label, string $type = 'text', array $a = []): string {
    $id = 'f_' . $name;
    $attrs = '';
    foreach ($a as $k => $v) { if ($v === true) $attrs .= ' ' . $k; elseif ($v !== false && $v !== null) $attrs .= ' ' . $k . '="' . e((string)$v) . '"'; }
    $val = $type === 'password' ? '' : ' value="' . e((string)($_POST[$name] ?? ($a['value'] ?? ''))) . '"';
    if ($type === 'textarea') return '<div class="field"><label for="' . $id . '">' . e($label) . '</label><textarea id="' . $id . '" name="' . $name . '"' . $attrs . '>' . e((string)($_POST[$name] ?? ($a['value'] ?? ''))) . '</textarea></div>';
    return '<div class="field"><label for="' . $id . '">' . e($label) . '</label><input id="' . $id . '" type="' . $type . '" name="' . $name . '"' . $val . $attrs . '></div>';
}
