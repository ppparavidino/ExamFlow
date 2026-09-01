// Proteção: sem login → volta para a tela de login
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

// Botão Sair
const btnSair = document.getElementById("btn-sair");

if (btnSair) {
  btnSair.addEventListener("click", () => {
    localStorage.removeItem("examflow_usuario");
    window.location.href = "/frontend/login.html";
  });
}