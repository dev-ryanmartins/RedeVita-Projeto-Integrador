// In-memory data store for RedeVita (CommonJS)

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

const usuarios = [
  {
    id: 1,
    nome: 'Administrador RedeVita',
    cpf: '00000000000',
    email: 'admin@redevita.local',
    senha: 'admin123',
    cargo: 'Admin',
    ativo: true,
  },
  {
    id: 2,
    nome: 'Ana Clara Voluntária',
    cpf: '22244466671',
    email: 'voluntario.demo@redevita.local',
    senha: 'demo1234',
    cargo: 'Voluntário',
    ativo: true,
  },
  {
    id: 3,
    nome: 'Marina Souza Farmacêutica',
    cpf: '33355577782',
    email: 'farmaceutico.demo@redevita.local',
    senha: 'demo1234',
    cargo: 'Farmacêutico',
    ativo: true,
  },
  {
    id: 4,
    nome: 'Dr. Rafael Almeida',
    cpf: '44466688893',
    email: 'medico.demo@redevita.local',
    senha: 'demo1234',
    cargo: 'Médico',
    ativo: true,
  },
  {
    id: 5,
    nome: 'Carlos Eduardo Silveira',
    cpf: '55577799904',
    email: 'carlos@redevita.local',
    senha: 'demo1234',
    cargo: 'Farmacêutico',
    ativo: true,
  }
];

const medicamentos = [
  {
    id: 1,
    nome: 'Dipirona Sódica 500mg/mL',
    lote: 'DIP-2024-01',
    data_validade: addDays(180),
    quantidade: 450,
    tarja: 'Sem Tarja',
    principio_ativo: 'Dipirona Sódica',
    status_semaforo: 0,
  },
  {
    id: 2,
    nome: 'Paracetamol 750mg',
    lote: 'PAR-2024-02',
    data_validade: addDays(120),
    quantidade: 320,
    tarja: 'Sem Tarja',
    principio_ativo: 'Paracetamol',
    status_semaforo: 0,
  },
  {
    id: 3,
    nome: 'Amoxicilina + Clavulanato 500mg+125mg',
    lote: 'AMX-2024-03',
    data_validade: addDays(25),
    quantidade: 180,
    tarja: 'Tarja Vermelha',
    principio_ativo: 'Amoxicilina Tri-hidratada + Clavulanato de Potássio',
    status_semaforo: 1,
  },
  {
    id: 4,
    nome: 'Losartana Potássica 50mg',
    lote: 'LOS-2024-04',
    data_validade: addDays(365),
    quantidade: 600,
    tarja: 'Tarja Vermelha',
    principio_ativo: 'Losartana Potássica',
    status_semaforo: 0,
  },
  {
    id: 5,
    nome: 'Hidroclorotiazida 25mg',
    lote: 'HCT-2024-05',
    data_validade: addDays(200),
    quantidade: 290,
    tarja: 'Tarja Vermelha',
    principio_ativo: 'Hidroclorotiazida',
    status_semaforo: 0,
  },
  {
    id: 6,
    nome: 'Metformina 850mg',
    lote: 'MET-2024-06',
    data_validade: addDays(-5),
    quantidade: 40,
    tarja: 'Tarja Vermelha',
    principio_ativo: 'Cloridrato de Metformina',
    status_semaforo: 2,
  },
  {
    id: 7,
    nome: 'Omeprazol 20mg',
    lote: 'OME-2024-07',
    data_validade: addDays(15),
    quantidade: 210,
    tarja: 'Tarja Vermelha',
    principio_ativo: 'Omeprazol',
    status_semaforo: 1,
  },
  {
    id: 8,
    nome: 'Sinvastatina 20mg',
    lote: 'SIN-2024-08',
    data_validade: addDays(300),
    quantidade: 195,
    tarja: 'Tarja Vermelha',
    principio_ativo: 'Sinvastatina',
    status_semaforo: 0,
  },
  {
    id: 9,
    nome: 'Atenolol 50mg',
    lote: 'ATE-2024-09',
    data_validade: addDays(400),
    quantidade: 310,
    tarja: 'Tarja Vermelha',
    principio_ativo: 'Atenolol',
    status_semaforo: 0,
  },
  {
    id: 10,
    nome: 'Clonazepam 2mg',
    lote: 'CNZ-2024-10',
    data_validade: addDays(90),
    quantidade: 85,
    tarja: 'Portaria 344',
    principio_ativo: 'Clonazepam',
    status_semaforo: 0,
  },
  {
    id: 11,
    nome: 'Insulina NPH 100UI/mL',
    lote: 'INS-2024-11',
    data_validade: addDays(45),
    quantidade: 60,
    tarja: 'Tarja Vermelha',
    principio_ativo: 'Insulina Humana',
    status_semaforo: 0,
  }
];

const doacoes = [
  {
    id: 1,
    doador: 'Hospital Santa Lucinda',
    medicamento: 'Amoxicilina 500mg',
    quantidade: 50,
    data_doacao: addDays(-2),
    status: 'Aprovada',
    observacoes: 'Lote lacrado original em boas condições',
    responsavel: 'Marina Souza',
  },
  {
    id: 2,
    doador: 'Drogaria São Paulo - Unidade Campolim',
    medicamento: 'Dipirona 500mg',
    quantidade: 100,
    data_doacao: addDays(-5),
    status: 'Aprovada',
    observacoes: 'Validade acima de 6 meses',
    responsavel: 'Ana Clara',
  },
  {
    id: 3,
    doador: 'Fernanda Oliveira Rocha',
    medicamento: 'Ibuprofeno 600mg',
    quantidade: 20,
    data_doacao: addDays(-1),
    status: 'Em Triagem',
    observacoes: 'Aguardando conferência de integridade',
    responsavel: 'Marina Souza',
  },
  {
    id: 4,
    doador: 'Roberto Silva Santos',
    medicamento: 'Paracetamol 750mg',
    quantidade: 40,
    data_doacao: addDays(0),
    status: 'Pendente',
    observacoes: 'Entregue na Farmácia Solidária Centro',
    responsavel: 'Ana Clara',
  },
  {
    id: 5,
    doador: 'João Pedro Martins',
    medicamento: 'Amoxicilina 500mg',
    quantidade: 15,
    data_doacao: addDays(-8),
    status: 'Recusada',
    observacoes: 'Embalagem violada sem identificação clara de lote',
    responsavel: 'Marina Souza',
  }
];

const pacientes = [
  {
    id: 1,
    nome: 'Maria da Silva',
    cpf: '11122233344',
    nascimento: '1975-03-15',
    endereco: 'Rua das Flores, 120 - Centro, Sorocaba/SP',
    contato: '(15) 99123-4567',
  },
  {
    id: 2,
    nome: 'José Oliveira Santos',
    cpf: '22233344455',
    nascimento: '1962-08-22',
    endereco: 'Av. Brasil, 450 - Jd. América, Sorocaba/SP',
    contato: '(15) 99789-0123',
  },
  {
    id: 3,
    nome: 'Ana Lúcia Ribeiro',
    cpf: '33344455566',
    nascimento: '1988-11-05',
    endereco: 'Rua São Paulo, 88 - Vila Hortência, Sorocaba/SP',
    contato: '(15) 98111-2233',
  },
  {
    id: 4,
    nome: 'Sebastião Ferreira',
    cpf: '44455566677',
    nascimento: '1950-01-30',
    endereco: 'Rua Quinze de Novembro, 310 - Centro, Votorantim/SP',
    contato: '(15) 99444-5566',
  }
];

const medicos = [
  {
    id: 1,
    nome: 'Dr. Rafael Almeida',
    crm: 'CRM-SP 142857',
    especialidade: 'Clínica Geral',
    contato: '(15) 3232-1000',
    email: 'rafael.almeida@redevita.local',
  },
  {
    id: 2,
    nome: 'Dra. Camila Nogueira',
    crm: 'CRM-SP 198420',
    especialidade: 'Cardiologia',
    contato: '(15) 3232-2000',
    email: 'camila.nogueira@redevita.local',
  },
  {
    id: 3,
    nome: 'Dr. Fernando Vasconcelos',
    crm: 'CRM-SP 167332',
    especialidade: 'Endocrinologia',
    contato: '(15) 3232-3000',
    email: 'fernando.vasconcelos@redevita.local',
  }
];

const farmacias = [
  {
    id: 1,
    nome_fantasia: 'Farmácia Solidária Central',
    razao_social: 'Associação Beneficente RedeVita Sorocaba',
    cnpj: '12.345.678/0001-90',
    endereco: 'Rua Monsenhor João Soares, 95 - Centro, Sorocaba/SP',
    responsavel: 'Marina Souza (CRF-SP 45892)',
    telefone: '(15) 3234-5678',
    horario: 'Seg-Sex 08:00 às 18:00',
    lat: -23.498,
    lng: -47.458
  },
  {
    id: 2,
    nome_fantasia: 'Ponto de Apoio Zona Norte',
    razao_social: 'Centro Comunitário Vila Fiori',
    cnpj: '98.765.432/0001-10',
    endereco: 'Av. Itavuvu, 1200 - Vila Fiori, Sorocaba/SP',
    responsavel: 'Carlos Eduardo (CRF-SP 52103)',
    telefone: '(15) 3226-9012',
    horario: 'Seg-Sex 08:00 às 17:00',
    lat: -23.475,
    lng: -47.465
  },
  {
    id: 3,
    nome_fantasia: 'Unidade Parceira Votorantim',
    razao_social: 'Farmácia Comunitária Votorantim',
    cnpj: '45.678.901/0001-23',
    endereco: 'Av. 31 de Março, 500 - Centro, Votorantim/SP',
    responsavel: 'Dra. Patrícia Lima (CRF-SP 38712)',
    telefone: '(15) 3243-1122',
    horario: 'Seg-Sex 09:00 às 17:30',
    lat: -23.541,
    lng: -47.443
  }
];

const receitas = [
  {
    id: 1,
    paciente_nome: 'Maria da Silva',
    medico_nome: 'Dr. Rafael Almeida',
    medicamento_nome: 'Losartana Potássica 50mg',
    tipo: 'Receita Simples',
    data_emissao: addDays(-3),
    status: 'dispensada',
    dispensada_por: 'Marina Souza Farmacêutica',
    observacoes: '1 comprimido ao dia pela manhã',
  },
  {
    id: 2,
    paciente_nome: 'José Oliveira Santos',
    medico_nome: 'Dra. Camila Nogueira',
    medicamento_nome: 'Hidroclorotiazida 25mg',
    tipo: 'Receita Simples',
    data_emissao: addDays(-1),
    status: 'ativa',
    dispensada_por: null,
    observacoes: '1 comprimido pela manhã após desjejum',
  },
  {
    id: 3,
    paciente_nome: 'Ana Lúcia Ribeiro',
    medico_nome: 'Dr. Fernando Vasconcelos',
    medicamento_nome: 'Metformina 850mg',
    tipo: 'Receita Simples',
    data_emissao: addDays(0),
    status: 'ativa',
    dispensada_por: null,
    observacoes: '2 comprimidos ao dia junto às refeições',
  }
];

const iotDispositivos = [
  {
    id: 'IOT-CF-01',
    nome: 'Câmara Fria Central 01',
    local: 'Almoxarifado Geral - Setor Termolábeis',
    temperatura: 4.2,
    tempMin: 2.0,
    tempMax: 8.0,
    umidade: 55,
    bateria: 98,
    status: 'normal',
    ultimaLeitura: new Date().toISOString(),
  },
  {
    id: 'IOT-GEL-02',
    nome: 'Geladeira de Insulinas e Vacinas',
    local: 'Farmácia Solidária Central - Balcão',
    temperatura: 5.1,
    tempMin: 2.0,
    tempMax: 8.0,
    umidade: 52,
    bateria: 85,
    status: 'normal',
    ultimaLeitura: new Date().toISOString(),
  },
  {
    id: 'IOT-AMB-03',
    nome: 'Sensor de Temperatura Ambiente',
    local: 'Prateleiras de Medicamentos Comuns',
    temperatura: 22.4,
    tempMin: 15.0,
    tempMax: 30.0,
    umidade: 48,
    bateria: 92,
    status: 'normal',
    ultimaLeitura: new Date().toISOString(),
  }
];

const logs = [
  {
    id: 1,
    usuario: 'Administrador RedeVita',
    acao: 'Login',
    detalhes: 'Autenticação bem-sucedida no sistema',
    data_hora: new Date().toLocaleString('pt-BR'),
    ip: '127.0.0.1'
  },
  {
    id: 2,
    usuario: 'Marina Souza',
    acao: 'Triagem de Doação',
    detalhes: 'Aprovação de lote Amoxicilina 500mg (Hospital Santa Lucinda)',
    data_hora: new Date(Date.now() - 3600000 * 2).toLocaleString('pt-BR'),
    ip: '192.168.1.15'
  },
  {
    id: 3,
    usuario: 'Marina Souza',
    acao: 'Dispensação',
    detalhes: 'Dispensação de Losartana Potássica para paciente Maria da Silva',
    data_hora: new Date(Date.now() - 3600000 * 5).toLocaleString('pt-BR'),
    ip: '192.168.1.15'
  }
];

const notificacoes = [
  {
    id: 1,
    tipo: 'warning',
    titulo: 'Vencimento Próximo',
    mensagem: 'Amoxicilina + Clavulanato vence em menos de 30 dias.',
    data: new Date().toLocaleDateString('pt-BR'),
    lida: false
  },
  {
    id: 2,
    tipo: 'info',
    titulo: 'Nova Doação Pendente',
    mensagem: 'Paracetamol 750mg recebido aguardando triagem.',
    data: new Date().toLocaleDateString('pt-BR'),
    lida: false
  }
];

// Helper functions

function adicionarMedicamento(dados) {
  const newId = medicamentos.length > 0 ? Math.max(...medicamentos.map(m => m.id)) + 1 : 1;
  const item = {
    id: newId,
    nome: dados.nome,
    lote: dados.lote,
    data_validade: dados.data_validade,
    quantidade: parseInt(dados.quantidade, 10) || 0,
    tarja: dados.tarja || 'Sem Tarja',
    principio_ativo: dados.principio_ativo || '',
    status_semaforo: calcularStatusSemaforo(dados.data_validade),
  };
  medicamentos.unshift(item);
  return item;
}

function atualizarMedicamento(id, dados) {
  const med = medicamentos.find(m => m.id === id);
  if (!med) return null;
  if (dados.nome) med.nome = dados.nome;
  if (dados.lote) med.lote = dados.lote;
  if (dados.data_validade) {
    med.data_validade = dados.data_validade;
    med.status_semaforo = calcularStatusSemaforo(dados.data_validade);
  }
  if (dados.quantidade !== undefined) med.quantidade = parseInt(dados.quantidade, 10) || 0;
  if (dados.tarja) med.tarja = dados.tarja;
  if (dados.principio_ativo) med.principio_ativo = dados.principio_ativo;
  return med;
}

function removerMedicamento(id) {
  const idx = medicamentos.findIndex(m => m.id === id);
  if (idx !== -1) {
    return medicamentos.splice(idx, 1)[0];
  }
  return null;
}

function adicionarDoacao(dados) {
  const newId = doacoes.length > 0 ? Math.max(...doacoes.map(d => d.id)) + 1 : 1;
  const d = {
    id: newId,
    doador: dados.doador,
    medicamento: dados.medicamento,
    quantidade: parseInt(dados.quantidade, 10) || 1,
    data_doacao: formatDate(new Date()),
    status: 'Pendente',
    observacoes: dados.observacoes || '',
    responsavel: dados.responsavel || 'Aguardando atribuição',
  };
  doacoes.unshift(d);
  return d;
}

function adicionarPaciente(dados) {
  const newId = pacientes.length > 0 ? Math.max(...pacientes.map(p => p.id)) + 1 : 1;
  const p = {
    id: newId,
    nome: dados.nome,
    cpf: dados.cpf,
    nascimento: dados.nascimento,
    endereco: dados.endereco || '',
    contato: dados.contato || '',
  };
  pacientes.push(p);
  return p;
}

function adicionarMedico(dados) {
  const newId = medicos.length > 0 ? Math.max(...medicos.map(m => m.id)) + 1 : 1;
  const m = {
    id: newId,
    nome: dados.nome,
    crm: dados.crm,
    especialidade: dados.especialidade,
    contato: dados.contato || '',
    email: dados.email || '',
  };
  medicos.push(m);
  return m;
}

function adicionarFarmacia(dados) {
  const newId = farmacias.length > 0 ? Math.max(...farmacias.map(f => f.id)) + 1 : 1;
  const f = {
    id: newId,
    nome_fantasia: dados.nome_fantasia,
    razao_social: dados.nome_fantasia + ' Ltda',
    cnpj: dados.cnpj,
    endereco: dados.endereco,
    responsavel: dados.responsavel || 'Responsável Técnico',
    telefone: dados.telefone || '(15) 3000-0000',
    horario: 'Seg-Sex 08:00 às 18:00',
    lat: -23.498 + (Math.random() - 0.5) * 0.05,
    lng: -47.458 + (Math.random() - 0.5) * 0.05
  };
  farmacias.push(f);
  return f;
}

function adicionarReceita(dados) {
  const newId = receitas.length > 0 ? Math.max(...receitas.map(r => r.id)) + 1 : 1;
  const r = {
    id: newId,
    paciente_nome: dados.paciente_nome,
    medico_nome: dados.medico_nome,
    medicamento_nome: dados.medicamento_nome,
    tipo: dados.tipo || 'Receita Simples',
    data_emissao: formatDate(new Date()),
    status: 'ativa',
    dispensada_por: null,
    observacoes: dados.observacoes || '',
  };
  receitas.unshift(r);
  return r;
}

function adicionarUsuario(dados) {
  const newId = usuarios.length > 0 ? Math.max(...usuarios.map(u => u.id)) + 1 : 1;
  const u = {
    id: newId,
    nome: dados.nome,
    cpf: dados.cpf,
    cargo: dados.cargo || 'Operador',
    email: dados.email || '',
    senha: dados.senha || '123456',
    ativo: true,
  };
  usuarios.push(u);
  return u;
}

function adicionarLog(usuario, acao, detalhes, ip = '127.0.0.1') {
  const newId = logs.length > 0 ? Math.max(...logs.map(l => l.id)) + 1 : 1;
  logs.unshift({
    id: newId,
    usuario,
    acao,
    detalhes,
    data_hora: new Date().toLocaleString('pt-BR'),
    ip
  });
  if (logs.length > 200) logs.pop();
}

function simularLeituraIot() {
  iotDispositivos.forEach(d => {
    const deltaTemp = (Math.random() - 0.5) * 0.4;
    d.temperatura = Math.max(d.tempMin, Math.min(d.tempMax, d.temperatura + deltaTemp));
    d.umidade = Math.max(40, Math.min(80, Math.round(d.umidade + (Math.random() - 0.5) * 4)));
    d.ultimaLeitura = new Date().toISOString();
  });
}

function getDashboardStats() {
  const totalMedicamentos = medicamentos.length;
  const totalEstoque = medicamentos.reduce((acc, m) => acc + (m.quantidade || 0), 0);
  const alertasVencimento = medicamentos.filter(m => m.status_semaforo === 1 || m.status_semaforo === 2).length;
  const totalDoacoes = doacoes.length;
  const totalPacientes = pacientes.length;
  const totalFarmacias = farmacias.length;
  const totalMedicos = medicos.length;

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

  return {
    medicamentos: medicamentos.filter(m => m.nome.toLowerCase().includes(q) || m.lote.toLowerCase().includes(q)),
    pacientes: pacientes.filter(p => p.nome.toLowerCase().includes(q) || p.cpf.includes(q)),
    medicos: medicos.filter(m => m.nome.toLowerCase().includes(q) || m.crm.toLowerCase().includes(q) || m.especialidade.toLowerCase().includes(q)),
    farmacias: farmacias.filter(f => f.nome_fantasia.toLowerCase().includes(q) || f.endereco.toLowerCase().includes(q))
  };
}

module.exports = {
  usuarios,
  medicamentos,
  doacoes,
  pacientes,
  medicos,
  farmacias,
  receitas,
  iotDispositivos,
  logs,
  notificacoes,
  calcularStatusSemaforo,
  adicionarMedicamento,
  atualizarMedicamento,
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
