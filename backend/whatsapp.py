"""
Gera links wa.me com mensagem de convocação preenchida.
"""

from urllib.parse import quote


def montar_link_whatsapp(
    celular,
    nome,
    data_agendada,
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
        f"Bom dia {primeiro_nome} ! Favor comparecer a Dual saúde no dia\n"
        f"{data_agendada} apartir das 07:00 até as 15:00h\n"
        f"(ordem de chegada) na rua Almirante Teffe, 669 Centro/ Niterói , "
        f"afim de fazer seu exame periódico.\n"
        f"Você deverá levar um documento com foto\n\n"
        f" Obs. Para funcionários homens acima de 39 anos, 2 dias que antecedem o exame, "
        f"não poderá andar de moto, bicicleta nem ter relação sexual pois irá realizar "
        f"o PSA ( exame de prevenção de câncer de próstata).\n\n"
        f"Obs2 Para MOTORISTA que usa óculos,  levá-lo para a clínica no dia do exame.\n\n"
        f"Obs3 Nenhum funcionário é retirado de escala!\n"
        f"Somente é ajustado o horário para ir realizar o periódico.\n\n"
        f"Obs4 Não é necessário está em jejum\n\n"
        f"FAVOR NÃO FALTAR\n"
        f"Qualquer DÚVIDA só entrar em contato."
    )

    return f"https://wa.me/{numeros}?text={quote(mensagem)}"