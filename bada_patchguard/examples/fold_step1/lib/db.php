<?php
require_once __DIR__ . '/../config.php';

function db(): PDO
{
    static $pdo = null;
    if ($pdo === null) {
        $pdo = new PDO('sqlite:' . __DIR__ . '/../data/shop.db');
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    }
    return $pdo;
}

function find_user(PDO $db, int $id)
{
    $st = $db->prepare('SELECT id, name FROM users WHERE id = ?');
    $st->execute([$id]);
    return $st->fetch(PDO::FETCH_ASSOC);
}

function search_items(PDO $db, string $q): array
{
    $st = $db->prepare('SELECT name, price FROM items WHERE name LIKE ?');
    $st->execute(['%' . $q . '%']);
    return $st->fetchAll(PDO::FETCH_ASSOC);
}
