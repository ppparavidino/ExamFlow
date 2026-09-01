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
// PAGINAÇÃO
// ==========================================================
const POR_PAGINA = 20;
let paginaAtual = 1;

// ==========================================================
// CARREGAR AGENDADOS
// ==========================================================
async function carregarAgendados(pagina = 1) {
    const container = document.getElementById("tabela-agendados");
    const totalEl = document.getElementById("total-agendados");
    const paginacaoEl = document.getElementById("paginacao");

    if (!container) return;

    container.innerHTML = "<p>Carregando...</p>";
    if (paginacaoEl) paginacaoEl.innerHTML = "";
    paginaAtual = pagina;

    try {
        const resposta = await fetch(
            `http://192.168.254.200:8000/exames/agendados?pagina=${pagina}&por_pagina=${POR_PAGINA}`
        );
        const dados = await resposta.json();

        if (dados.erro) {
            container.innerHTML = `<p class="mensagem erro">${dados.erro}</p>`;
            if (totalEl) totalEl.textContent = "0";
            return;
        }

        if (totalEl) totalEl.textContent = dados.total;

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
                        <th>Horário</th>
                        <th>Local</th>
                        <th>WhatsApp</th>
                        <th>PDF</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
        `;

        for (const item of dados.agendados) {
            const botaoWhats = item.whatsapp_link
                ? `<a class="btn-whatsapp" href="${item.whatsapp_link}" target="_blank" rel="noopener">WhatsApp</a>`
                : `<span class="sem-celular">Sem celular</span>`;

            const botaoPdf = `<a class="btn-pdf" href="http://192.168.254.200:8000/exames/${item.exame_id}/pdf" target="_blank" rel="noopener">PDF</a>`;

            // BOTÃO CANCELAR
            const botaoCancelar = `
                <button 
                    type="button" 
                    class="btn-cancelar" 
                    data-id="${item.exame_id}" 
                    data-nome="${item.nome}"
                >
                    ❌ Cancelar
                </button>
            `;

            html += `
                <tr>
                    <td>${item.matricula}</td>
                    <td>${item.nome}</td>
                    <td>${item.cargo}</td>
                    <td>${item.data_agendada}</td>
                    <td>${item.horario}</td>
                    <td>${item.local_exame || "—"}</td>
                    <td>${botaoWhats}</td>
                    <td>${botaoPdf}</td>
                    <td>${botaoCancelar}</td>
                </tr>
            `;
        }

        html += "</tbody></table>";
        container.innerHTML = html;

        // ==========================================================
        // EVENTOS DOS BOTÕES CANCELAR
        // ==========================================================
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
            '<p class="mensagem erro">Não foi possível carregar os agendados.</p>';
        if (totalEl) totalEl.textContent = "0";
    }
}

// ==========================================================
// CANCELAR EXAME
// ==========================================================
async function cancelarExame(exameId, nome) {
    // Confirmação antes de cancelar
    if (!confirm(`❌ Tem certeza que deseja cancelar o exame de ${nome}?`)) {
        return;
    }

    try {
        const resposta = await fetch(`http://192.168.254.200:8000/exames/${exameId}/cancelar`, {
            method: "PUT"
        });

        const dados = await resposta.json();

        if (dados.erro) {
            alert(`❌ Erro: ${dados.erro}`);
            return;
        }

        alert(`✅ ${dados.mensagem}`);
        
        // Recarrega a lista e atualiza o total
        carregarAgendados(paginaAtual);
        atualizarTotal();

    } catch (erro) {
        console.error("Erro ao cancelar:", erro);
        alert("❌ Erro ao cancelar exame. Verifique a conexão com o servidor.");
    }
}

// ==========================================================
// ATUALIZAR TOTAL
// ==========================================================
async function atualizarTotal() {
    try {
        const resposta = await fetch("http://192.168.254.200:8000/exames/agendados?pagina=1&por_pagina=1");
        const dados = await resposta.json();
        
        const totalEl = document.getElementById("total-agendados");
        if (totalEl) {
            totalEl.textContent = dados.total || 0;
        }
    } catch (erro) {
        console.error("Erro ao atualizar total:", erro);
    }
}

// ==========================================================
// MONTAR PAGINAÇÃO
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