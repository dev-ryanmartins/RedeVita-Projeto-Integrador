// RedeVita Database Store - SQLite Persistence (node:sqlite)
const path = require('path');
const { DatabaseSync } = require('node:sqlite');

const dbPath = path.join(__dirname, 'redevita.db');
const sqlite = new DatabaseSync(dbPath);

sqlite.exec('PRAGMA foreign_keys = ON;');
sqlite.exec('PRAGMA journal_mode = WAL;');

// 1. Inicialização de Tabelas no SQLite
sqlite.exec(`
  CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT UNIQUE NOT NULL,
    email TEXT,
    senha TEXT NOT NULL,
    cargo TEXT DEFAULT 'Voluntário',
    ativo INTEGER DEFAULT 1
  );

  CREATE TABLE IF NOT EXISTS medicamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    lote TEXT NOT NULL,
    data_validade TEXT NOT NULL,
    quantidade INTEGER DEFAULT 0,
    tarja TEXT DEFAULT 'Sem Tarja',
    principio_ativo TEXT DEFAULT '',
    status_semaforo INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS doacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doador TEXT NOT NULL,
    medicamento TEXT NOT NULL,
    quantidade INTEGER DEFAULT 1,
    data_doacao TEXT,
    status TEXT DEFAULT 'Pendente',
    observacoes TEXT,
    responsavel TEXT
  );

  CREATE TABLE IF NOT EXISTS pacientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT NOT NULL,
    nascimento TEXT,
    endereco TEXT,
    contato TEXT
  );

  CREATE TABLE IF NOT EXISTS medicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    crm TEXT NOT NULL,
    especialidade TEXT,
    contato TEXT,
    email TEXT
  );

  CREATE TABLE IF NOT EXISTS farmacias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_fantasia TEXT NOT NULL,
    razao_social TEXT,
    cnpj TEXT,
    endereco TEXT,
    responsavel TEXT,
    telefone TEXT,
    horario TEXT,
    lat REAL,
    lng REAL
  );

  CREATE TABLE IF NOT EXISTS receitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_nome TEXT NOT NULL,
    medico_nome TEXT NOT NULL,
    medicamento_nome TEXT NOT NULL,
    tipo TEXT,
    data_emissao TEXT,
    status TEXT DEFAULT 'ativa',
    dispensada_por TEXT,
    observacoes TEXT
  );

  CREATE TABLE IF NOT EXISTS iot_dispositivos (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    local TEXT,
    temperatura REAL,
    tempMin REAL,
    tempMax REAL,
    umidade INTEGER,
    bateria INTEGER,
    status TEXT,
    ultimaLeitura TEXT
  );

  CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL,
    acao TEXT NOT NULL,
    detalhes TEXT,
    data_hora TEXT,
    ip TEXT
  );

  CREATE TABLE IF NOT EXISTS movimentacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicamento_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    motivo TEXT,
    observacoes TEXT,
    responsavel TEXT,
    data_hora TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id) ON DELETE CASCADE
  );
`);

// Funções Utilitárias de Data e Semáforo
function calcularStatusSemaforo(validadeStr) {
  if (!validadeStr) return 0;
  const validade = new Date(validadeStr);
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  const diffTime = validade.getTime() - hoje.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  if (diffDays <= 0) return 2; // Vencido
  if (diffDays <= 30) return 1; // Alerta
  return 0; // Seguro
}

function formatDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function addDays(days) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return formatDate(d);
}

// 2. População Inicial de Dados (Seed Data no SQLite caso a base esteja vazia)
function semearBanco() {
  const countUsuarios = sqlite.prepare('SELECT COUNT(*) as count FROM usuarios').get().count;
  if (countUsuarios === 0) {
    const seedUsuarios = [
      { id: 1, nome: 'Administrador RedeVita', cpf: '00000000000', email: 'admin@redevita.local', senha: 'admin123', cargo: 'Admin', ativo: 1 },
      { id: 2, nome: 'Ana Clara Voluntária', cpf: '22244466671', email: 'voluntario.demo@redevita.local', senha: 'demo1234', cargo: 'Voluntário', ativo: 1 },
      { id: 3, nome: 'Marina Souza Farmacêutica', cpf: '33355577782', email: 'farmaceutico.demo@redevita.local', senha: 'demo1234', cargo: 'Farmacêutico', ativo: 1 },
      { id: 4, nome: 'Dr. Rafael Almeida', cpf: '44466688893', email: 'medico.demo@redevita.local', senha: 'demo1234', cargo: 'Médico', ativo: 1 },
      { id: 5, nome: 'Carlos Eduardo Silveira', cpf: '55577799904', email: 'carlos@redevita.local', senha: 'demo1234', cargo: 'Farmacêutico', ativo: 1 }
    ];
    const stmt = sqlite.prepare('INSERT INTO usuarios (id, nome, cpf, email, senha, cargo, ativo) VALUES (?, ?, ?, ?, ?, ?, ?)');
    for (const u of seedUsuarios) {
      stmt.run(u.id, u.nome, u.cpf, u.email, u.senha, u.cargo, u.ativo);
    }
  }

  const countMedicamentos = sqlite.prepare('SELECT COUNT(*) as count FROM medicamentos').get().count;
  if (countMedicamentos === 0) {
    const seedMedicamentos = [
      { id: 1, nome: 'Dipirona Sódica 500mg/mL', lote: 'DIP-2024-01', data_validade: addDays(180), quantidade: 450, tarja: 'Sem Tarja', principio_ativo: 'Dipirona Sódica' },
      { id: 2, nome: 'Paracetamol 750mg', lote: 'PAR-2024-02', data_validade: addDays(120), quantidade: 320, tarja: 'Sem Tarja', principio_ativo: 'Paracetamol' },
      { id: 3, nome: 'Amoxicilina + Clavulanato 500mg+125mg', lote: 'AMX-2024-03', data_validade: addDays(25), quantidade: 180, tarja: 'Tarja Vermelha', principio_ativo: 'Amoxicilina Tri-hidratada + Clavulanato de Potássio' },
      { id: 4, nome: 'Losartana Potássica 50mg', lote: 'LOS-2024-04', data_validade: addDays(365), quantidade: 600, tarja: 'Tarja Vermelha', principio_ativo: 'Losartana Potássica' },
      { id: 5, nome: 'Hidroclorotiazida 25mg', lote: 'HCT-2024-05', data_validade: addDays(200), quantidade: 290, tarja: 'Tarja Vermelha', principio_ativo: 'Hidroclorotiazida' },
      { id: 6, nome: 'Metformina 850mg', lote: 'MET-2024-06', data_validade: addDays(-5), quantidade: 40, tarja: 'Tarja Vermelha', principio_ativo: 'Cloridrato de Metformina' },
      { id: 7, nome: 'Omeprazol 20mg', lote: 'OME-2024-07', data_validade: addDays(15), quantidade: 210, tarja: 'Tarja Vermelha', principio_ativo: 'Omeprazol' },
      { id: 8, nome: 'Sinvastatina 20mg', lote: 'SIN-2024-08', data_validade: addDays(300), quantidade: 195, tarja: 'Tarja Vermelha', principio_ativo: 'Sinvastatina' },
      { id: 9, nome: 'Atenolol 50mg', lote: 'ATE-2024-09', data_validade: addDays(400), quantidade: 310, tarja: 'Tarja Vermelha', principio_ativo: 'Atenolol' },
      { id: 10, nome: 'Clonazepam 2mg', lote: 'CNZ-2024-10', data_validade: addDays(90), quantidade: 85, tarja: 'Portaria 344', principio_ativo: 'Clonazepam' },
      { id: 11, nome: 'Insulina NPH 100UI/mL', lote: 'INS-2024-11', data_validade: addDays(45), quantidade: 60, tarja: 'Tarja Vermelha', principio_ativo: 'Insulina Humana' }
    ];
    const stmt = sqlite.prepare('INSERT INTO medicamentos (id, nome, lote, data_validade, quantidade, tarja, principio_ativo, status_semaforo) VALUES (?, ?, ?, ?, ?, ?, ?, ?)');
    for (const m of seedMedicamentos) {
      stmt.run(m.id, m.nome, m.lote, m.data_validade, m.quantidade, m.tarja, m.principio_ativo, calcularStatusSemaforo(m.data_validade));
    }
  }

  const countDoacoes = sqlite.prepare('SELECT COUNT(*) as count FROM doacoes').get().count;
  if (countDoacoes === 0) {
    const seedDoacoes = [
      { id: 1, doador: 'Hospital Santa Lucinda', medicamento: 'Amoxicilina 500mg', quantidade: 50, data_doacao: addDays(-2), status: 'Aprovada', observacoes: 'Lote lacrado original em boas condições', responsavel: 'Marina Souza' },
      { id: 2, doador: 'Drogaria São Paulo - Unidade Campolim', medicamento: 'Dipirona 500mg', quantidade: 100, data_doacao: addDays(-5), status: 'Aprovada', observacoes: 'Validade acima de 6 meses', responsavel: 'Ana Clara' },
      { id: 3, doador: 'Fernanda Oliveira Rocha', medicamento: 'Ibuprofeno 600mg', quantidade: 20, data_doacao: addDays(-1), status: 'Em Triagem', observacoes: 'Aguardando conferência de integridade', responsavel: 'Marina Souza' },
      { id: 4, doador: 'Roberto Silva Santos', medicamento: 'Paracetamol 750mg', quantidade: 40, data_doacao: addDays(0), status: 'Pendente', observacoes: 'Entregue na Farmácia Solidária Centro', responsavel: 'Ana Clara' },
      { id: 5, doador: 'João Pedro Martins', medicamento: 'Amoxicilina 500mg', quantidade: 15, data_doacao: addDays(-8), status: 'Recusada', observacoes: 'Embalagem violada sem identificação clara de lote', responsavel: 'Marina Souza' }
    ];
    const stmt = sqlite.prepare('INSERT INTO doacoes (id, doador, medicamento, quantidade, data_doacao, status, observacoes, responsavel) VALUES (?, ?, ?, ?, ?, ?, ?, ?)');
    for (const d of seedDoacoes) {
      stmt.run(d.id, d.doador, d.medicamento, d.quantidade, d.data_doacao, d.status, d.observacoes, d.responsavel);
    }
  }

  const countPacientes = sqlite.prepare('SELECT COUNT(*) as count FROM pacientes').get().count;
  if (countPacientes === 0) {
    const seedPacientes = [
      { id: 1, nome: 'Maria da Silva', cpf: '11122233344', nascimento: '1975-03-15', endereco: 'Rua das Flores, 120 - Centro, Sorocaba/SP', contato: '(15) 99123-4567' },
      { id: 2, nome: 'José Oliveira Santos', cpf: '22233344455', nascimento: '1962-08-22', endereco: 'Av. Brasil, 450 - Jd. América, Sorocaba/SP', contato: '(15) 99789-0123' },
      { id: 3, nome: 'Ana Lúcia Ribeiro', cpf: '33344455566', nascimento: '1988-11-05', endereco: 'Rua São Paulo, 88 - Vila Hortência, Sorocaba/SP', contato: '(15) 98111-2233' },
      { id: 4, nome: 'Sebastião Ferreira', cpf: '44455566677', nascimento: '1950-01-30', endereco: 'Rua Quinze de Novembro, 310 - Centro, Votorantim/SP', contato: '(15) 99444-5566' }
    ];
    const stmt = sqlite.prepare('INSERT INTO pacientes (id, nome, cpf, nascimento, endereco, contato) VALUES (?, ?, ?, ?, ?, ?)');
    for (const p of seedPacientes) {
      stmt.run(p.id, p.nome, p.cpf, p.nascimento, p.endereco, p.contato);
    }
  }

  const countMedicos = sqlite.prepare('SELECT COUNT(*) as count FROM medicos').get().count;
  if (countMedicos === 0) {
    const seedMedicos = [
      { id: 1, nome: 'Dr. Rafael Almeida', crm: 'CRM-SP 142857', especialidade: 'Clínica Geral', contato: '(15) 3232-1000', email: 'rafael.almeida@redevita.local' },
      { id: 2, nome: 'Dra. Camila Nogueira', crm: 'CRM-SP 198420', especialidade: 'Cardiologia', contato: '(15) 3232-2000', email: 'camila.nogueira@redevita.local' },
      { id: 3, nome: 'Dr. Fernando Vasconcelos', crm: 'CRM-SP 167332', especialidade: 'Endocrinologia', contato: '(15) 3232-3000', email: 'fernando.vasconcelos@redevita.local' }
    ];
    const stmt = sqlite.prepare('INSERT INTO medicos (id, nome, crm, especialidade, contato, email) VALUES (?, ?, ?, ?, ?, ?)');
    for (const m of seedMedicos) {
      stmt.run(m.id, m.nome, m.crm, m.especialidade, m.contato, m.email);
    }
  }

  const countFarmacias = sqlite.prepare('SELECT COUNT(*) as count FROM farmacias').get().count;
  if (countFarmacias === 0) {
    const seedFarmacias = [
      { id: 1, nome_fantasia: 'Farmácia Solidária Central', razao_social: 'Associação Beneficente RedeVita Sorocaba', cnpj: '12.345.678/0001-90', endereco: 'Rua Monsenhor João Soares, 95 - Centro, Sorocaba/SP', responsavel: 'Marina Souza (CRF-SP 45892)', telefone: '(15) 3234-5678', horario: 'Seg-Sex 08:00 às 18:00', lat: -23.498, lng: -47.458 },
      { id: 2, nome_fantasia: 'Ponto de Apoio Zona Norte', razao_social: 'Centro Comunitário Vila Fiori', cnpj: '98.765.432/0001-10', endereco: 'Av. Itavuvu, 1200 - Vila Fiori, Sorocaba/SP', responsavel: 'Carlos Eduardo (CRF-SP 52103)', telefone: '(15) 3226-9012', horario: 'Seg-Sex 08:00 às 17:00', lat: -23.475, lng: -47.465 },
      { id: 3, nome_fantasia: 'Unidade Parceira Votorantim', razao_social: 'Farmácia Comunitária Votorantim', cnpj: '45.678.901/0001-23', endereco: 'Av. 31 de Março, 500 - Centro, Votorantim/SP', responsavel: 'Dra. Patrícia Lima (CRF-SP 38712)', telefone: '(15) 3243-1122', horario: 'Seg-Sex 09:00 às 17:30', lat: -23.541, lng: -47.443 }
    ];
    const stmt = sqlite.prepare('INSERT INTO farmacias (id, nome_fantasia, razao_social, cnpj, endereco, responsavel, telefone, horario, lat, lng) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)');
    for (const f of seedFarmacias) {
      stmt.run(f.id, f.nome_fantasia, f.razao_social, f.cnpj, f.endereco, f.responsavel, f.telefone, f.horario, f.lat, f.lng);
    }
  }

  const countReceitas = sqlite.prepare('SELECT COUNT(*) as count FROM receitas').get().count;
  if (countReceitas === 0) {
    const seedReceitas = [
      { id: 1, paciente_nome: 'Maria da Silva', medico_nome: 'Dr. Rafael Almeida', medicamento_nome: 'Losartana Potássica 50mg', tipo: 'Receita Simples', data_emissao: addDays(-3), status: 'dispensada', dispensada_por: 'Marina Souza Farmacêutica', observacoes: '1 comprimido ao dia pela manhã' },
      { id: 2, paciente_nome: 'José Oliveira Santos', medico_nome: 'Dra. Camila Nogueira', medicamento_nome: 'Hidroclorotiazida 25mg', tipo: 'Receita Simples', data_emissao: addDays(-1), status: 'ativa', dispensada_por: null, observacoes: '1 comprimido pela manhã após desjejum' },
      { id: 3, paciente_nome: 'Ana Lúcia Ribeiro', medico_nome: 'Dr. Fernando Vasconcelos', medicamento_nome: 'Metformina 850mg', tipo: 'Receita Simples', data_emissao: addDays(0), status: 'ativa', dispensada_por: null, observacoes: '2 comprimidos ao dia junto às refeições' }
    ];
    const stmt = sqlite.prepare('INSERT INTO receitas (id, paciente_nome, medico_nome, medicamento_nome, tipo, data_emissao, status, dispensada_por, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)');
    for (const r of seedReceitas) {
      stmt.run(r.id, r.paciente_nome, r.medico_nome, r.medicamento_nome, r.tipo, r.data_emissao, r.status, r.dispensada_por, r.observacoes);
    }
  }

  const countIot = sqlite.prepare('SELECT COUNT(*) as count FROM iot_dispositivos').get().count;
  if (countIot === 0) {
    const seedIot = [
      { id: 'IOT-CF-01', nome: 'Câmara Fria Central 01', local: 'Almoxarifado Geral - Setor Termolábeis', temperatura: 4.2, tempMin: 2.0, tempMax: 8.0, umidade: 55, bateria: 98, status: 'normal', ultimaLeitura: new Date().toISOString() },
      { id: 'IOT-GEL-02', nome: 'Geladeira de Insulinas e Vacinas', local: 'Farmácia Solidária Central - Balcão', temperatura: 5.1, tempMin: 2.0, tempMax: 8.0, umidade: 52, bateria: 85, status: 'normal', ultimaLeitura: new Date().toISOString() },
      { id: 'IOT-AMB-03', nome: 'Sensor de Temperatura Ambiente', local: 'Prateleiras de Medicamentos Comuns', temperatura: 22.4, tempMin: 15.0, tempMax: 30.0, umidade: 48, bateria: 92, status: 'normal', ultimaLeitura: new Date().toISOString() }
    ];
    const stmt = sqlite.prepare('INSERT INTO iot_dispositivos (id, nome, local, temperatura, tempMin, tempMax, umidade, bateria, status, ultimaLeitura) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)');
    for (const i of seedIot) {
      stmt.run(i.id, i.nome, i.local, i.temperatura, i.tempMin, i.tempMax, i.umidade, i.bateria, i.status, i.ultimaLeitura);
    }
  }

  const countLogs = sqlite.prepare('SELECT COUNT(*) as count FROM logs').get().count;
  if (countLogs === 0) {
    const seedLogs = [
      { usuario: 'Administrador RedeVita', acao: 'Login', detalhes: 'Autenticação bem-sucedida no sistema', data_hora: new Date().toLocaleString('pt-BR'), ip: '127.0.0.1' },
      { usuario: 'Marina Souza', acao: 'Triagem de Doação', detalhes: 'Aprovação de lote Amoxicilina 500mg (Hospital Santa Lucinda)', data_hora: new Date(Date.now() - 3600000 * 2).toLocaleString('pt-BR'), ip: '192.168.1.15' },
      { usuario: 'Marina Souza', acao: 'Dispensação', detalhes: 'Dispensação de Losartana Potássica para paciente Maria da Silva', data_hora: new Date(Date.now() - 3600000 * 5).toLocaleString('pt-BR'), ip: '192.168.1.15' }
    ];
    const stmt = sqlite.prepare('INSERT INTO logs (usuario, acao, detalhes, data_hora, ip) VALUES (?, ?, ?, ?, ?)');
    for (const l of seedLogs) {
      stmt.run(l.usuario, l.acao, l.detalhes, l.data_hora, l.ip);
    }
  }
}

// Executa semeadura do banco no carregamento
semearBanco();

// 3. Métodos Operacionais Persistentes em SQLite

function adicionarMedicamento(dados) {
  const nome = (dados.nome || '').trim();
  const lote = (dados.lote || '').trim().toUpperCase();
  const data_validade = dados.data_validade || '';
  const quantidade = Math.max(0, parseInt(dados.quantidade, 10) || 0);
  const tarja = dados.tarja || 'Sem Tarja';
  const principio_ativo = (dados.principio_ativo || '').trim();
  const status_semaforo = calcularStatusSemaforo(data_validade);

  const stmt = sqlite.prepare(`
    INSERT INTO medicamentos (nome, lote, data_validade, quantidade, tarja, principio_ativo, status_semaforo)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `);
  const res = stmt.run(nome, lote, data_validade, quantidade, tarja, principio_ativo, status_semaforo);
  const newId = Number(res.lastInsertRowid);

  // Registra movimentação de entrada no estoque
  try {
    sqlite.prepare(`
      INSERT INTO movimentacoes (medicamento_id, tipo, quantidade, motivo, observacoes, responsavel)
      VALUES (?, 'ENTRADA', ?, 'Cadastro inicial de medicamento', ?, ?)
    `).run(newId, quantidade, 'Cadastro via sistema', dados.responsavel || 'Sistema');
  } catch (err) {
    console.error('Erro ao gravar movimentação:', err);
  }

  return sqlite.prepare('SELECT * FROM medicamentos WHERE id = ?').get(newId);
}

function atualizarMedicamento(id, dados) {
  const med = sqlite.prepare('SELECT * FROM medicamentos WHERE id = ?').get(id);
  if (!med) return null;

  const nome = dados.nome !== undefined ? dados.nome.trim() : med.nome;
  const lote = dados.lote !== undefined ? dados.lote.trim().toUpperCase() : med.lote;
  const data_validade = dados.data_validade !== undefined ? dados.data_validade : med.data_validade;
  const quantidade = dados.quantidade !== undefined ? Math.max(0, parseInt(dados.quantidade, 10) || 0) : med.quantidade;
  const tarja = dados.tarja !== undefined ? dados.tarja : med.tarja;
  const principio_ativo = dados.principio_ativo !== undefined ? dados.principio_ativo.trim() : med.principio_ativo;
  const status_semaforo = calcularStatusSemaforo(data_validade);

  sqlite.prepare(`
    UPDATE medicamentos
    SET nome = ?, lote = ?, data_validade = ?, quantidade = ?, tarja = ?, principio_ativo = ?, status_semaforo = ?
    WHERE id = ?
  `).run(nome, lote, data_validade, quantidade, tarja, principio_ativo, status_semaforo, id);

  return sqlite.prepare('SELECT * FROM medicamentos WHERE id = ?').get(id);
}

function baixaMedicamento(id, quantidadeBaixa, motivo = 'Baixa de Estoque', observacoes = '', responsavel = 'Sistema') {
  const med = sqlite.prepare('SELECT * FROM medicamentos WHERE id = ?').get(id);
  if (!med) {
    throw new Error('Medicamento não encontrado na base de dados.');
  }

  const qtdBaixa = parseInt(quantidadeBaixa, 10);
  if (isNaN(qtdBaixa) || qtdBaixa <= 0) {
    throw new Error('A quantidade para baixa deve ser um número inteiro maior que zero.');
  }
  if (qtdBaixa > med.quantidade) {
    throw new Error(`A quantidade solicitada (${qtdBaixa} un.) excede o estoque disponível (${med.quantidade} un.).`);
  }

  const novaQtd = med.quantidade - qtdBaixa;
  sqlite.prepare('UPDATE medicamentos SET quantidade = ? WHERE id = ?').run(novaQtd, id);

  // Registra movimentação de baixa
  try {
    sqlite.prepare(`
      INSERT INTO movimentacoes (medicamento_id, tipo, quantidade, motivo, observacoes, responsavel)
      VALUES (?, 'BAIXA', ?, ?, ?, ?)
    `).run(id, qtdBaixa, motivo, observacoes, responsavel);
  } catch (err) {
    console.error('Erro ao gravar histórico de baixa:', err);
  }

  adicionarLog(responsavel, 'Baixa de Estoque', `Baixa de ${qtdBaixa} un. do medicamento ${med.nome} (Lote: ${med.lote}). Motivo: ${motivo}`);

  return sqlite.prepare('SELECT * FROM medicamentos WHERE id = ?').get(id);
}

function removerMedicamento(id) {
  const med = sqlite.prepare('SELECT * FROM medicamentos WHERE id = ?').get(id);
  if (med) {
    sqlite.prepare('DELETE FROM medicamentos WHERE id = ?').run(id);
  }
  return med;
}

function adicionarDoacao(dados) {
  const stmt = sqlite.prepare(`
    INSERT INTO doacoes (doador, medicamento, quantidade, data_doacao, status, observacoes, responsavel)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `);
  const data_doacao = formatDate(new Date());
  const res = stmt.run(
    dados.doador,
    dados.medicamento,
    parseInt(dados.quantidade, 10) || 1,
    data_doacao,
    'Pendente',
    dados.observacoes || '',
    dados.responsavel || 'Aguardando atribuição'
  );
  return sqlite.prepare('SELECT * FROM doacoes WHERE id = ?').get(res.lastInsertRowid);
}

function adicionarPaciente(dados) {
  const stmt = sqlite.prepare(`
    INSERT INTO pacientes (nome, cpf, nascimento, endereco, contato)
    VALUES (?, ?, ?, ?, ?)
  `);
  const res = stmt.run(dados.nome, dados.cpf, dados.nascimento, dados.endereco || '', dados.contato || '');
  return sqlite.prepare('SELECT * FROM pacientes WHERE id = ?').get(res.lastInsertRowid);
}

function adicionarMedico(dados) {
  const stmt = sqlite.prepare(`
    INSERT INTO medicos (nome, crm, especialidade, contato, email)
    VALUES (?, ?, ?, ?, ?)
  `);
  const res = stmt.run(dados.nome, dados.crm, dados.especialidade, dados.contato || '', dados.email || '');
  return sqlite.prepare('SELECT * FROM medicos WHERE id = ?').get(res.lastInsertRowid);
}

function adicionarFarmacia(dados) {
  const stmt = sqlite.prepare(`
    INSERT INTO farmacias (nome_fantasia, razao_social, cnpj, endereco, responsavel, telefone, horario, lat, lng)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);
  const lat = -23.498 + (Math.random() - 0.5) * 0.05;
  const lng = -47.458 + (Math.random() - 0.5) * 0.05;
  const res = stmt.run(
    dados.nome_fantasia,
    dados.nome_fantasia + ' Ltda',
    dados.cnpj,
    dados.endereco,
    dados.responsavel || 'Responsável Técnico',
    dados.telefone || '(15) 3000-0000',
    'Seg-Sex 08:00 às 18:00',
    lat,
    lng
  );
  return sqlite.prepare('SELECT * FROM farmacias WHERE id = ?').get(res.lastInsertRowid);
}

function adicionarReceita(dados) {
  const stmt = sqlite.prepare(`
    INSERT INTO receitas (paciente_nome, medico_nome, medicamento_nome, tipo, data_emissao, status, dispensada_por, observacoes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `);
  const res = stmt.run(
    dados.paciente_nome,
    dados.medico_nome,
    dados.medicamento_nome,
    dados.tipo || 'Receita Simples',
    formatDate(new Date()),
    'ativa',
    null,
    dados.observacoes || ''
  );
  return sqlite.prepare('SELECT * FROM receitas WHERE id = ?').get(res.lastInsertRowid);
}

function adicionarUsuario(dados) {
  const stmt = sqlite.prepare(`
    INSERT INTO usuarios (nome, cpf, cargo, email, senha, ativo)
    VALUES (?, ?, ?, ?, ?, 1)
  `);
  const res = stmt.run(
    dados.nome,
    dados.cpf,
    dados.cargo || 'Operador',
    dados.email || '',
    dados.senha || '123456'
  );
  return sqlite.prepare('SELECT * FROM usuarios WHERE id = ?').get(res.lastInsertRowid);
}

function adicionarLog(usuario, acao, detalhes, ip = '127.0.0.1') {
  const stmt = sqlite.prepare(`
    INSERT INTO logs (usuario, acao, detalhes, data_hora, ip)
    VALUES (?, ?, ?, ?, ?)
  `);
  stmt.run(usuario, acao, detalhes, new Date().toLocaleString('pt-BR'), ip);
}

function simularLeituraIot() {
  const iotList = sqlite.prepare('SELECT * FROM iot_dispositivos').all();
  for (const d of iotList) {
    const deltaTemp = (Math.random() - 0.5) * 0.4;
    const novaTemp = Math.max(d.tempMin, Math.min(d.tempMax, d.temperatura + deltaTemp));
    const novaUmidade = Math.max(40, Math.min(80, Math.round(d.umidade + (Math.random() - 0.5) * 4)));
    sqlite.prepare(`
      UPDATE iot_dispositivos SET temperatura = ?, umidade = ?, ultimaLeitura = ? WHERE id = ?
    `).run(novaTemp, novaUmidade, new Date().toISOString(), d.id);
  }
}

function getDashboardStats() {
  const meds = sqlite.prepare('SELECT * FROM medicamentos').all();
  const totalMedicamentos = meds.length;
  const totalEstoque = meds.reduce((acc, m) => acc + (m.quantidade || 0), 0);
  const alertasVencimento = meds.filter(m => {
    const status = calcularStatusSemaforo(m.data_validade);
    return status === 1 || status === 2;
  }).length;
  const totalDoacoes = sqlite.prepare('SELECT COUNT(*) as count FROM doacoes').get().count;
  const totalPacientes = sqlite.prepare('SELECT COUNT(*) as count FROM pacientes').get().count;
  const totalFarmacias = sqlite.prepare('SELECT COUNT(*) as count FROM farmacias').get().count;
  const totalMedicos = sqlite.prepare('SELECT COUNT(*) as count FROM medicos').get().count;

  return {
    totalMedicamentos,
    totalEstoque,
    alertasVencimento,
    totalDoacoes,
    totalPacientes,
    totalFarmacias,
    totalMedicos
  };
}

function buscar(termo) {
  const q = (termo || '').toLowerCase().trim();
  if (!q) {
    return { medicamentos: [], pacientes: [], medicos: [], farmacias: [] };
  }

  const allMeds = sqlite.prepare('SELECT * FROM medicamentos').all().map(m => ({
    ...m,
    status_semaforo: calcularStatusSemaforo(m.data_validade)
  }));
  const allPacientes = sqlite.prepare('SELECT * FROM pacientes').all();
  const allMedicos = sqlite.prepare('SELECT * FROM medicos').all();
  const allFarmacias = sqlite.prepare('SELECT * FROM farmacias').all();

  return {
    medicamentos: allMeds.filter(m => m.nome.toLowerCase().includes(q) || m.lote.toLowerCase().includes(q)),
    pacientes: allPacientes.filter(p => p.nome.toLowerCase().includes(q) || p.cpf.includes(q)),
    medicos: allMedicos.filter(m => m.nome.toLowerCase().includes(q) || m.crm.toLowerCase().includes(q) || (m.especialidade || '').toLowerCase().includes(q)),
    farmacias: allFarmacias.filter(f => f.nome_fantasia.toLowerCase().includes(q) || (f.endereco || '').toLowerCase().includes(q))
  };
}

// Getters dinâmicos para sincronizar coleções do SQLite diretamente
module.exports = {
  calcularStatusSemaforo,
  adicionarMedicamento,
  atualizarMedicamento,
  baixaMedicamento,
  removerMedicamento,
  adicionarDoacao,
  adicionarPaciente,
  adicionarMedico,
  adicionarFarmacia,
  adicionarReceita,
  adicionarUsuario,
  adicionarLog,
  simularLeituraIot,
  getDashboardStats,
  buscar
};

Object.defineProperties(module.exports, {
  usuarios: {
    get() {
      return sqlite.prepare('SELECT * FROM usuarios ORDER BY id ASC').all();
    }
  },
  medicamentos: {
    get() {
      const rows = sqlite.prepare('SELECT * FROM medicamentos ORDER BY id DESC').all();
      return rows.map(m => ({
        ...m,
        status_semaforo: calcularStatusSemaforo(m.data_validade)
      }));
    }
  },
  doacoes: {
    get() {
      return sqlite.prepare('SELECT * FROM doacoes ORDER BY id DESC').all();
    }
  },
  pacientes: {
    get() {
      return sqlite.prepare('SELECT * FROM pacientes ORDER BY id DESC').all();
    }
  },
  medicos: {
    get() {
      return sqlite.prepare('SELECT * FROM medicos ORDER BY id ASC').all();
    }
  },
  farmacias: {
    get() {
      return sqlite.prepare('SELECT * FROM farmacias ORDER BY id ASC').all();
    }
  },
  receitas: {
    get() {
      return sqlite.prepare('SELECT * FROM receitas ORDER BY id DESC').all();
    }
  },
  iotDispositivos: {
    get() {
      return sqlite.prepare('SELECT * FROM iot_dispositivos ORDER BY id ASC').all();
    }
  },
  logs: {
    get() {
      return sqlite.prepare('SELECT * FROM logs ORDER BY id DESC LIMIT 200').all();
    }
  },
  notificacoes: {
    get() {
      const medsAlert = sqlite.prepare('SELECT * FROM medicamentos ORDER BY data_validade ASC').all();
      return medsAlert
        .map(m => {
          const semaforo = calcularStatusSemaforo(m.data_validade);
          if (semaforo === 0) return null;
          return {
            id: m.id,
            tipo: semaforo === 2 ? 'danger' : 'warning',
            titulo: semaforo === 2 ? 'Medicamento Vencido' : 'Vencimento Próximo',
            mensagem: `${m.nome} (Lote: ${m.lote}) - Validade: ${m.data_validade}`,
            data: new Date().toLocaleDateString('pt-BR'),
            lida: false
          };
        })
        .filter(Boolean);
    }
  }
});
