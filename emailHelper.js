/**
 * RedeVita - Helper para geração de E-mails Transacionais
 * Gera o template HTML corporativo para recuperação de senha com código de 6 dígitos.
 */

function gerarEmailRecuperacaoHTML({ nome, codigo, email, minutosValidade = 15 }) {
    // Formata o código com espaçamento visual para facilitar leitura
    const codigoFormatado = String(codigo).split('').join(' ');

    return `<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Código de Recuperação de Senha - RedeVita</title>
  <style>
    body {
      margin: 0;
      padding: 0;
      background-color: #0b0f17;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      color: #e2e8f0;
      -webkit-font-smoothing: antialiased;
    }
    .wrapper {
      width: 100%;
      background-color: #0b0f17;
      padding: 40px 16px;
      box-sizing: border-box;
    }
    .container {
      max-width: 580px;
      margin: 0 auto;
      background-color: #151c2a;
      border: 1px solid #2d3748;
      border-radius: 20px;
      overflow: hidden;
      box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
    }
    .header {
      padding: 36px 32px 28px;
      text-align: center;
      background: linear-gradient(180deg, rgba(14, 165, 233, 0.12) 0%, rgba(21, 28, 42, 0) 100%);
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
    .logo-container {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      text-decoration: none;
      margin-bottom: 16px;
    }
    .logo-text {
      font-size: 26px;
      font-weight: 800;
      color: #ffffff;
      letter-spacing: -0.5px;
    }
    .logo-text span {
      color: #38bdf8;
    }
    .badge-tag {
      display: inline-block;
      padding: 6px 14px;
      background-color: rgba(56, 189, 248, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: #38bdf8;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      border-radius: 20px;
      margin-top: 8px;
    }
    .content {
      padding: 36px 32px;
    }
    h1 {
      font-size: 20px;
      font-weight: 700;
      color: #f8fafc;
      margin: 0 0 16px 0;
      line-height: 1.4;
    }
    p {
      font-size: 15px;
      line-height: 1.65;
      color: #94a3b8;
      margin: 0 0 20px 0;
    }
    .code-card {
      background-color: #0b0f17;
      border: 1.5px dashed #0284c7;
      border-radius: 16px;
      padding: 24px;
      text-align: center;
      margin: 28px 0;
      box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.4);
    }
    .code-label {
      font-size: 12px;
      font-weight: 600;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 2px;
      margin-bottom: 10px;
    }
    .code-number {
      font-family: 'Courier New', Courier, monospace;
      font-size: 38px;
      font-weight: 800;
      color: #38bdf8;
      letter-spacing: 10px;
      margin: 8px 0;
      text-shadow: 0 0 20px rgba(56, 189, 248, 0.35);
    }
    .expiry-note {
      font-size: 13px;
      color: #f59e0b;
      font-weight: 500;
      margin-top: 10px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .security-box {
      background: rgba(15, 23, 42, 0.6);
      border-left: 3px solid #0ea5e9;
      border-radius: 0 10px 10px 0;
      padding: 14px 18px;
      margin: 24px 0 10px;
    }
    .security-box p {
      font-size: 13px;
      color: #94a3b8;
      margin: 0;
      line-height: 1.5;
    }
    .footer {
      padding: 24px 32px;
      background-color: #0f172a;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      text-align: center;
    }
    .footer p {
      font-size: 12px;
      color: #64748b;
      margin: 0 0 6px 0;
    }
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="container">
      <div class="header">
        <div class="logo-container">
          <svg width="34" height="34" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="36" height="36" rx="9" fill="#0284C7"/>
            <path d="M18 7V29M7 18H29" stroke="white" stroke-width="4.5" stroke-linecap="round"/>
            <path d="M12 21L15 17L19 23L22 19L25 21" stroke="#38BDF8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <div class="logo-text">Rede<span>Vita</span></div>
        </div>
        <br>
        <span class="badge-tag">Segurança em Saúde</span>
      </div>

      <div class="content">
        <h1>Código de Verificação</h1>
        <p>Olá, <strong style="color: #f8fafc;">${nome || 'Usuário'}</strong>,</p>
        <p>
          Recebemos uma solicitação de redefinição de senha para sua conta vinculada a este endereço de e-mail (${email}).
          Utilize o código de verificação de 6 dígitos abaixo para autenticar sua solicitação:
        </p>

        <div class="code-card">
          <div class="code-label">Seu Código de Confirmação</div>
          <div class="code-number">${codigoFormatado}</div>
          <div class="expiry-note">
            ⏱ Válido por ${minutosValidade} minutos
          </div>
        </div>

        <div class="security-box">
          <p>
            <strong>Aviso de Segurança:</strong> Nunca compartilhe este código com ninguém. A equipe do RedeVita nunca solicitará seu código por mensagem ou telefone. Caso não tenha solicitado esta alteração, ignore este e-mail ou notifique o suporte.
          </p>
        </div>
      </div>

      <div class="footer">
        <p><strong>RedeVita &copy; 2026</strong> - Gestão Integrada de Medicamentos e Doações</p>
        <p>Este é um e-mail transacional automatizado do sistema de segurança. Por favor, não responda.</p>
      </div>
    </div>
  </div>
</body>
</html>`;
}

module.exports = {
    gerarEmailRecuperacaoHTML
};
