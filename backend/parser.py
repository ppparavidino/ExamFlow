"""
Parser do relatório de funcionários do TransNet (Transoft).
Extrai registros a partir do texto do PDF.
"""

import re
import pdfplumber
from datetime import datetime



def normalizar_celular(raw: str | None) -> tuple[str | None, str | None]:
    """
    Remove tudo que não for dígito.
    Retorna (celular_normalizado, celular_raw).

    Não inventa DDD.
    Se ficar inválido, celular_normalizado = None.
    """
    if not raw:
        return None, None

    bruto = raw.strip()
    so_digitos = re.sub(r"\D", "", bruto)

    # 10 ou 11 dígitos = aceitável (com DDD)
    # 8 ou 9 dígitos = guarda, mas pode estar sem DDD
    if len(so_digitos) < 8 or len(so_digitos) > 13:
        return None, bruto

    return so_digitos, bruto

    # Padrão de uma linha de funcionário:
# empresa + matrícula + nome + data + cargo + celular (opcional)
PADRAO_FUNCIONARIO = re.compile(
    r"^(\d{3})\s+(\d{5,6})\s+(.+?)\s+(\d{2}/\d{2}/\d{4})\s+(.+?)(?:\s+([\d\s\-]+))?$"
)


def parsear_linha(linha: str) -> dict | None:
    """
    Tenta transformar uma linha de texto em um dicionário de funcionário.
    Retorna None se a linha não for um registro válido.
    """
    linha = linha.strip()
    if not linha:
        return None

    match = PADRAO_FUNCIONARIO.match(linha)
    if not match:
        return None

    empresa, matricula, nome, data_str, cargo, celular_bruto = match.groups()

    try:
        data_admissao = datetime.strptime(data_str, "%d/%m/%Y").date()
    except ValueError:
        return None

    celular, celular_raw = normalizar_celular(celular_bruto)

    # Limpa cargo: às vezes sobra lixo no final
    cargo = cargo.strip(" -")

    return {
        "empresa": empresa,
        "matricula": matricula,
        "nome": nome.strip(),
        "data_admissao": data_admissao,
        "cargo": cargo,
        "celular": celular,
        "celular_raw": celular_raw,
    }

def extrair_funcionarios_pdf(caminho_pdf: str) -> list[dict]:
    encontrados: dict[str, dict] = {}
    linhas_lidas = 0
    linhas_ignoradas = 0

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text() or ""
            for linha in texto.splitlines():
                linhas_lidas += 1
                funcionario = parsear_linha(linha)
                if funcionario:
                    # chave = matrícula → evita duplicata
                    encontrados[funcionario["matricula"]] = funcionario
                else:
                    linhas_ignoradas += 1

    lista = list(encontrados.values())

    print(
        f"Parser: {len(lista)} funcionários | "
        f"linhas lidas: {linhas_lidas} | "
        f"ignoradas: {linhas_ignoradas}"
    )

    return lista