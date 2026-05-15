-- Execute este script no MySQL Workbench antes de iniciar o RedeVita
-- Menu: File > Open SQL Script > selecione este arquivo > Execute (raio)

-- Cria o banco de dados caso não exista
CREATE DATABASE IF NOT EXISTS redevita
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Seleciona o banco
USE redevita;

-- Garante privilégios ao usuário root (já tem por padrão)
-- Se quiser um usuário dedicado (recomendado em produção), descomente:
-- CREATE USER IF NOT EXISTS 'redevita_user'@'localhost' IDENTIFIED BY 'sua_senha';
-- GRANT ALL PRIVILEGES ON redevita.* TO 'redevita_user'@'localhost';
-- FLUSH PRIVILEGES;

-- As tabelas são criadas automaticamente pelo Flask ao iniciar.
-- Basta executar este script e depois rodar: iniciar.bat

SELECT 'Banco redevita criado com sucesso!' AS status;
