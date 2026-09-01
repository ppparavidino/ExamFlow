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
// BUSCAR PENDENTES
// ==========================================================
async function carregarPendentes() {
    const mes = selectMes.value;
    const ano = inputAno.value;
    const container = document.getElementById("tabela-pendentes");
    const totalEl = document.getElementById("total-pendentes");

    container.innerHTML = "<p>Carregando...</p>";

    try {
        const resposta = await fetch(
            `http://192.168.254.200:8001/exames/pendentes?ano=${ano}&mes=${mes}`
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

        let html = `
            <table class="tabela">
                <thead>
                    <tr>
                        <th>Matrícula</th>
                        <th>Nome</th>
                        <th>Cargo</th>
                        <th>Tipo</th>
                        <th>Data prevista</th>
                        <th>Celular</th>
                        <th>Ação</th>
                    </tr>
                </thead>
                <tbody>
        `;

        for (const f of dados.pendentes) {
            html += `
                <tr>
                    <td>${f.matricula}</td>
                    <td>${f.nome}</td>
                    <td>${f.cargo}</td>
                    <td>${f.tipo}</td>
                    <td>${f.data_prevista}</td>
                    <td>${f.celular || "—"}</td>
                    <td>
                        <button
                            type="button"
                            class="btn-agendar"
                            data-id="${f.id}"
                            data-nome="${f.nome}"
                            data-tipo="${f.tipo}"
                            data-prevista="${f.data_prevista}"
                        >
                            Agendar
                        </button>
                    </td>
                </tr>
            `;
        }

        html += "</tbody></table>";
        container.innerHTML = html;
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
    document.getElementById("agendar-prevista").value = botao.dataset.prevista;
    document.getElementById("agendar-funcionario").textContent =
        `Funcionário: ${botao.dataset.nome}`;

    document.getElementById("agendar-data").value = "";
    document.getElementById("agendar-horario").value = "09:00";
    document.getElementById("agendar-local").value = "";
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

document.getElementById("btn-confirmar-agendar").addEventListener("click", async () => {
    const funcionarioId = Number(document.getElementById("agendar-id").value);
    const tipo = document.getElementById("agendar-tipo").value;
    const dataPrevista = document.getElementById("agendar-prevista").value;
    const dataISO = document.getElementById("agendar-data").value;
    const horario = document.getElementById("agendar-horario").value;
    const local = document.getElementById("agendar-local").value.trim();

    if (!dataISO || !horario || !local) {
        agendarMsg.textContent = "Preencha data, horário e local.";
        agendarMsg.className = "mensagem erro";
        return;
    }

    const [ano, mes, dia] = dataISO.split("-");
    const dataAgendada = `${dia}/${mes}/${ano}`;

    agendarMsg.textContent = "Salvando...";
    agendarMsg.className = "mensagem";

    try {
        const resposta = await fetch("http://192.168.254.200:8001/exames/agendar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                funcionario_id: funcionarioId,
                tipo: tipo.includes("Oficina") || tipo.includes("Ano") || tipo.includes("Anual")
                    ? "PERIODICO"
                    : "PERIODICO",
                data_prevista: dataPrevista,
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
        const resposta = await fetch("http://192.168.254.200:8001/exames/agendados");
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
                        <th>Horário</th>
                        <th>Local</th>
                        <th>WhatsApp</th>
                    </tr>
                </thead>
                <tbody>
        `;

        for (const e of dados.agendados) {
            const botaoWhats = e.whatsapp_link
                ? `<a class="btn-whatsapp" href="${e.whatsapp_link}" target="_blank" rel="noopener">WhatsApp</a>`
                : `<span class="sem-celular">Sem celular</span>`;

            html += `
                <tr>
                    <td>${e.matricula}</td>
                    <td>${e.nome}</td>
                    <td>${e.data_agendada}</td>
                    <td>${e.horario}</td>
                    <td>${e.local_exame || "—"}</td>
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
// 🔥 MODAL DE ATUALIZAÇÃO DE FUNCIONÁRIOS (CORRIGIDO)
// ==========================================================

// Verifica se todos os elementos existem antes de usar
const modal = document.getElementById('modal-atualizacao');
const btnAbrirModal = document.getElementById('btn-atualizar-funcionarios');
const btnFecharModal = document.getElementById('btn-fechar-modal');
const inputArquivoModal = document.getElementById('arquivo-pdf-modal');
const btnAnalisarModal = document.getElementById('btn-analisar-modal');
const btnConfirmarModal = document.getElementById('btn-confirmar-modal');
const msgModal = document.getElementById('msg-modal');
const resumoDiv = document.getElementById('modal-resumo');

let arquivoAtualModal = null;

// Verifica se o botão existe
if (btnAbrirModal) {
    console.log('✅ Botão "Atualizar Funcionários" encontrado!');
    
    btnAbrirModal.addEventListener('click', function(event) {
        console.log('🔄 Botão clicado!');
        
        if (!modal) {
            console.error('❌ Modal não encontrado!');
            return;
        }
        
        modal.classList.remove('oculto');
        document.body.style.overflow = 'hidden';
        
        // Limpa campos
        if (inputArquivoModal) inputArquivoModal.value = '';
        if (resumoDiv) resumoDiv.style.display = 'none';
        if (btnConfirmarModal) btnConfirmarModal.disabled = true;
        if (msgModal) {
            msgModal.textContent = '';
            msgModal.className = 'mensagem';
        }
        arquivoAtualModal = null;
    });
} else {
    console.error('❌ Botão "btn-atualizar-funcionarios" não encontrado no HTML!');
}

// Fechar modal
function fecharModal() {
    if (modal) {
        modal.classList.add('oculto');
        document.body.style.overflow = 'auto';
    }
}

if (btnFecharModal) {
    btnFecharModal.addEventListener('click', fecharModal);
}

// Fechar ao clicar fora
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

// Analisar PDF
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
            const resposta = await fetch('http://192.168.254.200:8001/importacao/preview', {
                method: 'POST',
                body: formData,
            });

            const dados = await resposta.json();

            if (dados.erro) {
                mostrarMsgModal(dados.erro, 'erro');
                return;
            }

            // Preenche os cards
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

// Confirmar importação
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
            const resposta = await fetch('http://192.168.254.200:8001/importacao/confirmar', {
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