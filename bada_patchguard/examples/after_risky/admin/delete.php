<?php
require_once __DIR__ . '/../lib/db.php';
require_once __DIR__ . '/../lib/auth.php';

require_login();

$id = (int)($_POST['id'] ?? 0);
$st = db()->prepare('DELETE FROM items WHERE id = ?');
$st->execute([$id]);
header('Location: /admin/');
