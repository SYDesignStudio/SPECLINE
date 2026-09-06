<?php
/* The scheduled regulations check.
 *
 * Two ways in, both safe to leave in place:
 *   a cron job that fetches   https://specline.co.uk/cron.php?k=<key from Settings>
 *   a cron job that runs      php /home/…/public_html/site/cron.php
 * On the command line no key is needed, because only someone with shell access can run it.
 */
declare(strict_types=1);
require __DIR__ . '/app/bootstrap.php';
require __DIR__ . '/app/regwatch.php';

$cli = PHP_SAPI === 'cli';
if (!$cli) {
    header('Content-Type: text/plain; charset=utf-8');
    $token = setting('cron_token', '');
    $given = (string)($_GET['k'] ?? '');
    if ($token === '' || !hash_equals($token, $given)) {
        http_response_code(404);
        exit("Not found\n");
    }
    if (!throttle('cron-http', 6, 3600)) { http_response_code(429); exit("Too many runs in the last hour.\n"); }
}
set_time_limit(300);
$t = regwatch_run($cli ? 'cron-cli' : 'cron-http');
echo gmdate('c') . "  changed={$t['changed']} same={$t['same']} baseline={$t['baseline']} error={$t['error']}\n";
