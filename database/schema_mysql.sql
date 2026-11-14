-- ============================================================
-- RedeVita - Schema do banco de dados (MySQL / MariaDB)
-- Gerado automaticamente a partir dos modelos ORM do projeto.
-- Compativel com MySQL 5.7+ / MariaDB 10.3+
-- Charset: utf8mb4 / Collation: utf8mb4_unicode_ci / Engine: InnoDB
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Tabela: farmacias
DROP TABLE IF EXISTS `farmacias`;
CREATE TABLE farmacias (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	nome_fantasia VARCHAR(150) NOT NULL, 
	razao_social VARCHAR(200), 
	cnpj VARCHAR(20) NOT NULL, 
	endereco VARCHAR(255) NOT NULL, 
	responsavel VARCHAR(150) NOT NULL, 
	latitude FLOAT, 
	longitude FLOAT, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (cnpj)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: instituicoes
DROP TABLE IF EXISTS `instituicoes`;
CREATE TABLE instituicoes (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	nome VARCHAR(200) NOT NULL, 
	cnpj VARCHAR(18), 
	endereco VARCHAR(300), 
	responsavel VARCHAR(100), 
	telefone VARCHAR(20), 
	email VARCHAR(150), 
	ativo BOOL NOT NULL, 
	criado_em DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (cnpj)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: lotes_telemetria
DROP TABLE IF EXISTS `lotes_telemetria`;
CREATE TABLE lotes_telemetria (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	lote_id VARCHAR(36) NOT NULL COMMENT 'UUID interno gerado no servidor', 
	data_recebimento DATETIME NOT NULL COMMENT 'Timestamp de recebimento no servidor (UTC)', 
	total_recebidas INTEGER NOT NULL COMMENT 'Total de leituras recebidas no lote', 
	total_processadas INTEGER NOT NULL COMMENT 'Total de leituras processadas com sucesso', 
	total_rejeitadas INTEGER NOT NULL COMMENT 'Total de leituras rejeitadas', 
	resultado ENUM('COMPLETO','PARCIAL','REJEITADO') NOT NULL COMMENT 'Resultado agregado do processamento', 
	qtd_dispositivos INTEGER NOT NULL COMMENT 'Quantidade de dispositivos distintos no lote', 
	dispositivo_principal VARCHAR(50) COMMENT 'ID do dispositivo quando há apenas um no lote (não autenticado)', 
	erros_por_categoria JSON COMMENT 'Categorias e quantidades de erros, sem mensagens brutas', 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: medicamentos_referencia
DROP TABLE IF EXISTS `medicamentos_referencia`;
CREATE TABLE medicamentos_referencia (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	nome_comercial VARCHAR(120) NOT NULL, 
	registro_ms VARCHAR(30), 
	principio_ativo VARCHAR(120), 
	tarja VARCHAR(30) NOT NULL, 
	uso_continuo BOOL, 
	tipo_receita VARCHAR(60), 
	lista_portaria VARCHAR(10), 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: medicos
DROP TABLE IF EXISTS `medicos`;
CREATE TABLE medicos (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	nome VARCHAR(150) NOT NULL, 
	crm VARCHAR(30) NOT NULL, 
	especialidade VARCHAR(100) NOT NULL, 
	contato VARCHAR(30), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (crm)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: pacientes
DROP TABLE IF EXISTS `pacientes`;
CREATE TABLE pacientes (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	nome VARCHAR(150) NOT NULL, 
	cpf VARCHAR(14) NOT NULL, 
	data_nascimento DATE NOT NULL, 
	endereco VARCHAR(255), 
	telefone VARCHAR(20), 
	email VARCHAR(150), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (cpf)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: leituras_iot
DROP TABLE IF EXISTS `leituras_iot`;
CREATE TABLE leituras_iot (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	dispositivo_id VARCHAR(50) NOT NULL COMMENT 'ID único do dispositivo ESP32/sensor', 
	farmacia_id INTEGER NOT NULL COMMENT 'ID da farmácia associada (OBRIGATÓRIO)', 
	temperatura FLOAT NOT NULL COMMENT 'Temperatura em °C', 
	umidade FLOAT NOT NULL COMMENT 'Umidade relativa em %%', 
	luminosidade_lux FLOAT COMMENT 'Luminosidade em lux (fotodegradação)', 
	status_alerta ENUM('NORMAL','ALERTA_LEVE','CRITICO_TERMICO') NOT NULL COMMENT 'Status conforme regras ANVISA', 
	data_hora DATETIME NOT NULL COMMENT 'Timestamp da leitura', 
	PRIMARY KEY (id), 
	FOREIGN KEY(farmacia_id) REFERENCES farmacias (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: medicamentos
DROP TABLE IF EXISTS `medicamentos`;
CREATE TABLE medicamentos (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	nome VARCHAR(100) NOT NULL, 
	lote VARCHAR(50) NOT NULL, 
	data_validade DATE NOT NULL, 
	quantidade INTEGER, 
	status_semaforo INTEGER, 
	ativo BOOL NOT NULL, 
	tarja VARCHAR(30) NOT NULL, 
	principio_ativo VARCHAR(120), 
	uso_continuo BOOL, 
	referencia_id INTEGER, 
	observacoes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(referencia_id) REFERENCES medicamentos_referencia (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: usuarios
DROP TABLE IF EXISTS `usuarios`;
CREATE TABLE usuarios (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	nome VARCHAR(100) NOT NULL, 
	cpf VARCHAR(14) NOT NULL, 
	email VARCHAR(150), 
	senha VARCHAR(255) NOT NULL, 
	cargo VARCHAR(50), 
	ativo BOOL, 
	senha_trocada BOOL NOT NULL, 
	credencial_versao INTEGER NOT NULL, 
	farmacia_id INTEGER, 
	instituicao_id INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (cpf), 
	UNIQUE (email), 
	FOREIGN KEY(farmacia_id) REFERENCES farmacias (id), 
	FOREIGN KEY(instituicao_id) REFERENCES instituicoes (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: agendamentos_entrega
DROP TABLE IF EXISTS `agendamentos_entrega`;
CREATE TABLE agendamentos_entrega (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	farmacia_origem_id INTEGER NOT NULL, 
	farmacia_destino_id INTEGER NOT NULL, 
	data_hora_inicio DATETIME NOT NULL, 
	data_hora_fim DATETIME NOT NULL, 
	estado VARCHAR(50) NOT NULL, 
	criado_por_id INTEGER NOT NULL, 
	criado_em DATETIME NOT NULL, 
	confirmado_origem_por_id INTEGER, 
	confirmado_origem_em DATETIME, 
	confirmado_destino_por_id INTEGER, 
	confirmado_destino_em DATETIME, 
	cancelado_por_id INTEGER, 
	cancelado_em DATETIME, 
	motivo_cancelamento TEXT, 
	observacoes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(farmacia_origem_id) REFERENCES farmacias (id), 
	FOREIGN KEY(farmacia_destino_id) REFERENCES farmacias (id), 
	FOREIGN KEY(criado_por_id) REFERENCES usuarios (id), 
	FOREIGN KEY(confirmado_origem_por_id) REFERENCES usuarios (id), 
	FOREIGN KEY(confirmado_destino_por_id) REFERENCES usuarios (id), 
	FOREIGN KEY(cancelado_por_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: campanhas
DROP TABLE IF EXISTS `campanhas`;
CREATE TABLE campanhas (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	titulo VARCHAR(200) NOT NULL, 
	descricao TEXT NOT NULL, 
	tipo VARCHAR(50) NOT NULL, 
	data_inicio DATE NOT NULL, 
	data_fim DATE, 
	status VARCHAR(20), 
	criador_id INTEGER, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(criador_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: contagens_estoque
DROP TABLE IF EXISTS `contagens_estoque`;
CREATE TABLE contagens_estoque (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	medicamento_id INTEGER NOT NULL, 
	lote VARCHAR(50) NOT NULL, 
	quantidade_fisica INTEGER NOT NULL, 
	quantidade_sistema INTEGER NOT NULL, 
	divergencia INTEGER NOT NULL, 
	usuario_id INTEGER NOT NULL, 
	autorizado_por_id INTEGER, 
	criado_em DATETIME NOT NULL, 
	finalizada_em DATETIME, 
	estado VARCHAR(20) NOT NULL, 
	ajuste_realizado BOOL NOT NULL, 
	ajuste_realizado_por_id INTEGER, 
	ajuste_realizado_em DATETIME, 
	justificativa_ajuste TEXT, 
	observacoes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(medicamento_id) REFERENCES medicamentos (id), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id), 
	FOREIGN KEY(autorizado_por_id) REFERENCES usuarios (id), 
	FOREIGN KEY(ajuste_realizado_por_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: doacoes
DROP TABLE IF EXISTS `doacoes`;
CREATE TABLE doacoes (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	usuario_id INTEGER NOT NULL, 
	medicamento_id INTEGER NOT NULL, 
	data_doacao DATETIME, 
	quantidade INTEGER NOT NULL, 
	peso_gramas FLOAT COMMENT 'Peso em gramas da doação (referência)', 
	status_conferencia VARCHAR(50) COMMENT 'Status da conferência: APROVADO, PENDENTE_CONFERENCIA_MANUAL', 
	cancelado BOOL NOT NULL, 
	cancelado_por_id INTEGER, 
	cancelado_em DATETIME, 
	justificativa_cancelamento TEXT, 
	compensacao_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id), 
	FOREIGN KEY(medicamento_id) REFERENCES medicamentos (id), 
	FOREIGN KEY(cancelado_por_id) REFERENCES usuarios (id), 
	FOREIGN KEY(compensacao_id) REFERENCES doacoes (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: logs_atividade
DROP TABLE IF EXISTS `logs_atividade`;
CREATE TABLE logs_atividade (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	usuario_id INTEGER, 
	acao VARCHAR(100) NOT NULL, 
	detalhes VARCHAR(500), 
	ip VARCHAR(45), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: movimentos_estoque
DROP TABLE IF EXISTS `movimentos_estoque`;
CREATE TABLE movimentos_estoque (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	medicamento_id INTEGER NOT NULL, 
	quantidade INTEGER NOT NULL, 
	tipo VARCHAR(50) NOT NULL, 
	operacao_id VARCHAR(64), 
	usuario_id INTEGER NOT NULL, 
	autorizado_por_id INTEGER, 
	criado_em DATETIME NOT NULL, 
	justificativa TEXT, 
	referencia_documento VARCHAR(100), 
	PRIMARY KEY (id), 
	FOREIGN KEY(medicamento_id) REFERENCES medicamentos (id), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id), 
	FOREIGN KEY(autorizado_por_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: necessidades_institucionais
DROP TABLE IF EXISTS `necessidades_institucionais`;
CREATE TABLE necessidades_institucionais (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	instituicao_id INTEGER, 
	nome_instituicao VARCHAR(200), 
	medicamento_referencia_id INTEGER, 
	produto_descritivo VARCHAR(200), 
	quantidade_solicitada INTEGER NOT NULL, 
	unidade VARCHAR(20) NOT NULL, 
	data_desejada DATE, 
	prioridade VARCHAR(20) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	criado_por_id INTEGER NOT NULL, 
	criado_em DATETIME NOT NULL, 
	revisado_por_id INTEGER, 
	revisado_em DATETIME, 
	encerrado_por_id INTEGER, 
	encerrado_em DATETIME, 
	observacoes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(instituicao_id) REFERENCES instituicoes (id), 
	FOREIGN KEY(medicamento_referencia_id) REFERENCES medicamentos_referencia (id), 
	FOREIGN KEY(criado_por_id) REFERENCES usuarios (id), 
	FOREIGN KEY(revisado_por_id) REFERENCES usuarios (id), 
	FOREIGN KEY(encerrado_por_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: ofertas_medicamentos
DROP TABLE IF EXISTS `ofertas_medicamentos`;
CREATE TABLE ofertas_medicamentos (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	farmacia_id INTEGER NOT NULL, 
	medicamento_id INTEGER NOT NULL, 
	quantidade_ofertada INTEGER NOT NULL, 
	quantidade_reservada INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	data_expiracao DATETIME, 
	criado_por_id INTEGER NOT NULL, 
	criado_em DATETIME NOT NULL, 
	atualizado_em DATETIME NOT NULL, 
	observacoes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(farmacia_id) REFERENCES farmacias (id), 
	FOREIGN KEY(medicamento_id) REFERENCES medicamentos (id), 
	FOREIGN KEY(criado_por_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: receitas
DROP TABLE IF EXISTS `receitas`;
CREATE TABLE receitas (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	paciente_id INTEGER NOT NULL, 
	medico_id INTEGER NOT NULL, 
	medicamento_id INTEGER, 
	observacoes TEXT, 
	data_emissao DATETIME, 
	tipo_receita VARCHAR(60), 
	imagem_url VARCHAR(255), 
	status VARCHAR(20) NOT NULL, 
	dispensada_em DATETIME, 
	dispensada_por_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(paciente_id) REFERENCES pacientes (id), 
	FOREIGN KEY(medico_id) REFERENCES medicos (id), 
	FOREIGN KEY(medicamento_id) REFERENCES medicamentos (id), 
	FOREIGN KEY(dispensada_por_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: recuperacoes_senha
DROP TABLE IF EXISTS `recuperacoes_senha`;
CREATE TABLE recuperacoes_senha (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	usuario_id INTEGER NOT NULL, 
	token VARCHAR(64) NOT NULL, 
	token_hash VARCHAR(64) NOT NULL, 
	expira_em DATETIME NOT NULL, 
	usado_em DATETIME, 
	tentativas INTEGER NOT NULL, 
	max_tentativas INTEGER NOT NULL, 
	criado_em DATETIME NOT NULL, 
	ip_origem VARCHAR(45), 
	PRIMARY KEY (id), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: solicitacoes_estoque
DROP TABLE IF EXISTS `solicitacoes_estoque`;
CREATE TABLE solicitacoes_estoque (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	usuario_id INTEGER NOT NULL, 
	medicamento_id INTEGER NOT NULL, 
	lote VARCHAR(50) NOT NULL, 
	quantidade_solicitada INTEGER NOT NULL, 
	quantidade_reservada INTEGER, 
	quantidade_retirada INTEGER, 
	estado VARCHAR(50) NOT NULL, 
	criado_em DATETIME NOT NULL, 
	aprovado_em DATETIME, 
	reservado_em DATETIME, 
	retirado_em DATETIME, 
	cancelado_em DATETIME, 
	expira_em DATETIME, 
	aprovado_por_id INTEGER, 
	reservado_por_id INTEGER, 
	retirado_por_id INTEGER, 
	cancelado_por_id INTEGER, 
	justificativa TEXT, 
	justificativa_cancelamento TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id), 
	FOREIGN KEY(medicamento_id) REFERENCES medicamentos (id), 
	FOREIGN KEY(aprovado_por_id) REFERENCES usuarios (id), 
	FOREIGN KEY(reservado_por_id) REFERENCES usuarios (id), 
	FOREIGN KEY(retirado_por_id) REFERENCES usuarios (id), 
	FOREIGN KEY(cancelado_por_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: tags_rfid
DROP TABLE IF EXISTS `tags_rfid`;
CREATE TABLE tags_rfid (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	tag_uid VARCHAR(64) NOT NULL COMMENT 'Hash SHA-256 da tag física', 
	usuario_id INTEGER NOT NULL COMMENT 'ID do usuário associado', 
	descricao VARCHAR(100) COMMENT 'Descrição da tag (ex: Crachá Farmacêutico)', 
	ativo BOOL NOT NULL COMMENT 'Se a tag está ativa para uso', 
	data_cadastro DATETIME NOT NULL COMMENT 'Data de cadastro da tag', 
	ultimo_acesso DATETIME COMMENT 'Último acesso autorizado', 
	PRIMARY KEY (id), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: doacoes_etapas
DROP TABLE IF EXISTS `doacoes_etapas`;
CREATE TABLE doacoes_etapas (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	doacao_id INTEGER NOT NULL, 
	tipo_etapa VARCHAR(50) NOT NULL COMMENT 'Tipo da etapa (enum TipoEtapa)', 
	data_hora DATETIME NOT NULL COMMENT 'Data/hora do evento em UTC', 
	usuario_id INTEGER COMMENT 'Usuário responsável (null para eventos automáticos)', 
	origem VARCHAR(20) NOT NULL COMMENT 'Origem do evento (enum OrigemEvento)', 
	observacao TEXT COMMENT 'Observação opcional sobre a etapa', 
	criado_em DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(doacao_id) REFERENCES doacoes (id), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: qr_nonces
DROP TABLE IF EXISTS `qr_nonces`;
CREATE TABLE qr_nonces (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	nonce VARCHAR(64) NOT NULL, 
	receita_id INTEGER NOT NULL, 
	gerado_por_id INTEGER, 
	expira_em DATETIME NOT NULL, 
	usado BOOL NOT NULL, 
	usado_em DATETIME, 
	usado_por_id INTEGER, 
	criado_em DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(receita_id) REFERENCES receitas (id), 
	FOREIGN KEY(gerado_por_id) REFERENCES usuarios (id), 
	FOREIGN KEY(usado_por_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: reservas_ofertas
DROP TABLE IF EXISTS `reservas_ofertas`;
CREATE TABLE reservas_ofertas (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	oferta_id INTEGER NOT NULL, 
	instituicao_id INTEGER NOT NULL, 
	quantidade_reservada INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	reservado_por_id INTEGER NOT NULL, 
	confirmado_por_id INTEGER, 
	criado_em DATETIME NOT NULL, 
	atualizado_em DATETIME NOT NULL, 
	confirmado_em DATETIME, 
	data_expiracao DATETIME, 
	observacoes TEXT, 
	operacao_id VARCHAR(64), 
	PRIMARY KEY (id), 
	FOREIGN KEY(oferta_id) REFERENCES ofertas_medicamentos (id), 
	FOREIGN KEY(instituicao_id) REFERENCES instituicoes (id), 
	FOREIGN KEY(reservado_por_id) REFERENCES usuarios (id), 
	FOREIGN KEY(confirmado_por_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: aprovacoes_farmaceuticas
DROP TABLE IF EXISTS `aprovacoes_farmaceuticas`;
CREATE TABLE aprovacoes_farmaceuticas (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	reserva_id INTEGER NOT NULL, 
	usuario_id INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	observacoes TEXT, 
	criado_em DATETIME NOT NULL, 
	operacao_id VARCHAR(64), 
	PRIMARY KEY (id), 
	UNIQUE (reserva_id), 
	FOREIGN KEY(reserva_id) REFERENCES reservas_ofertas (id), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: entregas_institucionais
DROP TABLE IF EXISTS `entregas_institucionais`;
CREATE TABLE entregas_institucionais (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	reserva_id INTEGER NOT NULL, 
	estado VARCHAR(20) NOT NULL, 
	despachado_por_id INTEGER, 
	despachado_em DATETIME, 
	recebido_por_id INTEGER, 
	recebido_em DATETIME, 
	observacoes TEXT, 
	operacao_id VARCHAR(64), 
	criado_em DATETIME NOT NULL, 
	atualizado_em DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (reserva_id), 
	FOREIGN KEY(reserva_id) REFERENCES reservas_ofertas (id), 
	FOREIGN KEY(despachado_por_id) REFERENCES usuarios (id), 
	FOREIGN KEY(recebido_por_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: receitas_anexos
DROP TABLE IF EXISTS `receitas_anexos`;
CREATE TABLE receitas_anexos (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	reserva_id INTEGER NOT NULL, 
	nome_arquivo_original VARCHAR(255) NOT NULL, 
	nome_arquivo_interno VARCHAR(255) NOT NULL, 
	caminho_arquivo VARCHAR(512) NOT NULL, 
	tamanho_bytes INTEGER NOT NULL, 
	tipo_mime VARCHAR(100) NOT NULL, 
	validado BOOL NOT NULL, 
	uploadado_por_id INTEGER NOT NULL, 
	uploadado_em DATETIME NOT NULL, 
	observacoes TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (reserva_id), 
	FOREIGN KEY(reserva_id) REFERENCES reservas_ofertas (id), 
	UNIQUE (nome_arquivo_interno), 
	FOREIGN KEY(uploadado_por_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
-- Total de tabelas: 27