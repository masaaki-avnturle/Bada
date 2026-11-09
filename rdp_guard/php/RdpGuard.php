<?php
/*
 * RdpGuard.php — Bada RDP Guard コア (PHP 版, core/rdpguard.js と相互運用)
 *
 * RDP の「なりすまし・乗っ取り」を防ぐ防御用の、端末間 相互デジタル署名認証。
 * ハッシュの不可逆性のみに依存する Lamport 一回署名 + Merkle 署名方式。
 * SHA-256・seedRng・Merkle の組み方は JS 版と同一なので、同じ seed から
 * 同じ指紋 (root) と署名が得られます (相互運用テストで検証)。
 *
 * ※ 防御の概念実装です。実 RDP パケットは操作せず、RDP ゲートウェイが接続前に
 *   verifyTerminalSig() を呼ぶ想定の参照実装です。
 */
final class RdpGuard
{
    const N = 256;          // メッセージダイジェストのビット数
    const LEN = 32;         // 原像/ハッシュのバイト長

    public static function sha256(string $bytes): string { return hash('sha256', $bytes, true); }   // 生バイナリ32
    public static function hashHex(string $bytes): string { return hash('sha256', $bytes); }
    public static function toHex(string $bytes): string { return bin2hex($bytes); }
    public static function fromHex(string $hex): string { return hex2bin($hex); }

    /* 決定論的 RNG: seed から SHA-256 カウンタ列 (JS seedRng と同一) */
    public static function seedRng(string $seed): callable
    {
        $ctr = 0;
        return function (int $n) use (&$ctr, $seed): string {
            $out = '';
            while (strlen($out) < $n) { $out .= hash('sha256', $seed . '|' . ($ctr++), true); }
            return substr($out, 0, $n);
        };
    }
    public static function secureRng(): callable
    {
        return function (int $n): string { return random_bytes($n); };
    }

    private static function bit(string $digest, int $i): int
    {
        return (ord($digest[$i >> 3]) >> (7 - ($i & 7))) & 1;
    }

    /* ── Lamport 一回署名 ── */
    public static function lamportKeygen(callable $rng): array
    {
        $priv = []; $pub = [];
        for ($i = 0; $i < self::N; $i++) {
            $p0 = $rng(self::LEN); $p1 = $rng(self::LEN);
            $priv[$i] = [bin2hex($p0), bin2hex($p1)];
            $pub[$i]  = [hash('sha256', $p0), hash('sha256', $p1)];
        }
        return ['priv' => $priv, 'pub' => $pub];
    }
    public static function lamportSign(string $digest, array $priv): array
    {
        $sig = [];
        for ($i = 0; $i < self::N; $i++) { $sig[$i] = $priv[$i][self::bit($digest, $i)]; }
        return $sig;
    }
    public static function lamportVerify(string $digest, array $sig, array $pub): bool
    {
        if (count($sig) !== self::N) return false;
        for ($i = 0; $i < self::N; $i++) {
            $b = self::bit($digest, $i);
            if (hash('sha256', hex2bin($sig[$i])) !== $pub[$i][$b]) return false;
        }
        return true;
    }
    public static function lamportPubHash(array $pub): string
    {
        $s = '';
        for ($i = 0; $i < self::N; $i++) { $s .= $pub[$i][0] . $pub[$i][1]; }
        return hash('sha256', $s);
    }

    /* ── Merkle 木 ── */
    public static function merkleBuild(array $leafHashes): array
    {
        $levels = [array_values($leafHashes)];
        $cur = array_values($leafHashes);
        while (count($cur) > 1) {
            if (count($cur) % 2 === 1) { $cur[] = $cur[count($cur) - 1]; }
            $next = [];
            for ($i = 0; $i < count($cur); $i += 2) { $next[] = hash('sha256', $cur[$i] . $cur[$i + 1]); }
            $levels[] = $next; $cur = $next;
        }
        return ['root' => $cur[0], 'levels' => $levels];
    }
    public static function merkleRoot(array $leafHashes): string { return self::merkleBuild($leafHashes)['root']; }
    public static function merklePath(array $leafHashes, int $index): array
    {
        $built = self::merkleBuild($leafHashes); $path = []; $idx = $index;
        for ($lv = 0; $lv < count($built['levels']) - 1; $lv++) {
            $level = $built['levels'][$lv];
            $sib = ($idx % 2 === 0) ? $idx + 1 : $idx - 1;
            if ($sib >= count($level)) $sib = $idx;
            $path[] = ['hash' => $level[$sib], 'right' => ($idx % 2 === 0)];
            $idx = $idx >> 1;
        }
        return $path;
    }
    public static function merkleVerify(string $leafHash, array $path, string $root): bool
    {
        $h = $leafHash;
        foreach ($path as $p) {
            $h = $p['right'] ? hash('sha256', $h . $p['hash']) : hash('sha256', $p['hash'] . $h);
        }
        return $h === $root;
    }

    /* ── 端末 (Merkle 署名方式の鍵一式) ── */
    public static function createTerminal(string $name, int $nLeaves = 4, ?callable $rng = null): array
    {
        $rng = $rng ?? self::secureRng();
        $leaves = []; $keys = [];
        for ($i = 0; $i < $nLeaves; $i++) {
            $kp = self::lamportKeygen($rng);
            $keys[] = $kp; $leaves[] = self::lamportPubHash($kp['pub']);
        }
        $root = self::merkleRoot($leaves);
        return ['name' => $name, 'root' => $root, 'fingerprint' => substr($root, 0, 16),
                '_keys' => $keys, '_leaves' => $leaves, 'nLeaves' => $nLeaves, 'used' => 0];
    }
    public static function signChallenge(array &$term, string $challenge): array
    {
        if ($term['used'] >= $term['nLeaves']) return ['error' => '鍵の葉を使い切りました (再鍵が必要)'];
        $idx = $term['used']++;
        $digest = self::sha256($challenge);
        $kp = $term['_keys'][$idx];
        return ['leaf' => $idx, 'pub' => $kp['pub'], 'sig' => self::lamportSign($digest, $kp['priv']),
                'path' => self::merklePath($term['_leaves'], $idx)];
    }
    public static function verifyTerminalSig(string $fingerprintRoot, string $challenge, $s): bool
    {
        if (!is_array($s) || isset($s['error'])) return false;
        $digest = self::sha256($challenge);
        if (!self::lamportVerify($digest, $s['sig'], $s['pub'])) return false;
        return self::merkleVerify(self::lamportPubHash($s['pub']), $s['path'], $fingerprintRoot);
    }

    /* ── 相互認証ハンドシェイク ── */
    public static function mutualHandshake(array &$a, array &$b, array $opts = []): array
    {
        $sid = $opts['sessionId'] ?? bin2hex(random_bytes(8));
        $nonceA = $opts['nonceA'] ?? bin2hex(random_bytes(16));
        $nonceB = $opts['nonceB'] ?? bin2hex(random_bytes(16));
        $chalAtoB = "RDPGUARD1|$sid|{$a['name']}>{$b['name']}|$nonceB";
        $chalBtoA = "RDPGUARD1|$sid|{$b['name']}>{$a['name']}|$nonceA";
        $sigA = self::signChallenge($a, $chalAtoB);
        $sigB = self::signChallenge($b, $chalBtoA);
        $aOk = self::verifyTerminalSig($a['root'], $chalAtoB, $sigA);
        $bOk = self::verifyTerminalSig($b['root'], $chalBtoA, $sigB);
        return ['ok' => $aOk && $bOk, 'sessionId' => $sid, 'nonceA' => $nonceA, 'nonceB' => $nonceB,
                'aVerified' => $aOk, 'bVerified' => $bOk,
                'message' => ($aOk && $bOk) ? '相互認証成功 — RDP セッションを許可' : '相互認証失敗 — RDP 接続を拒否'];
    }

    /* ── Reviser: tuple-network 辞書式順序のポリシー・パッチ ── */
    public static function tupleKey(array $tuple): string
    {
        return implode("\u{241f}", array_map('strval', $tuple));
    }
    public static function revise(array $baseRules, array $patchSets): array
    {
        $all = [];
        foreach ($baseRules as $i => $r) { $all[] = self::normRule($r, 'base', $i); }
        foreach ($patchSets as $patch) {
            $pid = $patch['id'] ?? 'patch';
            foreach (($patch['rules'] ?? []) as $i => $r) { $all[] = self::normRule($r, $pid, $i); }
        }
        usort($all, function ($x, $y) {
            if ($x['key'] !== $y['key']) return $x['key'] < $y['key'] ? -1 : 1;
            return $x['seq'] <=> $y['seq'];
        });
        $map = [];
        foreach ($all as $r) { $map[$r['key']] = $r; }
        ksort($map);
        return array_values($map);
    }
    public static function decide(array $effective, array $conn): array
    {
        $connKey = array_map('strval', $conn);
        $best = null; $bestLen = -1;
        foreach ($effective as $r) {
            $t = $r['tuple']; if (count($t) > count($connKey)) continue;
            $okm = true;
            for ($j = 0; $j < count($t); $j++) {
                if ((string)$t[$j] !== '*' && (string)$t[$j] !== $connKey[$j]) { $okm = false; break; }
            }
            if ($okm && count($t) > $bestLen) { $best = $r; $bestLen = count($t); }
        }
        return ['effect' => $best ? $best['effect'] : 'deny', 'rule' => $best, 'matched' => $best !== null];
    }
    private static function normRule(array $r, string $src, int $i): array
    {
        return ['tuple' => $r['tuple'], 'key' => self::tupleKey($r['tuple']),
                'effect' => (($r['effect'] ?? 'deny') === 'allow') ? 'allow' : 'deny',
                'note' => $r['note'] ?? '', 'source' => $src, 'seq' => $r['seq'] ?? $i];
    }
}
