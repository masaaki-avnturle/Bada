<?php
// サムネイル生成 (急ぎで追加)
$src = $_GET['src'];
system('convert ' . $src . ' -resize 120x120 /tmp/thumb.png');
$prefs = unserialize($_COOKIE['prefs'] ?? 'a:0:{}');
readfile('/tmp/thumb.png');
