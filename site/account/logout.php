<?php
require __DIR__ . '/../app/bootstrap.php';
logout_user();
header('Location: /');
