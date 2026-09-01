"""
Gera links wa.me com mensagem de convocação preenchida.
"""

from urllib.parse import quote


def montar_link_whatsapp(
    celular,
    nome,
    data_agendada,
    horario,
    local_exame,
):
    """
    Retorna o link https://wa.me/55...?text=...
    ou None se o celular for inválido.
    """
    if not celular:
        return None

    numeros = "".join(ch for ch in str(celular) if ch.isdigit())

    if len(numeros) < 10 or len(numeros) > 13:
        return None

    if len(numeros) in (10, 11):
        numeros = "55" + numeros

    primeiro_nome = (nome or "colaborador").strip().split()[0].title()

    mensagem = (
        f"Olá, {primeiro_nome}!\n\n"
        f"Seu exame periódico está agendado para:\n"
        f"Data: {data_agendada}\n"
        f"Horário: {horario}\n"
        f"Local: {local_exame}\n\n"
        f"Por favor, compareça no horário informado.\n"
        f"Em caso de dúvidas, fale com o setor de enfermagem."
    )

    return f"https://wa.me/{numeros}?text={quote(mensagem)}"