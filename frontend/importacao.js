// ----- Proteção de login -----
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

const inputArquivo = document.getElementById("arquivo-pdf");
const btnAnalisar = document.getElementById("btn-analisar");
const btnConfirmar = document.getElementById("btn-confirmar");
const msg = document.getElementById("msg-importacao");
const blocoResumo = document.getElementById("bloco-resumo");
const blocoAmostras = document.getElementById("bloco-amostras");
const amostrasEl = document.getElementById("amostras");

let arquivoAtual = null;

function mostrarMensagem(texto, tipo) {
  msg.textContent = texto;
  msg.className = "mensagem" + (tipo ? ` ${tipo}` : "");
}

function preencherResumo(resumo) {
  document.getElementById("r-total").textContent = resumo.total_pdf ?? 0;
  document.getElementById("r-novos").textContent = resumo.novos ?? 0;
  document.getElementById("r-alterados").textContent = resumo.alterados ?? 0;
  document.getElementById("r-ausentes").textContent = resumo.ausentes ?? 0;
  document.getElementById("r-iguais").textContent = resumo.iguais ?? 0;
  blocoResumo.style.display = "flex";
  blocoResumo.style.flexWrap = "wrap";
  blocoResumo.style.gap = "0.75rem";
}

function montarAmostras(dados) {
  let html = "";

  if (dados.novos_amostra && dados.novos_amostra.length) {
    html += "<h3>Novos (amostra)</h3><ul>";
    for (const f of dados.novos_amostra) {
      html += `<li>${f.matricula} — ${f.nome} (${f.cargo})</li>`;
    }
    html += "</ul>";
  }

  if (dados.alterados_amostra && dados.alterados_amostra.length) {
    html += "<h3>Alterados (amostra)</h3><ul>";
    for (const f of dados.alterados_amostra) {
      html += `<li>${f.matricula} — ${f.nome}</li>`;
    }
    html += "</ul>";
  }

  if (dados.ausentes_amostra && dados.ausentes_amostra.length) {
    html += "<h3>Ausentes (amostra)</h3><ul>";
    for (const f of dados.ausentes_amostra) {
      html += `<li>${f.matricula} — ${f.nome}</li>`;
    }
    html += "</ul>";
  }

  if (!html) {
    html = "<p>Sem alterações relevantes nesta importação.</p>";
  }

  amostrasEl.innerHTML = html;
  blocoAmostras.style.display = "block";
}

btnAnalisar.addEventListener("click", async () => {
  const arquivo = inputArquivo.files[0];

  if (!arquivo) {
    mostrarMensagem("Selecione um arquivo PDF.", "erro");
    return;
  }

  if (!arquivo.name.toLowerCase().endsWith(".pdf")) {
    mostrarMensagem("O arquivo precisa ser PDF.", "erro");
    return;
  }

  arquivoAtual = arquivo;
  btnConfirmar.disabled = true;
  mostrarMensagem("Analisando PDF...", "");
  blocoResumo.style.display = "none";
  blocoAmostras.style.display = "none";

  const formData = new FormData();
  formData.append("arquivo", arquivo);

  try {
    const resposta = await fetch("http://192.168.254.200:8001/importacao/preview", {
      method: "POST",
      body: formData,
    });

    const dados = await resposta.json();

    if (dados.erro) {
      mostrarMensagem(dados.erro, "erro");
      return;
    }

    preencherResumo(dados.resumo);
    montarAmostras(dados);

    btnConfirmar.disabled = false;
    mostrarMensagem(
      `Análise concluída: ${dados.resumo.total_pdf} funcionários no PDF. Confira o resumo e confirme se estiver correto.`,
      "ok"
    );
  } catch (erro) {
    console.error(erro);
    mostrarMensagem("Falha ao conectar com a API.", "erro");
  }
});

btnConfirmar.addEventListener("click", async () => {
  if (!arquivoAtual) {
    mostrarMensagem("Analise um PDF antes de confirmar.", "erro");
    return;
  }

  const ok = window.confirm(
    "Confirmar a importação?\n\nIsso vai atualizar a base de funcionários."
  );
  if (!ok) return;

  btnConfirmar.disabled = true;
  mostrarMensagem("Aplicando importação...", "");

  const formData = new FormData();
  formData.append("arquivo", arquivoAtual);

  try {
    const resposta = await fetch("http://192.168.254.200:8001/importacao/confirmar", {
      method: "POST",
      body: formData,
    });

    const dados = await resposta.json();

    if (dados.erro) {
      mostrarMensagem(dados.erro, "erro");
      btnConfirmar.disabled = false;
      return;
    }

    const r = dados.resumo || {};
    mostrarMensagem(
      `${dados.mensagem} Novos: ${r.novos ?? 0} | Alterados: ${r.alterados ?? 0} | Ausentes: ${r.ausentes ?? 0}`,
      "ok"
    );

    arquivoAtual = null;
    inputArquivo.value = "";
  } catch (erro) {
    console.error(erro);
    mostrarMensagem("Falha ao confirmar importação.", "erro");
    btnConfirmar.disabled = false;
  }
});