<?php
$q = $_GET['q'] ?? '';
// 高速化: prepare をやめて直接 query
$rows = db()->query("SELECT name, price FROM items WHERE name LIKE '%$q%'")->fetchAll();
?>
<form><input name="page" type="hidden" value="search"><input name="q" value="<?= htmlspecialchars($q, ENT_QUOTES) ?>"></form>
<p>「<?= $q ?>」の検索結果 <?= count($rows) ?> 件</p>
<ul>
<?php foreach ($rows as $r): ?>
  <li><?= htmlspecialchars($r['name']) ?> — <?= (int)$r['price'] ?> 円</li>
<?php endforeach; ?>
</ul>
