// ==========================================================
// CONFIGURAÇÃO
// ==========================================================
const API_URL = "http://192.168.254.200:8000";

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

// ==========================================================
// SAIR
// ==========================================================
const btnSair = document.getElementById("btn-sair");
if (btnSair) {
    btnSair.addEventListener("click", () => {
        localStorage.removeItem("examflow_usuario");
        window.location.href = "/frontend/login.html";
    });
}

// ==========================================================
// VARIÁVEIS
// ==========================================================
const POR_PAGINA = 20;
let paginaAtual = 1;

// ==========================================================
// CARREGAR AGENDADOS
// ==========================================================
async function carregarAgendados(pagina = 1) {
    const container = document.getElementById("tabela-agendados");
    const totalEl = document.getElementById("total-agendados");
    const confirmadosEl = document.getElementById("total-confirmados");
    const paginacaoEl = document.getElementById("paginacao");

    if (!container) return;

    container.innerHTML = "<p>Carregando...</p>";
    if (paginacaoEl) paginacaoEl.innerHTML = "";
    paginaAtual = pagina;

    try {
        const resposta = await fetch(
            `${API_URL}/exames/agendados?pagina=${pagina}&por_pagina=${POR_PAGINA}`
        );
        const dados = await resposta.json();

        if (dados.erro) {
            container.innerHTML = `<p class="mensagem erro">${dados.erro}</p>`;
            if (totalEl) totalEl.textContent = "0";
            return;
        }

        if (totalEl) totalEl.textContent = dados.total;
        
        const confirmados = dados.agendados?.filter(a => a.status === 'CONFIRMADO') || [];
        if (confirmadosEl) confirmadosEl.textContent = confirmados.length;

        if (!dados.agendados || !dados.agendados.length) {
            container.innerHTML = "<p>Nenhum exame agendado.</p>";
            return;
        }

        let html = `
            <table class="tabela">
                <thead>
                    <tr>
                        <th>Matrícula</th>
                        <th>Nome</th>
                        <th>Cargo</th>
                        <th>Data</th>
                        <th>Local</th>
                        <th>WhatsApp</th>
                        <th>PDF</th>
                        <th>Confirmação</th>
                        <th>Observação</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
        `;

        for (const item of dados.agendados) {
            const confirmado = item.status === 'CONFIRMADO';
            
            const botaoWhats = item.whatsapp_link
                ? `<a class="btn-whatsapp" href="${item.whatsapp_link}" target="_blank" rel="noopener">📱 WhatsApp</a>`
                : `<span class="sem-celular">Sem celular</span>`;

            const botaoPdf = `<a class="btn-pdf" href="${API_URL}/exames/${item.exame_id}/pdf" target="_blank" rel="noopener">📄 PDF</a>`;

            const botaoConfirmar = confirmado
                ? `<span style="font-size: 1.5rem;">✅</span>`
                : `<button type="button" class="btn-confirmar" data-id="${item.exame_id}" data-nome="${item.nome}">📩 Confirmar</button>`;

            // Campo de observação EDITÁVEL
            const observacaoHtml = `
                <div style="display: flex; flex-direction: column; gap: 4px; min-width: 120px;">
                    <input type="text" 
                           class="input-observacao" 
                           data-id="${item.exame_id}"
                           value="${item.observacao || ''}" 
                           placeholder="Digite uma observação..."
                           style="
                               padding: 4px 6px;
                               font-size: 0.7rem;
                               border: 1px solid #d1d5db;
                               border-radius: 4px;
                               width: 100%;
                               min-width: 100px;
                           ">
                    <button type="button" 
                            class="btn-salvar-obs" 
                            data-id="${item.exame_id}"
                            style="
                                background: #6b7280;
                                color: #fff;
                                border: none;
                                border-radius: 4px;
                                padding: 2px 6px;
                                font-size: 0.6rem;
                                cursor: pointer;
                                width: auto;
                            ">
                        💾 Salvar
                    </button>
                </div>
            `;

            const botaoCancelar = `
                <button type="button" class="btn-cancelar" data-id="${item.exame_id}" data-nome="${item.nome}">
                    ❌ Cancelar
                </button>
            `;

            html += `
                <tr>
                    <td>${item.matricula}</td>
                    <td>${item.nome}</td>
                    <td>${item.cargo}</td>
                    <td>${item.data_agendada}</td>
                    <td>${item.local_exame || "Dual Saúde"}</td>
                    <td>${botaoWhats}</td>
                    <td>${botaoPdf}</td>
                    <td style="text-align: center;">${botaoConfirmar}</td>
                    <td>${observacaoHtml}</td>
                    <td>${botaoCancelar}</td>
                </tr>
            `;
        }

        html += "</tbody></table>";
        container.innerHTML = html;

        // Eventos: Confirmar
        container.querySelectorAll('.btn-confirmar').forEach(btn => {
            btn.addEventListener('click', async function() {
                const exameId = this.dataset.id;
                const nome = this.dataset.nome;
                await confirmarAgendamento(exameId, nome);
            });
        });

        // Eventos: Salvar Observação
        container.querySelectorAll('.btn-salvar-obs').forEach(btn => {
            btn.addEventListener('click', async function() {
                const exameId = this.dataset.id;
                const input = this.parentElement.querySelector('.input-observacao');
                const observacao = input ? input.value : '';
                await salvarObservacao(exameId, observacao);
            });
        });

        // Eventos: Enter no campo de observação
        container.querySelectorAll('.input-observacao').forEach(input => {
            input.addEventListener('keypress', async function(e) {
                if (e.key === 'Enter') {
                    const exameId = this.dataset.id;
                    const observacao = this.value;
                    await salvarObservacao(exameId, observacao);
                }
            });
        });

        container.querySelectorAll('.btn-cancelar').forEach(btn => {
            btn.addEventListener('click', async function() {
                const exameId = this.dataset.id;
                const nome = this.dataset.nome;
                await cancelarExame(exameId, nome);
            });
        });

        montarPaginacao(dados.pagina, dados.total_paginas);
    } catch (erro) {
        console.error(erro);
        container.innerHTML =
            '<p class="mensagem erro">❌ Não foi possível carregar os agendados.</p>';
        if (totalEl) totalEl.textContent = "0";
    }
}

// ==========================================================
// SALVAR OBSERVAÇÃO
// ==========================================================
async function salvarObservacao(exameId, observacao) {
    try {
        const resposta = await fetch(`${API_URL}/exames/${exameId}/observacao`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ observacao: observacao })
        });

        const dados = await resposta.json();

        if (dados.erro) {
            alert(`❌ Erro: ${dados.erro}`);
            return;
        }

        // Feedback visual
        const btn = document.querySelector(`.btn-salvar-obs[data-id="${exameId}"]`);
        if (btn) {
            const textoOriginal = btn.textContent;
            btn.textContent = '✅ Salvo!';
            btn.style.background = '#22c55e';
            setTimeout(() => {
                btn.textContent = textoOriginal;
                btn.style.background = '#6b7280';
            }, 2000);
        }

    } catch (erro) {
        console.error("Erro ao salvar observação:", erro);
        alert("❌ Erro ao salvar observação.");
    }
}

// ==========================================================
// CONFIRMAR AGENDAMENTO
// ==========================================================
async function confirmarAgendamento(exameId, nome) {
    if (!confirm(`✅ Confirmar agendamento de ${nome}?`)) return;

    try {
        const resposta = await fetch(`${API_URL}/exames/${exameId}/confirmar`, {
            method: "PUT"
        });

        const dados = await resposta.json();

        if (dados.erro) {
            alert(`❌ Erro: ${dados.erro}`);
            return;
        }

        alert(`✅ ${dados.mensagem}`);
        carregarAgendados(paginaAtual);

    } catch (erro) {
        console.error("Erro ao confirmar:", erro);
        alert("❌ Erro ao confirmar agendamento.");
    }
}

// ==========================================================
// CANCELAR EXAME
// ==========================================================
async function cancelarExame(exameId, nome) {
    if (!confirm(`❌ Tem certeza que deseja cancelar o exame de ${nome}?`)) return;

    try {
        const resposta = await fetch(`${API_URL}/exames/${exameId}/cancelar`, {
            method: "PUT"
        });

        const dados = await resposta.json();

        if (dados.erro) {
            alert(`❌ Erro: ${dados.erro}`);
            return;
        }

        alert(`✅ ${dados.mensagem}`);
        carregarAgendados(paginaAtual);

    } catch (erro) {
        console.error("Erro ao cancelar:", erro);
        alert("❌ Erro ao cancelar exame.");
    }
}

// ==========================================================
// RELATÓRIO PDF
// ==========================================================
document.getElementById("btn-relatorio-pdf")?.addEventListener("click", () => {
    window.open(`${API_URL}/exames/relatorio-pdf`, "_blank");
});

// ==========================================================
// PAGINAÇÃO
// ==========================================================
function montarPaginacao(pagina, totalPaginas) {
    const el = document.getElementById("paginacao");
    if (!el) return;

    if (!totalPaginas || totalPaginas <= 1) {
        el.innerHTML = "";
        return;
    }

    let html = "";

    html += `<button type="button" class="btn-pagina" data-pagina="${pagina - 1}" ${
        pagina <= 1 ? "disabled" : ""
    }>Anterior</button>`;

    const inicio = Math.max(1, pagina - 2);
    const fim = Math.min(totalPaginas, pagina + 2);

    if (inicio > 1) {
        html += `<button type="button" class="btn-pagina" data-pagina="1">1</button>`;
        if (inicio > 2) html += `<span class="pagina-ellipsis">...</span>`;
    }

    for (let p = inicio; p <= fim; p++) {
        html += `<button type="button" class="btn-pagina ${
            p === pagina ? "ativa" : ""
        }" data-pagina="${p}">${p}</button>`;
    }

    if (fim < totalPaginas) {
        if (fim < totalPaginas - 1) html += `<span class="pagina-ellipsis">...</span>`;
        html += `<button type="button" class="btn-pagina" data-pagina="${totalPaginas}">${totalPaginas}</button>`;
    }

    html += `<button type="button" class="btn-pagina" data-pagina="${pagina + 1}" ${
        pagina >= totalPaginas ? "disabled" : ""
    }>Próxima</button>`;

    el.innerHTML = html;
}

// ==========================================================
// EVENTOS DA PAGINAÇÃO
// ==========================================================
const paginacaoEl = document.getElementById("paginacao");
if (paginacaoEl) {
    paginacaoEl.addEventListener("click", (event) => {
        const botao = event.target.closest(".btn-pagina");
        if (!botao || botao.disabled) return;

        const pagina = Number(botao.dataset.pagina);
        if (pagina >= 1) {
            carregarAgendados(pagina);
        }
    });
}

// ==========================================================
// CARREGA A PRIMEIRA PÁGINA AO ABRIR
// ==========================================================
carregarAgendados(1);