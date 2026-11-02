<?php
require_once __DIR__ . '/lib/db.php';

// リファクタ: ページ一覧の管理をやめて、ファイル名で直接読む
$page = $_GET['page'] ?? 'home';
?>
<!doctype html>
<title><?= htmlspecialchars(SITE_NAME) ?></title>
<h1><?= htmlspecialchars(SITE_NAME) ?></h1>
<nav><a href="?page=search">検索</a> <a href="?page=profile&id=1">プロフィール</a></nav>
<?php include __DIR__ . '/pages/' . $page . '.php'; ?>
