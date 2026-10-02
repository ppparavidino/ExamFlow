// ==========================================================
// CONFIGURAÇÃO
// ==========================================================
const API_URL = window.location.origin;

// ==========================================================
// PROTEÇÃO DE LOGIN
// ==========================================================
const usuarioSalvo = localStorage.getItem("examflow_usuario");

if (!usuarioSalvo) {
    window.location.href = "/frontend/login.html";
} else {
    const usuario = JSON.parse(usuarioSalvo);
    const bemVindo = document.getElementById("bem-vindo");
    if (bemVindo) {
        bemVindo.textContent = `Olá, ${usuario.nome}`;
    }
}

// ----- Sair -----
const btnSair = document.getElementById("btn-sair");
if (btnSair) {
    btnSair.addEventListener("click", () => {
        localStorage.removeItem("examflow_usuario");
        window.location.href = "/frontend/login.html";
    });
}

// ==========================================================
// PREENCHER MESES E ANO ATUAL
// ==========================================================
const selectMes = document.getElementById("mes");
const inputAno = document.getElementById("ano");

const nomesMeses = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

const hoje = new Date();

nomesMeses.forEach((nome, index) => {
    const option = document.createElement("option");
    option.value = index + 1;
    option.textContent = nome;
    if (index + 1 === hoje.getMonth() + 1) {
        option.selected = true;
    }
    selectMes.appendChild(option);
});

inputAno.value = hoje.getFullYear();

// ==========================================================
// BUSCAR PENDENTES (SEM DATA PREVISTA)
// ==========================================================
async function carregarPendentes() {
    const mes = selectMes.value;
    const ano = inputAno.value;
    const container = document.getElementById("tabela-pendentes");
    const totalEl = document.getElementById("total-pendentes");

    container.innerHTML = "<p>Carregando...</p>";

    try {
        const resposta = await fetch(
            `${API_URL}/exames/pendentes?ano=${ano}&mes=${mes}`
        );
        const dados = await resposta.json();

        if (dados.erro) {
            container.innerHTML = `<p class="mensagem erro">${dados.erro}</p>`;
            totalEl.textContent = "0";
            return;
        }

        totalEl.textContent = dados.total;

        if (!dados.pendentes.length) {
            container.innerHTML = "<p>Nenhum exame pendente neste mês.</p>";
            return;
        }

        // Agrupa por cargo
        const cargos = {};
        dados.pendentes.forEach(f => {
            const cargoKey = f.cargo || "Outros";
            if (!cargos[cargoKey]) cargos[cargoKey] = [];
            cargos[cargoKey].push(f);
        });

        let html = "";
        let totalExibidos = 0;

        // Para cada cargo, cria uma tabela
        for (const [cargo, funcionarios] of Object.entries(cargos)) {
            totalExibidos += funcionarios.length;
            
            html += `
                <h3 style="margin: 1.5rem 0 0.5rem 0; color: var(--gray-700); font-size: 1rem;">
                    🏷️ ${cargo} (${funcionarios.length})
                </h3>
                <table class="tabela">
                    <thead>
                        <tr>
                            <th>Matrícula</th>
                            <th>Nome</th>
                            <th>Tipo</th>
                            <th>Celular</th>
                            <th>Ação</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            for (const f of funcionarios) {
                html += `
                    <tr>
                        <td>${f.matricula}</td>
                        <td>${f.nome}</td>
                        <td><span class="badge-tipo">${f.tipo}</span></td>
                        <td>${f.celular || "—"}</td>
                        <td>
                            <button
                                type="button"
                                class="btn-agendar"
                                data-id="${f.id}"
                                data-nome="${f.nome}"
                                data-tipo="${f.tipo}"
                            >
                                📝 Agendar
                            </button>
                        </td>
                    </tr>
                `;
            }

            html += `
                    </tbody>
                </table>
            `;
        }

        html += `<p style="color: var(--gray-500); font-size: 0.9rem; margin-top: 1rem;">
            Total: ${totalExibidos} funcionários
        </p>`;

        container.innerHTML = html;

        // Estiliza badges
        document.querySelectorAll('.badge-tipo').forEach(el => {
            const texto = el.textContent;
            if (texto.includes('Oficina')) {
                el.style.cssText = 'background: #fef3c7; color: #92400e; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; display: inline-block;';
            } else if (texto.includes('1º Ano')) {
                el.style.cssText = 'background: #dbeafe; color: #1e40af; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; display: inline-block;';
            } else {
                el.style.cssText = 'background: #d1fae5; color: #065f46; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; display: inline-block;';
            }
        });

    } catch (erro) {
        console.error(erro);
        container.innerHTML =
            '<p class="mensagem erro">Não foi possível carregar os pendentes.</p>';
        totalEl.textContent = "0";
    }
}

document.getElementById("btn-buscar").addEventListener("click", carregarPendentes);

// Carrega automaticamente ao abrir
carregarPendentes();
carregarAgendados();

// ==========================================================
// PAINEL DE AGENDAMENTO
// ==========================================================
const painel = document.getElementById("painel-agendar");
const agendarMsg = document.getElementById("agendar-mensagem");

function abrirPainelAgendar(botao) {
    document.getElementById("agendar-id").value = botao.dataset.id;
    document.getElementById("agendar-tipo").value = botao.dataset.tipo;
    document.getElementById("agendar-funcionario").textContent =
        `Funcionário: ${botao.dataset.nome}`;

    document.getElementById("agendar-data").value = "";
    agendarMsg.textContent = "";
    agendarMsg.className = "mensagem";

    painel.classList.remove("oculto");
    painel.scrollIntoView({ behavior: "smooth", block: "start" });
}

// Delegação de clique nos botões Agendar
document.getElementById("tabela-pendentes").addEventListener("click", (event) => {
    const botao = event.target.closest(".btn-agendar");
    if (botao) {
        abrirPainelAgendar(botao);
    }
});

document.getElementById("btn-cancelar-agendar").addEventListener("click", () => {
    painel.classList.add("oculto");
});

// ==========================================================
// AGENDAR EXAME (VERSÃO SIMPLIFICADA)
// ==========================================================
document.getElementById("btn-confirmar-agendar").addEventListener("click", async () => {
    const funcionarioId = Number(document.getElementById("agendar-id").value);
    const tipo = document.getElementById("agendar-tipo").value;
    const dataISO = document.getElementById("agendar-data").value;

    if (!dataISO) {
        agendarMsg.textContent = "Selecione uma data para o exame.";
        agendarMsg.className = "mensagem erro";
        return;
    }

    // Converte yyyy-mm-dd → dd/mm/aaaa
    const [ano, mes, dia] = dataISO.split("-");
    const dataAgendada = `${dia}/${mes}/${ano}`;

    // Local e horário fixos
    const local = "Dual Saúde - Rua Almirante Teffé, 669 - Centro, Niterói";
    const horario = "07:00";

    agendarMsg.textContent = "Salvando...";
    agendarMsg.className = "mensagem";

    try {
        const resposta = await fetch(`${API_URL}/exames/agendar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                funcionario_id: funcionarioId,
                tipo: "PERIODICO",
                data_prevista: null,
                data_agendada: dataAgendada,
                horario: horario,
                local_exame: local,
            }),
        });

        const dados = await resposta.json();

        if (dados.erro) {
            agendarMsg.textContent = dados.erro;
            agendarMsg.className = "mensagem erro";
            return;
        }

        agendarMsg.textContent = dados.mensagem;
        agendarMsg.className = "mensagem ok";

        setTimeout(() => {
            painel.classList.add("oculto");
            carregarPendentes();
            carregarAgendados();
        }, 1000);
    } catch (erro) {
        console.error(erro);
        agendarMsg.textContent = "Falha ao conectar com a API.";
        agendarMsg.className = "mensagem erro";
    }
});

// ==========================================================
// CARREGAR AGENDADOS
// ==========================================================
async function carregarAgendados() {
    const container = document.getElementById("tabela-agendados");
    if (!container) return;

    container.innerHTML = "<p>Carregando...</p>";

    try {
        const resposta = await fetch(`${API_URL}/exames/agendados`);
        const dados = await resposta.json();

        if (dados.erro) {
            container.innerHTML = `<p class="mensagem erro">${dados.erro}</p>`;
            return;
        }

        if (!dados.agendados.length) {
            container.innerHTML = "<p>Nenhum exame agendado no momento.</p>";
            return;
        }

        let html = `
            <table class="tabela">
                <thead>
                    <tr>
                        <th>Matrícula</th>
                        <th>Nome</th>
                        <th>Data</th>
                        <th>Local</th>
                        <th>WhatsApp</th>
                    </tr>
                </thead>
                <tbody>
        `;

        for (const e of dados.agendados) {
            const botaoWhats = e.whatsapp_link
                ? `<a class="btn-whatsapp" href="${e.whatsapp_link}" target="_blank" rel="noopener">📱 WhatsApp</a>`
                : `<span class="sem-celular">Sem celular</span>`;

            html += `
                <tr>
                    <td>${e.matricula}</td>
                    <td>${e.nome}</td>
                    <td>${e.data_agendada}</td>
                    <td>${e.local_exame || "Dual Saúde"}</td>
                    <td>${botaoWhats}</td>
                </tr>
            `;
        }

        html += "</tbody></table>";
        container.innerHTML = html;
    } catch (erro) {
        console.error(erro);
        container.innerHTML =
            '<p class="mensagem erro">Não foi possível carregar os agendados.</p>';
    }
}

// ==========================================================
// MODAL DE ATUALIZAÇÃO DE FUNCIONÁRIOS
// ==========================================================

const modal = document.getElementById('modal-atualizacao');
const btnAbrirModal = document.getElementById('btn-atualizar-funcionarios');
const btnFecharModal = document.getElementById('btn-fechar-modal');
const inputArquivoModal = document.getElementById('arquivo-pdf-modal');
const btnAnalisarModal = document.getElementById('btn-analisar-modal');
const btnConfirmarModal = document.getElementById('btn-confirmar-modal');
const msgModal = document.getElementById('msg-modal');
const resumoDiv = document.getElementById('modal-resumo');

let arquivoAtualModal = null;

if (btnAbrirModal) {
    btnAbrirModal.addEventListener('click', function() {
        if (!modal) return;
        modal.classList.remove('oculto');
        document.body.style.overflow = 'hidden';
        if (inputArquivoModal) inputArquivoModal.value = '';
        if (resumoDiv) resumoDiv.style.display = 'none';
        if (btnConfirmarModal) btnConfirmarModal.disabled = true;
        if (msgModal) {
            msgModal.textContent = '';
            msgModal.className = 'mensagem';
        }
        arquivoAtualModal = null;
    });
}

function fecharModal() {
    if (modal) {
        modal.classList.add('oculto');
        document.body.style.overflow = 'auto';
    }
}

if (btnFecharModal) {
    btnFecharModal.addEventListener('click', fecharModal);
}

if (modal) {
    modal.addEventListener('click', function(event) {
        if (event.target === modal) {
            fecharModal();
        }
    });
}

function mostrarMsgModal(texto, tipo) {
    if (msgModal) {
        msgModal.textContent = texto;
        msgModal.className = 'mensagem' + (tipo ? ` ${tipo}` : '');
    }
}

if (btnAnalisarModal) {
    btnAnalisarModal.addEventListener('click', async function() {
        if (!inputArquivoModal) {
            mostrarMsgModal('Campo de arquivo não encontrado.', 'erro');
            return;
        }
        
        const arquivo = inputArquivoModal.files[0];

        if (!arquivo) {
            mostrarMsgModal('Selecione um arquivo PDF.', 'erro');
            return;
        }

        if (!arquivo.name.toLowerCase().endsWith('.pdf')) {
            mostrarMsgModal('O arquivo precisa ser PDF.', 'erro');
            return;
        }

        arquivoAtualModal = arquivo;
        if (btnConfirmarModal) btnConfirmarModal.disabled = true;
        
        mostrarMsgModal('Analisando PDF...', 'info');
        if (resumoDiv) resumoDiv.style.display = 'none';

        const formData = new FormData();
        formData.append('arquivo', arquivo);

        try {
            const resposta = await fetch(`${API_URL}/importacao/preview`, {
                method: 'POST',
                body: formData,
            });

            const dados = await resposta.json();

            if (dados.erro) {
                mostrarMsgModal(dados.erro, 'erro');
                return;
            }

            const totalEl = document.getElementById('r-total-modal');
            const novosEl = document.getElementById('r-novos-modal');
            const alteradosEl = document.getElementById('r-alterados-modal');
            const ausentesEl = document.getElementById('r-ausentes-modal');
            
            if (totalEl) totalEl.textContent = dados.resumo.total_pdf || 0;
            if (novosEl) novosEl.textContent = dados.resumo.novos || 0;
            if (alteradosEl) alteradosEl.textContent = dados.resumo.alterados || 0;
            if (ausentesEl) ausentesEl.textContent = dados.resumo.ausentes || 0;

            if (resumoDiv) resumoDiv.style.display = 'block';
            if (btnConfirmarModal) btnConfirmarModal.disabled = false;

            mostrarMsgModal(
                `✅ Análise concluída: ${dados.resumo.total_pdf} funcionários no PDF.`,
                'ok'
            );

        } catch (erro) {
            console.error('Erro na análise:', erro);
            mostrarMsgModal('Falha ao conectar com a API.', 'erro');
        }
    });
}

if (btnConfirmarModal) {
    btnConfirmarModal.addEventListener('click', async function() {
        if (!arquivoAtualModal) {
            mostrarMsgModal('Analise um PDF antes de confirmar.', 'erro');
            return;
        }

        const ok = confirm(
            'Confirmar a importação?\n\nIsso vai atualizar a base de funcionários.\n- Novos funcionários serão adicionados\n- Funcionários alterados serão atualizados\n- Funcionários ausentes serão desativados'
        );
        if (!ok) return;

        btnConfirmarModal.disabled = true;
        mostrarMsgModal('Aplicando importação...', 'info');

        const formData = new FormData();
        formData.append('arquivo', arquivoAtualModal);

        try {
            const resposta = await fetch(`${API_URL}/importacao/confirmar`, {
                method: 'POST',
                body: formData,
            });

            const dados = await resposta.json();

            if (dados.erro) {
                mostrarMsgModal(dados.erro, 'erro');
                btnConfirmarModal.disabled = false;
                return;
            }

            const r = dados.resumo || {};
            mostrarMsgModal(
                `✅ ${dados.mensagem} | Novos: ${r.novos || 0} | Alterados: ${r.alterados || 0} | Ausentes: ${r.ausentes || 0}`,
                'ok'
            );

            setTimeout(() => {
                fecharModal();
                carregarPendentes();
                carregarAgendados();
                const totalEl = document.getElementById('total-pendentes');
                if (totalEl) totalEl.textContent = '...';
            }, 2000);

            arquivoAtualModal = null;
            if (inputArquivoModal) inputArquivoModal.value = '';

        } catch (erro) {
            console.error('Erro ao confirmar:', erro);
            mostrarMsgModal('Falha ao confirmar importação.', 'erro');
            btnConfirmarModal.disabled = false;
        }
    });
}
