document.addEventListener('DOMContentLoaded', () => {

    function aplicarMascaraCPF(input) {
        input.addEventListener('input', (e) => {
            let v = e.target.value.replace(/\D/g, '').slice(0, 11);
            v = v.replace(/(\d{3})(\d)/, '$1.$2');
            v = v.replace(/(\d{3})(\d)/, '$1.$2');
            v = v.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
            e.target.value = v;
        });
        
        input.addEventListener('blur', (e) => {
            const valor = e.target.value.replace(/\D/g, '');
            if (valor.length === 11) {
                const cpf = valor;
                let soma = 0;
                let resto;
                
                for (let i = 1; i <= 9; i++) {
                    soma = soma + parseInt(cpf.substring(i-1, i)) * (11 - i);
                }
                resto = (soma * 10) % 11;
                if ((resto === 10) || (resto === 11)) resto = 0;
                if (resto !== parseInt(cpf.substring(9, 10))) {
                    e.target.style.borderColor = '#ef4444';
                } else {
                    soma = 0;
                    for (let i = 1; i <= 10; i++) {
                        soma = soma + parseInt(cpf.substring(i-1, i)) * (12 - i);
                    }
                    resto = (soma * 10) % 11;
                    if ((resto === 10) || (resto === 11)) resto = 0;
                    if (resto !== parseInt(cpf.substring(10, 11))) {
                        e.target.style.borderColor = '#ef4444';
                    } else {
                        e.target.style.borderColor = 'rgba(56, 189, 248, 0.2)';
                    }
                }
            }
        });
    }

    function aplicarMascaraCNPJ(input) {
        input.addEventListener('input', (e) => {
            let v = e.target.value.replace(/\D/g, '').slice(0, 14);
            v = v.replace(/(\d{2})(\d)/, '$1.$2');
            v = v.replace(/(\d{3})(\d)/, '$1.$2');
            v = v.replace(/(\d{3})(\d)/, '$1/$2');
            v = v.replace(/(\d{4})(\d{1,2})$/, '$1-$2');
            e.target.value = v;
        });
    }

    function aplicarMascaraCRM(input) {
        input.addEventListener('input', (e) => {
            let v = e.target.value.replace(/\D/g, '').slice(0, 10);
            e.target.value = v;
        });
    }

    function aplicarMascaraTel(input) {
        input.addEventListener('input', (e) => {
            let v = e.target.value.replace(/\D/g, '').slice(0, 11);
            if (v.length <= 10) {
                v = v.replace(/(\d{2})(\d)/, '($1) $2');
                v = v.replace(/(\d{4})(\d{1,4})$/, '$1-$2');
            } else {
                v = v.replace(/(\d{2})(\d)/, '($1) $2');
                v = v.replace(/(\d{5})(\d{1,4})$/, '$1-$2');
            }
            e.target.value = v;
        });
    }

    function aplicarMascaraCEP(input) {
        input.addEventListener('input', (e) => {
            let v = e.target.value.replace(/\D/g, '').slice(0, 8);
            v = v.replace(/(\d{5})(\d{1,3})/, '$1-$2');
            e.target.value = v;
        });
        
        input.addEventListener('blur', async (e) => {
            const cep = e.target.value.replace(/\D/g, '');
            if (cep.length === 8) {
                try {
                    const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
                    const data = await response.json();
                    
                    if (!data.erro) {
                        const enderecoInput = document.querySelector('input[name="endereco"]');
                        if (enderecoInput) {
                            enderecoInput.value = `${data.logradouro}, ${data.bairro}, ${data.localidade} - ${data.uf}`;
                            enderecoInput.style.borderColor = '#10b981';
                        }
                    }
                } catch (error) {
                    console.error('Erro ao buscar CEP:', error);
                }
            }
        });
    }

    document.querySelectorAll('.mask-cpf').forEach(aplicarMascaraCPF);
    document.querySelectorAll('.mask-cnpj').forEach(aplicarMascaraCNPJ);
    document.querySelectorAll('.mask-crm').forEach(aplicarMascaraCRM);
    document.querySelectorAll('.mask-tel').forEach(aplicarMascaraTel);
    document.querySelectorAll('.mask-cep').forEach(aplicarMascaraCEP);

    const cpfInput = document.getElementById('cpf');
    if (cpfInput && !cpfInput.classList.contains('mask-cpf')) {
        aplicarMascaraCPF(cpfInput);
    }

    const cnpjInput = document.getElementById('cnpj');
    if (cnpjInput && !cnpjInput.classList.contains('mask-cnpj')) {
        aplicarMascaraCNPJ(cnpjInput);
    }

    document.querySelectorAll('input[type="number"]').forEach((input) => {
        input.addEventListener('input', () => {
            const min = parseInt(input.min, 10);
            if (!isNaN(min) && parseFloat(input.value) < min) {
                input.value = min;
            }
        });
    });

    const hoje = new Date().toISOString().split('T')[0];
    document.querySelectorAll('input[type="date"].date-future').forEach((input) => {
        if (!input.getAttribute('min')) {
            input.setAttribute('min', hoje);
        }
    });
    document.querySelectorAll('input[type="date"].date-nascimento').forEach((input) => {
        input.setAttribute('min', '1900-01-01');
        input.setAttribute('max', hoje);
    });

    document.querySelectorAll('[data-table-search]').forEach((input) => {
        const table = document.getElementById(input.dataset.tableSearch);
        if (!table) return;

        input.addEventListener('input', (event) => {
            const termo = event.target.value.toLocaleLowerCase('pt-BR').trim();
            table.querySelectorAll('tbody tr').forEach((row) => {
                row.hidden = termo && !row.textContent.toLocaleLowerCase('pt-BR').includes(termo);
            });
        });
    });
});
