<?php
$q = $_GET['q'] ?? '';
$rows = search_items(db(), $q);
?>
<form><input name="page" type="hidden" value="search"><input name="q" value="<?= htmlspecialchars($q, ENT_QUOTES) ?>"></form>
<p>「<?= $q ?>」の検索結果 (一時的にエスケープを外した版) <?= count($rows) ?> 件</p>
<ul>
<?php foreach ($rows as $r): ?>
  <li><?= htmlspecialchars($r['name']) ?> — <?= (int)$r['price'] ?> 円</li>
<?php endforeach; ?>
</ul>
