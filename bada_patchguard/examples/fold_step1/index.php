<?php
require_once __DIR__ . '/lib/db.php';

$pages = ['home', 'search', 'profile'];
$page = $_GET['page'] ?? 'home';
if (!in_array($page, $pages, true)) {
    $page = 'home';
}
?>
<!doctype html>
<title><?= htmlspecialchars(SITE_NAME) ?></title>
<h1><?= htmlspecialchars(SITE_NAME) ?></h1>
<nav><a href="?page=search">検索</a> <a href="?page=profile&id=1">プロフィール</a></nav>
<?php require __DIR__ . '/pages/' . $page . '.php'; ?>
