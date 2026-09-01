"""
Regras de cálculo dos exames periódicos.
Mesma lógica do Controle Periódicos.
"""

from datetime import date
from dateutil.relativedelta import relativedelta
from backend.database import conectar


# Cargos com periodicidade semestral permanente
CARGOS_OFICINA = [
    "MECANICO",
    "MECÂNICO",
    "PINTOR",
    "AUXILIAR DE MECANICA",
    "AUXILIAR DE MECÂNICA",
    "AUXILIAR DE MECANICO",
    "AUXILIAR DE MECÂNICO",
    "BORRACHEIRO",
    "LANTERNEIRO",
    "CAPOTEIRO",
    "SOCORRISTA",
]


def eh_cargo_oficina(cargo: str) -> bool:
    """Verifica se o cargo é de oficina (exame semestral contínuo)."""
    cargo_upper = (cargo or "").upper()
    return any(palavra in cargo_upper for palavra in CARGOS_OFICINA)


def calcular_proximo_exame(
    data_admissao: date,
    data_referencia: date,
    cargo: str,
) -> tuple[date, str]:
    """
    Calcula a próxima data de exame e o tipo.

    Retorna: (data_proximo_exame, tipo)
      tipo = "Semestral (Oficina)" | "Semestral (1º Ano)" | "Anual"
    """
    oficina = eh_cargo_oficina(cargo)

    # Primeiro exame: sempre 6 meses após a admissão
    proximo = data_admissao + relativedelta(months=6)

    if oficina:
        # Oficina: avança de 6 em 6 meses até chegar no mês de referência (ou depois)
        while proximo.year < data_referencia.year or (
            proximo.year == data_referencia.year
            and proximo.month < data_referencia.month
        ):
            proximo += relativedelta(months=6)
        tipo = "Semestral (Oficina)"
    else:
        # Ainda está no primeiro ciclo de 6 meses?
        if proximo.year < data_referencia.year or (
            proximo.year == data_referencia.year
            and proximo.month < data_referencia.month
        ):
            # Já passou o 1º semestre → passa a ser anual
            proximo = data_admissao + relativedelta(years=1)
            while proximo.year < data_referencia.year or (
                proximo.year == data_referencia.year
                and proximo.month < data_referencia.month
            ):
                proximo += relativedelta(years=1)
            tipo = "Anual"
        else:
            tipo = "Semestral (1º Ano)"

    return proximo, tipo

def listar_pendentes_do_mes(ano: int, mes: int) -> list[dict]:
    """
    Retorna funcionários ativos cujo próximo exame cai no mês/ano informados.
    """
    data_ref = date(ano, mes, 1)

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT id, matricula, nome, cargo, data_admissao, celular
        FROM funcionarios
        WHERE ativo = 1
        ORDER BY nome
        """
    )

    pendentes = []

    for row in cursor.fetchall():
        func_id = row[0]
        matricula = row[1]
        nome = row[2]
        cargo = row[3]
        data_admissao = row[4]
        celular = row[5]

        # pyodbc pode devolver datetime — normaliza para date
        if hasattr(data_admissao, "date"):
            data_admissao = data_admissao.date()

        proximo, tipo = calcular_proximo_exame(data_admissao, data_ref, cargo)

        if proximo.month == mes and proximo.year == ano:
            pendentes.append({
                "id": func_id,
                "matricula": matricula,
                "nome": nome,
                "cargo": cargo,
                "data_admissao": data_admissao.strftime("%d/%m/%Y"),
                "celular": celular,
                "data_prevista": proximo.strftime("%d/%m/%Y"),
                "tipo": tipo,
            })

    conexao.close()
    return pendentes