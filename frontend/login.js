const form = document.getElementById("form-login");
const mensagem = document.getElementById("mensagem");

form.addEventListener("submit", async (event) => {
  event.preventDefault(); // não recarrega a página

  const login = document.getElementById("login").value.trim();
  const senha = document.getElementById("senha").value;

  mensagem.textContent = "Entrando...";
  mensagem.className = "mensagem";

  try {
    const resposta = await fetch("http://192.168.254.200:8000/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ login, senha }),
    });

    const dados = await resposta.json();

    if (dados.erro) {
      mensagem.textContent = dados.erro;
      mensagem.className = "mensagem erro";
      return;
    }

    // Guarda os dados da usuária no navegador
    localStorage.setItem("examflow_usuario", JSON.stringify(dados.usuario));

    mensagem.textContent = "Login ok! Redirecionando...";
    mensagem.className = "mensagem ok";

    // Por enquanto vai para a index; depois será o dashboard
    window.location.href = "/frontend/dashboard.html";
  } catch (erro) {
    console.error(erro);
    mensagem.textContent = "Não foi possível conectar à API.";
    mensagem.className = "mensagem erro";
  }
});