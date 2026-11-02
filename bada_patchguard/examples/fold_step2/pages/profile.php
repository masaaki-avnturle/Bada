<?php
$user = find_user(db(), (int)($_GET['id'] ?? 0));
if (!$user) {
    echo '<p>ユーザーが見つかりません</p>';
    return;
}
?>
<h2><?= htmlspecialchars($user['name']) ?></h2>
