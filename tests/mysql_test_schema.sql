-- Minimal schema for P0.9 concurrency testing on MySQL 8.0
-- This creates only the tables needed for atomic stock reduction tests
-- No production data, no sensitive information

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(100) NOT NULL,
  cpf VARCHAR(14) NOT NULL UNIQUE,
  email VARCHAR(150) NULL UNIQUE,
  senha VARCHAR(255) NOT NULL,
  cargo VARCHAR(50) DEFAULT 'Voluntário',
  ativo BOOLEAN DEFAULT TRUE,
  senha_trocada BOOLEAN DEFAULT TRUE,
  credencial_versao INT DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS medicamento_referencia (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome_comercial VARCHAR(120) NOT NULL,
  registro_ms VARCHAR(30) NULL,
  principio_ativo VARCHAR(120) NULL,
  tarja VARCHAR(30) NOT NULL DEFAULT 'Sem Tarja',
  uso_continuo BOOLEAN DEFAULT FALSE,
  tipo_receita VARCHAR(60) NULL,
  lista_portaria VARCHAR(10) NULL,
  UNIQUE KEY uq_medicamentos_referencia_nome (nome_comercial)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS medicamentos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(100) NOT NULL,
  lote VARCHAR(50) NOT NULL,
  data_validade DATE NOT NULL,
  quantidade INT DEFAULT 0,
  status_semaforo INT DEFAULT 0,
  tarja VARCHAR(30) NOT NULL DEFAULT 'Sem Tarja',
  principio_ativo VARCHAR(120) NULL,
  uso_continuo BOOLEAN DEFAULT FALSE,
  referencia_id INT NULL,
  ativo BOOLEAN DEFAULT TRUE,
  controlado BOOLEAN DEFAULT FALSE,
  observacoes TEXT NULL,
  CONSTRAINT fk_medicamentos_referencia FOREIGN KEY (referencia_id) REFERENCES medicamento_referencia(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS medicos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(150) NOT NULL,
  crm VARCHAR(30) NOT NULL UNIQUE,
  especialidade VARCHAR(100) NOT NULL,
  contato VARCHAR(30) NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS pacientes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(150) NOT NULL,
  cpf VARCHAR(14) NOT NULL UNIQUE,
  data_nascimento DATE NOT NULL,
  endereco VARCHAR(255) NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS receitas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  paciente_id INT NOT NULL,
  medico_id INT NOT NULL,
  medicamento_id INT NULL,
  status VARCHAR(50) DEFAULT 'pendente',
  tipo_receita VARCHAR(50) NULL,
  data_prescricao DATE,
  dispensada_em DATETIME NULL,
  cancelado_em DATETIME NULL,
  cancelado_por_id INT NULL,
  CONSTRAINT fk_receitas_paciente FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE,
  CONSTRAINT fk_receitas_medico FOREIGN KEY (medico_id) REFERENCES medicos(id) ON DELETE CASCADE,
  CONSTRAINT fk_receitas_medicamento FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS doacoes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id INT NOT NULL,
  medicamento_id INT NOT NULL,
  quantidade INT NOT NULL,
  data_doacao DATETIME DEFAULT CURRENT_TIMESTAMP,
  peso_gramas FLOAT NULL,
  status_conferencia VARCHAR(50) DEFAULT 'APROVADO',
  cancelado BOOLEAN DEFAULT FALSE NOT NULL,
  cancelado_por_id INT NULL,
  cancelado_em DATETIME NULL,
  justificativa_cancelamento TEXT NULL,
  compensacao_id INT NULL,
  CONSTRAINT fk_doacoes_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
  CONSTRAINT fk_doacoes_medicamento FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id) ON DELETE CASCADE,
  CONSTRAINT fk_doacoes_cancelado_por FOREIGN KEY (cancelado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT fk_doacoes_compensacao FOREIGN KEY (compensacao_id) REFERENCES doacoes(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS qr_nonces (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nonce VARCHAR(64) NOT NULL UNIQUE,
  receita_id INT NOT NULL,
  gerado_por_id INT NULL,
  expira_em DATETIME NOT NULL,
  usado BOOLEAN DEFAULT FALSE NOT NULL,
  usado_em DATETIME NULL,
  usado_por_id INT NULL,
  criado_em DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
  CONSTRAINT fk_qr_nonces_receita FOREIGN KEY (receita_id) REFERENCES receitas(id) ON DELETE CASCADE,
  CONSTRAINT fk_qr_nonces_gerado_por FOREIGN KEY (gerado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT fk_qr_nonces_usado_por FOREIGN KEY (usado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS movimentos_estoque (
  id INT AUTO_INCREMENT PRIMARY KEY,
  medicamento_id INT NOT NULL,
  quantidade INT NOT NULL,
  tipo VARCHAR(50) NOT NULL,
  operacao_id VARCHAR(64) UNIQUE NULL,
  usuario_id INT NOT NULL,
  autorizado_por_id INT NULL,
  criado_em DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
  justificativa TEXT NULL,
  referencia_documento VARCHAR(100) NULL,
  CONSTRAINT fk_movimentos_medicamento FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id) ON DELETE CASCADE,
  CONSTRAINT fk_movimentos_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
  CONSTRAINT fk_movimentos_autorizado_por FOREIGN KEY (autorizado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS solicitacoes_estoque (
  id INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id INT NOT NULL,
  medicamento_id INT NOT NULL,
  lote VARCHAR(50) NOT NULL,
  quantidade_solicitada INT NOT NULL,
  quantidade_reservada INT NULL,
  quantidade_retirada INT NULL,
  estado VARCHAR(50) DEFAULT 'PENDENTE' NOT NULL,
  criado_em DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
  aprovado_em DATETIME NULL,
  reservado_em DATETIME NULL,
  retirado_em DATETIME NULL,
  cancelado_em DATETIME NULL,
  expira_em DATETIME NULL,
  aprovado_por_id INT NULL,
  reservado_por_id INT NULL,
  retirado_por_id INT NULL,
  cancelado_por_id INT NULL,
  justificativa TEXT NULL,
  justificativa_cancelamento TEXT NULL,
  CONSTRAINT fk_solicitacoes_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
  CONSTRAINT fk_solicitacoes_medicamento FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id) ON DELETE CASCADE,
  CONSTRAINT fk_solicitacoes_aprovado_por FOREIGN KEY (aprovado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT fk_solicitacoes_reservado_por FOREIGN KEY (reservado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT fk_solicitacoes_retirado_por FOREIGN KEY (retirado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT fk_solicitacoes_cancelado_por FOREIGN KEY (cancelado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
