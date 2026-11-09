<?php
/*
 * test-rdpguard.php — Bada RDP Guard コア (PHP 版) の自己検査
 *   php rdp_guard/tools/test-rdpguard.php
 */
declare(strict_types=1);
require __DIR__ . '/../php/RdpGuard.php';

$failed = 0;
function ok(bool $c, string $l): void { global $failed; echo ($c ? 'PASS' : 'FAIL') . "  $l\n"; if (!$c) $failed++; }

/* ── SHA-256 既知ベクタ ── */
ok(RdpGuard::hashHex('abc') === 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad', "SHA-256('abc') 一致");
ok(RdpGuard::hashHex('') === 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', "SHA-256('') 一致");

$rng = RdpGuard::seedRng('test-seed');

/* ── Lamport ── */
$kp = RdpGuard::lamportKeygen($rng);
$digest = RdpGuard::sha256('challenge-xyz');
$sig = RdpGuard::lamportSign($digest, $kp['priv']);
ok(RdpGuard::lamportVerify($digest, $sig, $kp['pub']), 'Lamport 正しい署名は検証OK');
ok(!RdpGuard::lamportVerify(RdpGuard::sha256('challenge-XYZ'), $sig, $kp['pub']), 'Lamport 別メッセージは失敗');

/* ── Merkle ── */
$leaves = array_map(fn($s) => RdpGuard::hashHex($s), ['aa','bb','cc','dd','ee']);
$root = RdpGuard::merkleRoot($leaves);
$allok = true;
for ($i = 0; $i < count($leaves); $i++) { if (!RdpGuard::merkleVerify($leaves[$i], RdpGuard::merklePath($leaves, $i), $root)) $allok = false; }
ok($allok, 'Merkle すべての葉の認証パスが根に結びつく');

/* ── 相互認証: 正規は成功、なりすまし/リプレイは失敗 ── */
$a = RdpGuard::createTerminal('WorkstationA', 4, $rng);
$b = RdpGuard::createTerminal('ServerB', 4, $rng);
$r = RdpGuard::mutualHandshake($a, $b, ['sessionId' => 'S1', 'nonceA' => 'nA', 'nonceB' => 'nB']);
ok($r['ok'] && $r['aVerified'] && $r['bVerified'], '正規端末同士は相互認証成功 (RDP 許可)');

$impostor = RdpGuard::createTerminal('ServerB', 4, $rng);  // 名前詐称・鍵は別物
$chal = 'RDPGUARD1|S2|ServerB>WorkstationA|nA2';
$fake = RdpGuard::signChallenge($impostor, $chal);
ok(!RdpGuard::verifyTerminalSig($b['root'], $chal, $fake), 'なりすましは本物の指紋で検証失敗 → 乗っ取り阻止');
$stolen = RdpGuard::signChallenge($b, 'RDPGUARD1|S3|ServerB>WorkstationA|nOLD');
ok(!RdpGuard::verifyTerminalSig($b['root'], 'RDPGUARD1|S4|ServerB>WorkstationA|nNEW', $stolen), 'リプレイ無効 (別ノンス)');

/* ── Reviser ── */
$base = [
    ['tuple' => ['*'], 'effect' => 'deny', 'note' => '既定全拒否'],
    ['tuple' => ['rdp','office','server1'], 'effect' => 'allow'],
];
$p1 = ['id' => 'patch-a', 'rules' => [
    ['tuple' => ['rdp','office','server1','admin'], 'effect' => 'allow'],
    ['tuple' => ['rdp','vpn','server1'], 'effect' => 'allow'],
]];
$p2 = ['id' => 'patch-b', 'rules' => [
    ['tuple' => ['rdp','office','server1','admin'], 'effect' => 'deny', 'note' => 'admin一時停止'],
]];
$eff = RdpGuard::revise($base, [$p1, $p2]);
ok(RdpGuard::decide($eff, ['rdp','office','server1','bob'])['effect'] === 'allow', '社内一般ユーザ許可');
ok(RdpGuard::decide($eff, ['rdp','internet','server1','bob'])['effect'] === 'deny', '社外は既定拒否');
ok(RdpGuard::decide($eff, ['rdp','office','server1','admin'])['effect'] === 'deny', '後のパッチが上書き (admin deny に改訂)');
ok(RdpGuard::decide($eff, ['rdp','vpn','server1','carol'])['effect'] === 'allow', 'VPN 許可');

/* ── 相互運用: 引数で渡された JS 由来の root と一致するか (任意) ── */
if ($argc > 1) {
    $seed = $argv[1]; $expectRoot = $argv[2] ?? '';
    $t = RdpGuard::createTerminal('Interop', 4, RdpGuard::seedRng($seed));
    ok($t['root'] === $expectRoot, "相互運用: seed '$seed' の指紋が JS と一致 ($t[root])");
}

echo $failed === 0 ? "\nALL RDPGUARD PHP TESTS PASSED\n" : "\n$failed TEST(S) FAILED\n";
exit($failed === 0 ? 0 : 1);
