<?php
/*
 * server.php — Bada RDP Guard の PHP リファレンス サーバ / RDP ゲートウェイ API
 *
 *   php -S 127.0.0.1:8080 rdp_guard/php/server.php
 *
 * ・GET  /                … web/ のデモ UI を配信
 * ・GET  /rdpguard.js     … ブラウザ用コア (web/ と同一)
 * ・GET  /api/health      … 稼働確認
 * ・POST /api/handshake   … 2 端末の相互認証を実行 (seed 指定で再現可能)
 *     body: {"seed":"...", "sessionId":"S1", "nonceA":"nA", "nonceB":"nB",
 *            "impostor": false}
 * ・POST /api/revise      … base/patches を改訂し conn を判定
 *     body: {"base":[{tuple,effect,note}...], "patches":[{id,rules}...], "conn":[...]}
 *
 * 実運用では RDP ゲートウェイ/プロキシが接続受付時に /api/handshake 相当を呼び、
 * ok=false なら RDP を張らせない、という使い方を想定した防御用参照実装です。
 */
declare(strict_types=1);
require __DIR__ . '/RdpGuard.php';

$webDir = realpath(__DIR__ . '/../web');
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

function jsonOut($data, int $code = 200): void {
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}
function body(): array {
    $raw = file_get_contents('php://input');
    if ($raw === '' || $raw === false) return [];
    $d = json_decode($raw, true);
    return is_array($d) ? $d : [];
}

/* ── API ── */
if ($path === '/api/health') {
    jsonOut(['ok' => true, 'service' => 'bada-rdp-guard', 'php' => PHP_VERSION]);
}

if ($path === '/api/handshake' && $method === 'POST') {
    $b = body();
    $rng = isset($b['seed']) ? RdpGuard::seedRng((string)$b['seed']) : RdpGuard::secureRng();
    $a = RdpGuard::createTerminal('WorkstationA', 4, $rng);
    $srv = RdpGuard::createTerminal('ServerB', 4, $rng);
    $pinnedB = $srv['root'];                 // A がピン留めした B の指紋

    if (!empty($b['impostor'])) {
        // 攻撃者が ServerB を詐称 (鍵は別物) → B の指紋で検証失敗するはず
        $impostor = RdpGuard::createTerminal('ServerB', 4, $rng);
        $sid = $b['sessionId'] ?? 'S-atk';
        $nonceA = $b['nonceA'] ?? bin2hex(random_bytes(16));
        $chal = "RDPGUARD1|$sid|ServerB>WorkstationA|$nonceA";
        $fake = RdpGuard::signChallenge($impostor, $chal);
        $ok = RdpGuard::verifyTerminalSig($pinnedB, $chal, $fake);
        jsonOut(['ok' => $ok, 'impostor' => true,
                 'pinnedFingerprintB' => substr($pinnedB, 0, 16),
                 'impostorFingerprint' => $impostor['fingerprint'],
                 'message' => $ok ? '想定外' : 'なりすまし拒否 — 攻撃者の署名は本物 B の指紋で検証失敗。RDP 乗っ取りを阻止。']);
    }

    $r = RdpGuard::mutualHandshake($a, $srv, [
        'sessionId' => $b['sessionId'] ?? null,
        'nonceA' => $b['nonceA'] ?? null,
        'nonceB' => $b['nonceB'] ?? null,
    ]);
    $r['fingerprintA'] = $a['fingerprint'];
    $r['fingerprintB'] = $srv['fingerprint'];
    $r['decision'] = $r['ok'] ? 'ALLOW RDP' : 'DENY RDP';
    jsonOut($r);
}

if ($path === '/api/revise' && $method === 'POST') {
    $b = body();
    $eff = RdpGuard::revise($b['base'] ?? [], $b['patches'] ?? []);
    $out = ['effective' => array_map(fn($r) => ['tuple' => $r['tuple'], 'effect' => $r['effect'], 'source' => $r['source']], $eff)];
    if (!empty($b['conn'])) { $out['decision'] = RdpGuard::decide($eff, $b['conn']); }
    jsonOut($out);
}

/* ── 静的ファイル (web/) ── */
if ($path === '/' || $path === '') { $file = $webDir . '/index.html'; }
else { $file = realpath($webDir . '/' . ltrim($path, '/')); }

if ($file && $webDir && strpos($file, $webDir) === 0 && is_file($file)) {
    $ext = strtolower(pathinfo($file, PATHINFO_EXTENSION));
    $types = ['html' => 'text/html; charset=utf-8', 'js' => 'application/javascript; charset=utf-8',
              'css' => 'text/css; charset=utf-8', 'json' => 'application/json; charset=utf-8'];
    header('Content-Type: ' . ($types[$ext] ?? 'application/octet-stream'));
    readfile($file);
    exit;
}

// php -S 用: 実在の静的ファイルはそのまま返す
if (php_sapi_name() === 'cli-server' && $file && is_file($file)) { return false; }
jsonOut(['error' => 'not found', 'path' => $path], 404);
