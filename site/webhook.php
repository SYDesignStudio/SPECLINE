<?php
/* Stripe's webhook. The only endpoint on this site that grants an entitlement.
 *
 * It is public, because Stripe has to reach it, and that is exactly why the signature check is
 * the first thing it does and the only thing that lets anything through. No secret configured,
 * no signature header, a stale timestamp or a digest that does not match all mean 400 and
 * nothing written. Anyone can POST here; only Stripe can be believed.
 *
 * Two more rules. The raw body is verified BEFORE it is decoded, because the signature covers
 * the bytes Stripe sent and not a re-encoded version of them. And a 200 is returned for an event
 * this site does not act on, because a webhook that answers with an error to things it simply
 * does not care about teaches a processor to retry forever.
 */

declare(strict_types=1);
require __DIR__ . '/app/bootstrap.php';

header('Content-Type: text/plain; charset=utf-8');
header('Cache-Control: no-store');

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') { http_response_code(405); echo "POST only.\n"; exit; }

$payload = (string)file_get_contents('php://input');
if ($payload === '' || strlen($payload) > 1000000) { http_response_code(400); echo "No usable body.\n"; exit; }

$sig    = (string)($_SERVER['HTTP_STRIPE_SIGNATURE'] ?? '');
$secret = stripe_webhook_secret();

if (!stripe_verify($payload, $sig, $secret)) {
    /* Deliberately terse: an attacker learns nothing, and the administrator can see the count. */
    set_setting('stripe_webhook_rejected', (string)(((int)setting('stripe_webhook_rejected', '0')) + 1));
    set_setting('stripe_webhook_rejected_at', now());
    http_response_code(400);
    echo "Signature did not verify.\n";
    exit;
}

$ev = json_decode($payload, true);
if (!is_array($ev)) { http_response_code(400); echo "Malformed event.\n"; exit; }

$note = stripe_handle_event($ev);
set_setting('stripe_webhook_last', now());
set_setting('stripe_webhook_last_type', (string)($ev['type'] ?? ''));

http_response_code(200);
echo "ok: " . $note . "\n";
