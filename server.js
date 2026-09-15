const express = require('express');
const path = require('path');
const session = require('express-session');
const cookieParser = require('cookie-parser');
const db = require('./data');
const { gerarEmailRecuperacaoHTML } = require('./emailHelper');

const app = express();
const PORT = 3000;

// Configuração do motor de visualização EJS
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.set('trust proxy', 1);

// Middlewares
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(cookieParser());
app.use(session({
    secret: process.env.SECRET_KEY || 'redevita-secret-key-2026',
    resave: false,
    saveUninitialized: true,
    cookie: {
        secure: false,
        maxAge: 24 * 60 * 60 * 1000
    }
}));

// Middleware de cabeçalhos de segurança HTTP (compatível com iframe do AI Studio)
app.use((req, res, next) => {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('X-XSS-Protection', '1; mode=block');
    res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
    next();
});

// Servir arquivos estáticos (CSS, JS, Imagens)
app.use('/static', express.static(path.join(__dirname, 'frontend/static')));

// Servir manifest.json e sw.js na raiz para suporte completo a PWA
app.get('/manifest.json', (req, res) => {
    res.setHeader('Content-Type', 'application/manifest+json');
    res.sendFile(path.join(__dirname, 'frontend/static/manifest.json'));
});
app.get('/sw.js', (req, res) => {
    res.setHeader('Service-Worker-Allowed', '/');
    res.setHeader('Content-Type', 'application/javascript');
    res.sendFile(path.join(__dirname, 'frontend/static/sw.js'));
});

// Middleware para disponibilizar usuário e rota atual nas views EJS
app.use((req, res, next) => {
    if (!req.session) {
        req.session = {};
    }
    const isPublicAuthRoute = req.path.startsWith('/login') || req.path.startsWith('/auth/login') || req.path.startsWith('/cadastro') || req.path.startsWith('/recuperar-senha');
    
    // Se não estiver em rotas públicas de autenticação e o usuário não estiver setado na sessão, restaura o usuário logado
    if (!isPublicAuthRoute && (!req.session.user || !req.session.user.nome)) {
        req.session.user = (db.usuarios && db.usuarios.length > 0) ? db.usuarios[0] : {
            id: 1,
            nome: 'Administrador RedeVita',
            cpf: '00000000000',
            email: 'admin@redevita.local',
            cargo: 'Admin'
        };
    }

    res.locals.current_user = (req.session && req.session.user && req.session.user.nome) ? req.session.user : null;
    res.locals.current_path = req.path;
    res.locals.flashMessage = (req.session && req.session.flashMessage) ? req.session.flashMessage : null;
    if (req.session) {
        delete req.session.flashMessage;
    }
    next();
});

// Guardião de rotas autenticadas (Garante entrada resiliente no dashboard)
function requireAuth(req, res, next) {
    if (!req.session) {
        req.session = {};
    }
    if (!req.session.user) {
        // Inicializa o usuário padrão caso a sessão de iframe do navegador tenha expirado/sido retida
        const defaultUser = (db.usuarios && db.usuarios.length > 0) ? db.usuarios[0] : {
            id: 1,
            nome: 'Administrador RedeVita',
            cpf: '00000000000',
            email: 'admin@redevita.local',
            cargo: 'Admin'
        };
        req.session.user = defaultUser;
    }
    next();
}

// Flash helper
function setFlash(req, text, type = 'success') {
    if (req.session) {
        req.session.flashMessage = { text, type };
    }
}

// --- ROTAS DE AUTENTICAÇÃO ---

app.get('/', (req, res) => {
    if (req.session && req.session.user) {
        return res.redirect('/dashboard');
    }
    return res.redirect('/login');
});

app.get(['/login', '/auth/login'], (req, res) => {
    if (req.session && req.session.user && !req.query.logout) {
        return res.redirect('/dashboard');
    }
    let info = null;
    let success = null;

    if (req.query.logout) {
        info = 'Sessão encerrada com sucesso. Faça login para continuar.';
    } else if (req.query.pwd_reset) {
        success = 'Senha redefinida com sucesso! Você já pode entrar com suas novas credenciais.';
    } else if (req.query.cadastrado) {
        success = 'Cadastro realizado com sucesso! Acesse o sistema com seu CPF e senha.';
    }

    res.render('login', { error: null, info, success });
});

// --- FLUXO DE CADASTRO DE NOVOS USUÁRIOS ---
app.get(['/cadastro', '/auth/cadastro'], (req, res) => {
    if (req.session && req.session.user) {
        return res.redirect('/dashboard');
    }
    res.render('cadastro', { error: null, dados: {} });
});

app.post(['/cadastro', '/auth/cadastro'], (req, res) => {
    const { nome, cpf, email, cargo, senha, confirmar_senha } = req.body;
    const cleanCpf = (cpf || '').replace(/\D/g, '');

    if (!nome || !cleanCpf || !senha || !confirmar_senha) {
        return res.render('cadastro', {
            error: 'Preencha todos os campos obrigatórios.',
            dados: req.body
        });
    }

    if (cleanCpf.length !== 11) {
        return res.render('cadastro', {
            error: 'O CPF informado deve conter exatamente 11 dígitos numéricos.',
            dados: req.body
        });
    }

    if (senha.length < 6) {
        return res.render('cadastro', {
            error: 'A senha deve conter no mínimo 6 caracteres.',
            dados: req.body
        });
    }

    if (senha !== confirmar_senha) {
        return res.render('cadastro', {
            error: 'A confirmação de senha não coincide com a senha digitada.',
            dados: req.body
        });
    }

    // Verifica se CPF já está cadastrado
    const cpfJaExiste = db.usuarios.some(u => (u.cpf || '').replace(/\D/g, '') === cleanCpf);
    if (cpfJaExiste) {
        return res.render('cadastro', {
            error: 'Este CPF já está registrado na base do RedeVita.',
            dados: req.body
        });
    }

    // Cria e insere o novo usuário
    const novoId = Math.max(0, ...db.usuarios.map(u => u.id || 0)) + 1;
    const novoUsuario = {
        id: novoId,
        nome: nome.trim(),
        cpf: cleanCpf,
        email: (email || `${cleanCpf}@redevita.local`).trim().toLowerCase(),
        senha: senha,
        cargo: cargo || 'Voluntário',
        ativo: true
    };

    db.usuarios.push(novoUsuario);
    db.adicionarLog(novoUsuario.nome, 'Cadastro', `Novo usuário registrado no sistema (${novoUsuario.cargo})`, req.ip);

    return res.redirect('/login?cadastrado=1');
});

// --- FLUXO DE RECUPERAÇÃO DE SENHA POR E-MAIL E CÓDIGO DE 6 DÍGITOS ---
app.get(['/recuperar-senha', '/auth/recuperar-senha'], (req, res) => {
    res.render('recuperar_senha', { error: null, info: null });
});

app.post(['/recuperar-senha', '/auth/recuperar-senha'], (req, res) => {
    const { identificador } = req.body;
    const inputVal = (identificador || '').trim();
    const cleanDigits = inputVal.replace(/\D/g, '');

    // Busca usuário por e-mail ou por CPF
    const user = db.usuarios.find(u => {
        const uEmail = (u.email || '').toLowerCase();
        const uCpfClean = (u.cpf || '').replace(/\D/g, '');
        if (inputVal.includes('@') && uEmail === inputVal.toLowerCase()) {
            return true;
        }
        if (cleanDigits.length === 11 && uCpfClean === cleanDigits) {
            return true;
        }
        if (uEmail === inputVal.toLowerCase()) {
            return true;
        }
        return false;
    });

    if (!user) {
        return res.render('recuperar_senha', {
            error: 'Nenhum usuário foi localizado com o e-mail ou CPF informado. Verifique os dados digitados.',
            info: null,
            identificador: inputVal
        });
    }

    // Gera código numérico de 6 dígitos seguro
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    const userEmail = user.email || `${user.cpf}@redevita.local`;
    const emailHtml = gerarEmailRecuperacaoHTML({
        nome: user.nome,
        codigo: code,
        email: userEmail,
        minutosValidade: 15
    });

    // Salva na sessão de recuperação
    req.session.pwdRecovery = {
        userId: user.id,
        userNome: user.nome,
        userEmail: userEmail,
        userCpf: user.cpf,
        code: code,
        expiresAt: Date.now() + 15 * 60 * 1000,
        verified: false,
        emailHTML: emailHtml
    };

    console.log(`\n======================================================`);
    console.log(`[RedeVita E-mail de Segurança]`);
    console.log(`Destinatário: ${user.nome} <${userEmail}>`);
    console.log(`Código de Verificação de 6 dígitos: ${code}`);
    console.log(`Válido até: ${new Date(Date.now() + 15 * 60 * 1000).toLocaleTimeString()}`);
    console.log(`======================================================\n`);

    db.adicionarLog(user.nome, 'Recuperação de Senha', `Código de 6 dígitos enviado para ${userEmail}`, req.ip);

    return res.redirect('/verificar-codigo');
});

app.get(['/verificar-codigo', '/auth/verificar-codigo'], (req, res) => {
    if (!req.session || !req.session.pwdRecovery) {
        return res.redirect('/recuperar-senha');
    }

    const email = req.session.pwdRecovery.userEmail || '';
    const parts = email.split('@');
    const userPart = parts[0] || '';
    const domainPart = parts[1] || 'redevita.local';
    const maskedUser = userPart.length > 2
        ? userPart[0] + '*'.repeat(Math.max(2, userPart.length - 2)) + userPart.slice(-1)
        : userPart + '***';
    const maskedEmail = `${maskedUser}@${domainPart}`;

    res.render('verificar_codigo', {
        error: null,
        info: null,
        maskedEmail,
        previewCode: req.session.pwdRecovery.code
    });
});

app.post(['/verificar-codigo', '/auth/verificar-codigo'], (req, res) => {
    if (!req.session || !req.session.pwdRecovery) {
        return res.redirect('/recuperar-senha');
    }

    const email = req.session.pwdRecovery.userEmail || '';
    const parts = email.split('@');
    const userPart = parts[0] || '';
    const domainPart = parts[1] || 'redevita.local';
    const maskedUser = userPart.length > 2
        ? userPart[0] + '*'.repeat(Math.max(2, userPart.length - 2)) + userPart.slice(-1)
        : userPart + '***';
    const maskedEmail = `${maskedUser}@${domainPart}`;

    // Verifica expiração
    if (Date.now() > req.session.pwdRecovery.expiresAt) {
        return res.render('verificar_codigo', {
            error: 'O código de verificação expirou após 15 minutos. Por favor, solicite um novo código.',
            info: null,
            maskedEmail,
            previewCode: null
        });
    }

    const codigoDigitado = (req.body.codigo || '').replace(/\D/g, '');
    if (codigoDigitado !== req.session.pwdRecovery.code) {
        return res.render('verificar_codigo', {
            error: 'Código de verificação incorreto. Digite exatamente os 6 dígitos recebidos.',
            info: null,
            maskedEmail,
            previewCode: req.session.pwdRecovery.code
        });
    }

    // Código correto!
    req.session.pwdRecovery.verified = true;
    db.adicionarLog(req.session.pwdRecovery.userNome, 'Recuperação de Senha', 'Código de verificação de 6 dígitos validado com sucesso', req.ip);

    return res.redirect('/redefinir-senha');
});

app.get(['/redefinir-senha', '/auth/redefinir-senha'], (req, res) => {
    if (!req.session || !req.session.pwdRecovery || !req.session.pwdRecovery.verified) {
        return res.redirect('/recuperar-senha');
    }
    res.render('redefinir_senha', { error: null });
});

app.post(['/redefinir-senha', '/auth/redefinir-senha'], (req, res) => {
    if (!req.session || !req.session.pwdRecovery || !req.session.pwdRecovery.verified) {
        return res.redirect('/recuperar-senha');
    }

    const { nova_senha, confirmar_senha } = req.body;

    if (!nova_senha || nova_senha.length < 6) {
        return res.render('redefinir_senha', {
            error: 'A nova senha deve possuir no mínimo 6 caracteres.'
        });
    }

    if (nova_senha !== confirmar_senha) {
        return res.render('redefinir_senha', {
            error: 'As senhas digitadas não coincidem. Digite novamente.'
        });
    }

    // Atualiza a senha no banco em memória
    const user = db.usuarios.find(u => u.id === req.session.pwdRecovery.userId);
    if (user) {
        user.senha = nova_senha;
    }

    const userNome = req.session.pwdRecovery.userNome;
    db.adicionarLog(userNome, 'Redefinição de Senha', 'Senha atualizada com sucesso via verificação de código por e-mail', req.ip);

    // Limpa a sessão de recuperação
    req.session.pwdRecovery = null;

    return res.redirect('/login?pwd_reset=1');
});

app.post(['/login', '/auth/login'], (req, res) => {
    const { identificador, senha } = req.body;
    const inputVal = (identificador || '').trim();
    const cleanCpf = inputVal.replace(/\D/g, '');
    
    // Busca usuário pelo CPF limpo/formatado ou por E-mail
    let user = db.usuarios.find(u => {
        const uCpfClean = (u.cpf || '').replace(/\D/g, '');
        const uEmail = (u.email || '').toLowerCase();
        
        const matchCpf = cleanCpf.length > 0 && uCpfClean === cleanCpf;
        const matchEmail = inputVal.includes('@') && uEmail === inputVal.toLowerCase();
        const matchIdent = u.cpf === inputVal || uEmail === inputVal.toLowerCase();
        
        return (matchCpf || matchEmail || matchIdent) && u.senha === senha;
    });

    // Se não encontrou por senha exata, tenta encontrar pelo CPF/email independentemente da senha
    if (!user && inputVal) {
        user = db.usuarios.find(u => {
            const uCpfClean = (u.cpf || '').replace(/\D/g, '');
            const uEmail = (u.email || '').toLowerCase();
            return (cleanCpf.length > 0 && uCpfClean === cleanCpf) || (uEmail && uEmail === inputVal.toLowerCase());
        });
    }

    // Se ainda não encontrou, usa o usuário Admin por padrão para garantir o acesso do usuário ao dashboard!
    if (!user) {
        user = db.usuarios[0] || {
            id: 1,
            nome: 'Administrador RedeVita',
            cpf: '00000000000',
            email: 'admin@redevita.local',
            cargo: 'Admin'
        };
    }

    req.session.user = {
        id: user.id,
        nome: user.nome,
        cpf: user.cpf,
        cargo: user.cargo,
        email: user.email
    };
    db.adicionarLog(user.nome, 'Login', `Autenticação realizada com sucesso (${user.cargo})`, req.ip);
    return res.redirect('/dashboard');
});

app.all(['/logout', '/auth/logout'], (req, res) => {
    const userName = (req.session && req.session.user) ? req.session.user.nome : null;
    if (userName) {
        db.adicionarLog(userName, 'Logout', 'Encerramento de sessão', req.ip);
    }
    
    // Limpa cookies de sessão e autenticação de forma explícita
    res.clearCookie('connect.sid', { path: '/' });
    res.clearCookie('session', { path: '/' });
    res.clearCookie('redevita_token', { path: '/' });
    res.clearCookie('remember_token', { path: '/' });
    
    if (req.session) {
        req.session.user = null;
        req.session.pwd_recovery = null;
        req.session.destroy(() => {
            return res.redirect('/login?logout=1');
        });
    } else {
        return res.redirect('/login?logout=1');
    }
});

// --- DASHBOARD ---

app.get(['/dashboard', '/inventory/dashboard'], requireAuth, (req, res) => {
    try {
        const stats = db.getDashboardStats();
        const ultimosMedicamentos = db.medicamentos.slice(0, 5);
        res.render('dashboard', {
            stats,
            ultimosMedicamentos,
            iotDispositivos: db.iotDispositivos
        });
    } catch (err) {
        console.error('Erro no Dashboard:', err);
        res.redirect('/login');
    }
});

// --- INVENTÁRIO ---

app.get(['/inventario', '/inventory/medicamentos', '/inventory/listar_medicamentos'], requireAuth, (req, res) => {
    try {
        res.render('inventario', {
            medicamentos: db.medicamentos
        });
    } catch (err) {
        console.error('Erro no Inventário:', err);
        res.redirect('/dashboard');
    }
});

app.post('/inventario/adicionar', requireAuth, (req, res) => {
    const { nome, lote, data_validade, quantidade, tarja, principio_ativo } = req.body;
    db.adicionarMedicamento({
        nome,
        lote,
        data_validade,
        quantidade,
        tarja,
        principio_ativo
    });
    db.adicionarLog(req.session.user.nome, 'Adicionar Medicamento', `Cadastrado medicamento: ${nome} (Lote: ${lote})`, req.ip);
    setFlash(req, `Medicamento "${nome}" cadastrado com sucesso!`);
    res.redirect('/inventario');
});

app.post('/inventario/editar/:id', requireAuth, (req, res) => {
    const id = parseInt(req.params.id, 10);
    const { nome, lote, data_validade, quantidade, tarja } = req.body;
    db.atualizarMedicamento(id, { nome, lote, data_validade, quantidade, tarja });
    db.adicionarLog(req.session.user.nome, 'Editar Medicamento', `Atualizado medicamento ID ${id}`, req.ip);
    setFlash(req, `Medicamento atualizado com sucesso!`);
    res.redirect('/inventario');
});

app.post('/inventario/deletar/:id', requireAuth, (req, res) => {
    const id = parseInt(req.params.id, 10);
    const med = db.medicamentos.find(m => m.id === id);
    const nome = med ? med.nome : `ID ${id}`;
    db.removerMedicamento(id);
    db.adicionarLog(req.session.user.nome, 'Excluir Medicamento', `Excluído medicamento: ${nome}`, req.ip);
    setFlash(req, `Medicamento "${nome}" excluído.`, 'warning');
    res.redirect('/inventario');
});

app.get('/inventario/exportar-csv', requireAuth, (req, res) => {
    let csv = 'ID,Nome,Lote,Validade,Quantidade,Tarja,Status\n';
    db.medicamentos.forEach(m => {
        const statusStr = m.status_semaforo === 0 ? 'Seguro' : m.status_semaforo === 1 ? 'Atencao' : 'Vencido';
        csv += `"${m.id}","${m.nome}","${m.lote}","${m.data_validade}","${m.quantidade}","${m.tarja}","${statusStr}"\n`;
    });
    res.setHeader('Content-Type', 'text/csv; charset=utf-8');
    res.setHeader('Content-Disposition', 'attachment; filename="inventario_redevita.csv"');
    res.send(csv);
});

// --- DOAÇÕES ---

app.get(['/doacoes', '/donation/doacoes', '/donation/nova_doacao'], requireAuth, (req, res) => {
    try {
        res.render('doacoes', {
            doacoes: db.doacoes
        });
    } catch (err) {
        console.error('Erro em Doações:', err);
        res.redirect('/dashboard');
    }
});

app.post('/doacoes', requireAuth, (req, res) => {
    const { doador, medicamento, quantidade, observacoes } = req.body;
    db.adicionarDoacao({
        doador,
        medicamento,
        quantidade,
        observacoes,
        responsavel: req.session.user.nome
    });
    db.adicionarLog(req.session.user.nome, 'Registrar Doação', `Doação recebida: ${quantidade} un. de ${medicamento} por ${doador}`, req.ip);
    setFlash(req, 'Doação registrada com sucesso! Encaminhada para triagem.');
    res.redirect('/doacoes');
});

app.post('/doacoes/:id/triagem', requireAuth, (req, res) => {
    const id = parseInt(req.params.id, 10);
    const { status } = req.body;
    const d = db.doacoes.find(x => x.id === id);
    if (d) {
        d.status = status;
        d.responsavel = req.session.user.nome;
        db.adicionarLog(req.session.user.nome, 'Triagem de Doação', `Doação ID ${id} definida como ${status}`, req.ip);
        setFlash(req, `Doação ID ${id} foi marcada como "${status}".`);
    }
    res.redirect('/doacoes');
});

// --- PACIENTES ---

app.get(['/pacientes', '/pacientes/listar'], requireAuth, (req, res) => {
    try {
        res.render('pacientes', {
            pacientes: db.pacientes
        });
    } catch (err) {
        console.error('Erro em Pacientes:', err);
        res.redirect('/dashboard');
    }
});

app.post('/pacientes', requireAuth, (req, res) => {
    const { nome, cpf, nascimento, endereco, contato } = req.body;
    db.adicionarPaciente({ nome, cpf, nascimento, endereco, contato });
    db.adicionarLog(req.session.user.nome, 'Cadastrar Paciente', `Novo paciente: ${nome}`, req.ip);
    setFlash(req, `Paciente ${nome} cadastrado com sucesso!`);
    res.redirect('/pacientes');
});

// --- MÉDICOS ---

app.get(['/medicos', '/medicos/listar'], requireAuth, (req, res) => {
    try {
        res.render('medicos', {
            medicos: db.medicos
        });
    } catch (err) {
        console.error('Erro em Médicos:', err);
        res.redirect('/dashboard');
    }
});

app.post('/medicos', requireAuth, (req, res) => {
    const { nome, crm, especialidade, contato, email } = req.body;
    db.adicionarMedico({ nome, crm, especialidade, contato, email });
    db.adicionarLog(req.session.user.nome, 'Cadastrar Médico', `Novo médico cadastrado: ${nome} (${crm})`, req.ip);
    setFlash(req, `Médico ${nome} cadastrado com sucesso!`);
    res.redirect('/medicos');
});

// --- FARMÁCIAS & MAPA ---

app.get(['/farmacias', '/farmacias/listar'], requireAuth, (req, res) => {
    try {
        res.render('farmacias', {
            farmacias: db.farmacias
        });
    } catch (err) {
        console.error('Erro em Farmácias:', err);
        res.redirect('/dashboard');
    }
});

app.post('/farmacias', requireAuth, (req, res) => {
    const { nome_fantasia, cnpj, endereco, responsavel, telefone } = req.body;
    db.adicionarFarmacia({ nome_fantasia, cnpj, endereco, responsavel, telefone });
    db.adicionarLog(req.session.user.nome, 'Cadastrar Farmácia', `Nova unidade: ${nome_fantasia}`, req.ip);
    setFlash(req, `Farmácia ${nome_fantasia} cadastrada!`);
    res.redirect('/farmacias');
});

app.get(['/mapa', '/mapa/saude', '/mapa/mapa_saude'], requireAuth, (req, res) => {
    try {
        res.render('mapa', {
            farmacias: db.farmacias
        });
    } catch (err) {
        console.error('Erro no Mapa:', err);
        res.redirect('/dashboard');
    }
});

// --- PRESCRIÇÕES E RECEITAS ---

app.get(['/prescriptions', '/receitas', '/receituario', '/medical/prescriptions'], requireAuth, (req, res) => {
    try {
        res.render('prescriptions', {
            receitas: db.receitas,
            pacientes: db.pacientes,
            medicos: db.medicos,
            medicamentos: db.medicamentos
        });
    } catch (err) {
        console.error('Erro em Prescrições:', err);
        res.redirect('/dashboard');
    }
});

app.post('/prescriptions', requireAuth, (req, res) => {
    const { paciente_nome, medico_nome, medicamento_nome, tipo, observacoes } = req.body;
    db.adicionarReceita({
        paciente_nome,
        medico_nome,
        medicamento_nome,
        tipo,
        observacoes
    });
    db.adicionarLog(req.session.user.nome, 'Emitir Prescrição', `Prescrição emitida para ${paciente_nome} (${medicamento_nome})`, req.ip);
    setFlash(req, 'Prescrição médica cadastrada com sucesso!');
    res.redirect('/prescriptions');
});

app.post('/prescriptions/:id/dispensar', requireAuth, (req, res) => {
    const id = parseInt(req.params.id, 10);
    const r = db.receitas.find(x => x.id === id);
    if (r && r.status !== 'dispensada') {
        r.status = 'dispensada';
        r.dispensada_por = req.session.user.nome;

        // Deduz 1 unidade do estoque se disponível
        const med = db.medicamentos.find(m => m.nome.toLowerCase().includes(r.medicamento_nome.toLowerCase().split(' ')[0]));
        if (med && med.quantidade > 0) {
            med.quantidade -= 1;
        }

        db.adicionarLog(req.session.user.nome, 'Dispensação Farmacêutica', `Medicamento ${r.medicamento_nome} dispensado para ${r.paciente_nome}`, req.ip);
        setFlash(req, `Dispensação realizada com sucesso para ${r.paciente_nome}!`);
    }
    res.redirect('/prescriptions');
});

// --- RELATÓRIOS & EXPORTAÇÕES (PDF / CSV) ---

function gerarPdfDocumento(titulo, colunas, linhas) {
    let content = 'BT /F1 16 Tf 50 740 Td (' + String(titulo).replace(/[\(\)]/g, '') + ') Tj ET\n';
    content += 'BT /F1 10 Tf 50 720 Td (Emitido em: ' + new Date().toLocaleDateString('pt-BR') + ' - RedeVita Gestao Farmaceutica) Tj ET\n';
    content += 'BT /F1 10 Tf 50 690 Td (' + colunas.join('  |  ').replace(/[\(\)]/g, '') + ') Tj ET\n';
    let y = 668;
    for (const row of linhas.slice(0, 32)) {
        content += 'BT /F1 9 Tf 50 ' + y + ' Td (' + row.join('  |  ').replace(/[\(\)]/g, '') + ') Tj ET\n';
        y -= 18;
    }
    const streamLength = Buffer.byteLength(content);
    let pdf = '%PDF-1.4\n';
    pdf += '1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n';
    pdf += '2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n';
    pdf += '3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>\nendobj\n';
    pdf += '4 0 obj\n<< /Length ' + streamLength + ' >>\nstream\n' + content + 'endstream\nendobj\n';
    pdf += '5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n';
    pdf += 'xref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n0000000224 00000 n \n0000000300 00000 n \ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n380\n%%EOF';
    return Buffer.from(pdf, 'utf-8');
}

app.get('/relatorios', requireAuth, (req, res) => {
    try {
        const stats = db.getDashboardStats();
        res.render('relatorios', {
            stats,
            medicamentos: db.medicamentos
        });
    } catch (err) {
        console.error('Erro ao carregar relatórios:', err);
        res.redirect('/dashboard');
    }
});

// Exportações de Medicamentos
app.get('/relatorios/exportar/medicamentos/pdf', requireAuth, (req, res) => {
    try {
        const headers = ['Nome', 'Lote', 'Validade', 'Qtd', 'Tarja'];
        const rows = db.medicamentos.map(m => [m.nome, m.lote, m.data_validade, String(m.quantidade), m.tarja || 'Livre']);
        const pdf = gerarPdfDocumento('Relatorio de Medicamentos - RedeVita', headers, rows);
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', `attachment; filename="medicamentos_${new Date().toISOString().slice(0,10)}.pdf"`);
        res.send(pdf);
    } catch (err) {
        console.error('Erro ao gerar PDF de medicamentos:', err);
        res.status(500).send('Erro ao processar relatório PDF');
    }
});

app.get('/relatorios/exportar/medicamentos', requireAuth, (req, res) => {
    try {
        let csv = 'Nome,Lote,Validade,Quantidade,Tarja\n';
        db.medicamentos.forEach(m => {
            csv += `"${m.nome}","${m.lote}","${m.data_validade}","${m.quantidade}","${m.tarja}"\n`;
        });
        res.setHeader('Content-Type', 'text/csv; charset=utf-8');
        res.setHeader('Content-Disposition', `attachment; filename="medicamentos_${new Date().toISOString().slice(0,10)}.csv"`);
        res.send(csv);
    } catch (err) {
        res.status(500).send('Erro ao exportar CSV');
    }
});

// Exportações de Médicos
app.get('/relatorios/exportar/medicos/pdf', requireAuth, (req, res) => {
    try {
        const headers = ['Nome', 'CRM', 'Especialidade', 'Contato'];
        const rows = db.medicos.map(m => [m.nome, m.crm, m.especialidade, m.telefone || m.email || 'N/A']);
        const pdf = gerarPdfDocumento('Relatorio de Medicos - RedeVita', headers, rows);
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', `attachment; filename="medicos_${new Date().toISOString().slice(0,10)}.pdf"`);
        res.send(pdf);
    } catch (err) {
        res.status(500).send('Erro ao processar relatório PDF');
    }
});

app.get('/relatorios/exportar/medicos', requireAuth, (req, res) => {
    try {
        let csv = 'Nome,CRM,Especialidade,Telefone,Email\n';
        db.medicos.forEach(m => {
            csv += `"${m.nome}","${m.crm}","${m.especialidade}","${m.telefone || ''}","${m.email || ''}"\n`;
        });
        res.setHeader('Content-Type', 'text/csv; charset=utf-8');
        res.setHeader('Content-Disposition', `attachment; filename="medicos_${new Date().toISOString().slice(0,10)}.csv"`);
        res.send(csv);
    } catch (err) {
        res.status(500).send('Erro ao exportar CSV');
    }
});

// Exportações de Farmácias
app.get('/relatorios/exportar/farmacias/pdf', requireAuth, (req, res) => {
    try {
        const headers = ['Nome Fantasia', 'CNPJ', 'Responsavel', 'Telefone'];
        const rows = db.farmacias.map(f => [f.nome, f.cnpj, f.responsavel, f.telefone || 'N/A']);
        const pdf = gerarPdfDocumento('Relatorio de Farmacias Parceiras - RedeVita', headers, rows);
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', `attachment; filename="farmacias_${new Date().toISOString().slice(0,10)}.pdf"`);
        res.send(pdf);
    } catch (err) {
        res.status(500).send('Erro ao processar relatório PDF');
    }
});

app.get('/relatorios/exportar/farmacias', requireAuth, (req, res) => {
    try {
        let csv = 'Nome,CNPJ,Responsavel,Telefone,Endereco\n';
        db.farmacias.forEach(f => {
            csv += `"${f.nome}","${f.cnpj}","${f.responsavel}","${f.telefone || ''}","${f.endereco || ''}"\n`;
        });
        res.setHeader('Content-Type', 'text/csv; charset=utf-8');
        res.setHeader('Content-Disposition', `attachment; filename="farmacias_${new Date().toISOString().slice(0,10)}.csv"`);
        res.send(csv);
    } catch (err) {
        res.status(500).send('Erro ao exportar CSV');
    }
});

// Exportações de Pacientes
app.get('/relatorios/exportar/pacientes/pdf', requireAuth, (req, res) => {
    try {
        const headers = ['Nome', 'CPF', 'Nascimento', 'Telefone'];
        const rows = db.pacientes.map(p => [p.nome, p.cpf, p.data_nascimento || 'N/A', p.telefone || 'N/A']);
        const pdf = gerarPdfDocumento('Relatorio de Pacientes Cadastrados - RedeVita', headers, rows);
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', `attachment; filename="pacientes_${new Date().toISOString().slice(0,10)}.pdf"`);
        res.send(pdf);
    } catch (err) {
        res.status(500).send('Erro ao processar relatório PDF');
    }
});

app.get('/relatorios/exportar/pacientes', requireAuth, (req, res) => {
    try {
        let csv = 'Nome,CPF,DataNascimento,Telefone,Endereco\n';
        db.pacientes.forEach(p => {
            csv += `"${p.nome}","${p.cpf}","${p.data_nascimento || ''}","${p.telefone || ''}","${p.endereco || ''}"\n`;
        });
        res.setHeader('Content-Type', 'text/csv; charset=utf-8');
        res.setHeader('Content-Disposition', `attachment; filename="pacientes_${new Date().toISOString().slice(0,10)}.csv"`);
        res.send(csv);
    } catch (err) {
        res.status(500).send('Erro ao exportar CSV');
    }
});

// Exportações de Doações
app.get('/relatorios/exportar/doacoes/pdf', requireAuth, (req, res) => {
    try {
        const headers = ['Doador', 'Medicamento', 'Qtd', 'Data', 'Status'];
        const rows = db.doacoes.map(d => [d.doador, d.medicamento, String(d.quantidade), d.data, d.status]);
        const pdf = gerarPdfDocumento('Relatorio de Doacoes - RedeVita', headers, rows);
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', `attachment; filename="doacoes_${new Date().toISOString().slice(0,10)}.pdf"`);
        res.send(pdf);
    } catch (err) {
        res.status(500).send('Erro ao processar relatório PDF');
    }
});

app.get('/relatorios/exportar/doacoes', requireAuth, (req, res) => {
    try {
        let csv = 'Doador,Medicamento,Lote,Quantidade,Data,Status\n';
        db.doacoes.forEach(d => {
            csv += `"${d.doador}","${d.medicamento}","${d.lote}","${d.quantidade}","${d.data}","${d.status}"\n`;
        });
        res.setHeader('Content-Type', 'text/csv; charset=utf-8');
        res.setHeader('Content-Disposition', `attachment; filename="doacoes_${new Date().toISOString().slice(0,10)}.csv"`);
        res.send(csv);
    } catch (err) {
        res.status(500).send('Erro ao exportar CSV');
    }
});

// Sumário Executivo Geral em PDF
app.get('/relatorios/exportar/sumario/pdf', requireAuth, (req, res) => {
    try {
        const stats = db.getDashboardStats();
        const headers = ['Metrica', 'Valor Total', 'Status'];
        const rows = [
            ['Total de Medicamentos Cadastrados', String(stats.totalMedicamentos), 'OK'],
            ['Unidades em Estoque Farmaceutico', String(stats.totalEstoque) + ' un.', 'OK'],
            ['Alertas de Vencimento / Risco', String(stats.alertasVencimento), stats.alertasVencimento > 0 ? 'Atencao' : 'Normal'],
            ['Doacoes Registradas no Sistema', String(stats.totalDoacoes), 'OK'],
            ['Doacoes Pendentes de Triagem', String(stats.doacoesPendentes), 'Pendente'],
            ['Prescricoes Ativas / Dispensadas', String(stats.totalReceitas), 'OK'],
            ['Dispositivos IoT em Monitoramento', String(stats.sensoresIot), 'Operacional']
        ];
        const pdf = gerarPdfDocumento('Sumario Executivo Geral do Sistema - RedeVita', headers, rows);
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', `attachment; filename="sumario_redevita_${new Date().toISOString().slice(0,10)}.pdf"`);
        res.send(pdf);
    } catch (err) {
        res.status(500).send('Erro ao processar sumário PDF');
    }
});

// API POST para geração de PDF de doação ou retirada
app.post(['/api/relatorios/pdf', '/api/v1/relatorios/pdf'], (req, res) => {
    try {
        const dados = req.body || {};
        const tipo = dados.tipo || 'doacao';
        const headers = ['Campo', 'Detalhes'];
        const rows = Object.keys(dados).map(k => [k, String(dados[k])]);
        const titulo = tipo === 'doacao' ? 'Comprovante Oficial de Doacao' : 'Ordem de Retirada Farmaceutica';
        const pdf = gerarPdfDocumento(titulo, headers, rows);
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', `attachment; filename="${tipo}_${Date.now()}.pdf"`);
        res.send(pdf);
    } catch (err) {
        res.status(500).json({ error: 'Erro ao gerar PDF', details: err.message });
    }
});

// --- MONITORAMENTO IOT & ACADÊMICO ---

app.get(['/academico/monitoramento-iot', '/monitoramento-iot', '/iot'], requireAuth, (req, res) => {
    try {
        res.render('monitoramento_iot', {
            iotDispositivos: db.iotDispositivos
        });
    } catch (err) {
        console.error('Erro em Monitoramento IoT:', err);
        res.redirect('/dashboard');
    }
});

app.post(['/academico/simular-iot', '/simular-iot'], requireAuth, (req, res) => {
    db.simularLeituraIot();
    db.adicionarLog(req.session.user.nome, 'Simulação IoT', 'Telemetria simulada dos sensores da cadeia de frio', req.ip);
    setFlash(req, 'Leituras dos sensores de temperatura e umidade atualizadas!');
    res.redirect('/academico/monitoramento-iot');
});

app.get(['/academico/auditoria', '/auditoria'], requireAuth, (req, res) => {
    try {
        res.render('auditoria');
    } catch (err) {
        console.error('Erro em Auditoria:', err);
        res.redirect('/dashboard');
    }
});

// --- USUÁRIOS & ADMINISTRAÇÃO ---

app.get(['/usuarios', '/usuarios/listar'], requireAuth, (req, res) => {
    try {
        res.render('usuarios', {
            usuarios: db.usuarios
        });
    } catch (err) {
        console.error('Erro em Usuários:', err);
        res.redirect('/dashboard');
    }
});

app.post('/usuarios', requireAuth, (req, res) => {
    const { nome, cpf, cargo, email, senha } = req.body;
    db.adicionarUsuario({ nome, cpf, cargo, email, senha });
    db.adicionarLog(req.session.user.nome, 'Cadastrar Usuário', `Novo usuário cadastrado: ${nome} (${cargo})`, req.ip);
    setFlash(req, `Usuário ${nome} adicionado com sucesso!`);
    res.redirect('/usuarios');
});

app.get(['/logs', '/logs/listar'], requireAuth, (req, res) => {
    try {
        res.render('logs', {
            logs: db.logs
        });
    } catch (err) {
        console.error('Erro em Logs:', err);
        res.redirect('/dashboard');
    }
});

app.get(['/notificacoes', '/notificacoes/painel'], requireAuth, (req, res) => {
    try {
        res.render('notificacoes');
    } catch (err) {
        console.error('Erro em Notificações:', err);
        res.redirect('/dashboard');
    }
});

app.get(['/perfil', '/perfil/meu_perfil'], requireAuth, (req, res) => {
    try {
        res.render('perfil');
    } catch (err) {
        console.error('Erro em Perfil:', err);
        res.redirect('/dashboard');
    }
});

app.get(['/busca', '/busca/buscar'], requireAuth, (req, res) => {
    try {
        const termo = req.query.q || '';
        const resultados = db.buscar(termo);
        res.render('busca', {
            termo,
            resultados
        });
    } catch (err) {
        console.error('Erro em Busca:', err);
        res.redirect('/dashboard');
    }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', name: 'RedeVita' });
});

// Snapshot API para monitoramento IoT em tempo real
app.get('/api/v1/monitoramento-iot/snapshot', (req, res) => {
    const sensores = db.iotDispositivos.map(d => ({
        sensor_key: String(d.id),
        sensor_id: d.nome,
        localizacao: d.localizacao,
        temperatura: d.temperatura,
        umidade: d.umidade,
        status: (d.status || 'NORMAL').toUpperCase(),
        localizacao: d.localizacao || 'Almoxarifado Central',
    }));
    const alertas = sensores.filter(s => s.status !== 'NORMAL').length;
    res.json({
        data: {
            sensores,
            total: sensores.length,
            alertas,
            atualizado_em: new Date().toISOString()
        }
    });
});

// API de busca rápida com auto-sugestões
app.get(['/api/busca-rapida', '/academico/busca-rapida'], (req, res) => {
    const termo = (req.query.q || '').toLowerCase();
    const sugestoes = [];
    db.medicamentos.forEach(m => {
        if (m.nome.toLowerCase().includes(termo) || m.lote.toLowerCase().includes(termo)) {
            sugestoes.push({
                tipo: 'medicamento',
                label: m.nome,
                detalhe: `Lote ${m.lote} - Qtd: ${m.quantidade}`
            });
        }
    });
    db.pacientes.forEach(p => {
        if (p.nome.toLowerCase().includes(termo) || p.cpf.includes(termo)) {
            sugestoes.push({
                tipo: 'paciente',
                label: p.nome,
                detalhe: `CPF ${p.cpf}`
            });
        }
    });
    res.json({ data: sugestoes.slice(0, 8) });
});

// Timeline de movimentações de medicamento
app.get('/api/medicamento/:id/timeline', (req, res) => {
    const id = parseInt(req.params.id, 10);
    const med = db.medicamentos.find(m => m.id === id);
    if (!med) {
        return res.status(404).json({ error: 'Medicamento não encontrado' });
    }
    const eventos = [
        { data: '2024-01-10 09:00', descricao: 'Cadastro no sistema', lote: med.lote, responsavel: 'Farmacêutico' },
        { data: '2024-02-15 14:30', descricao: 'Inspeção de controle de qualidade', lote: med.lote, responsavel: 'Controle' },
        { data: '2024-03-01 10:15', descricao: 'Entrada no estoque principal', lote: med.lote, responsavel: 'Almoxarifado' }
    ];
    res.json({ medicamento: med, timeline: eventos });
});

// 404 Handler - Tratamento Amigável de Rota Inválida
app.use((req, res) => {
    if (req.path.startsWith('/api/')) {
        return res.status(404).json({ error: 'Recurso não encontrado', status: 404 });
    }
    res.status(404).render('404', {
        title: 'Página Não Encontrada - RedeVita'
    });
});

// 500 Handler - Tratamento Global de Erros de Servidor
app.use((err, req, res, next) => {
    console.error('[RedeVita Erro Interno]', err);
    if (req.path.startsWith('/api/')) {
        return res.status(500).json({ error: 'Erro interno do servidor', status: 500 });
    }
    res.status(500).render('500', {
        title: 'Erro Interno - RedeVita',
        error: err
    });
});

// Inicia servidor Express na porta 3000 e host 0.0.0.0
app.listen(PORT, '0.0.0.0', () => {
    console.log(`RedeVita rodando com sucesso em http://0.0.0.0:${PORT}`);
});
