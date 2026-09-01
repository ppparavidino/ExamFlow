"""
Comparação entre o PDF e o banco de funcionários.
Ainda não grava nada — só analisa.
"""

from backend.database import conectar


def carregar_funcionarios_banco() -> dict:
    """
    Retorna um dicionário:
    { matricula: { campos... } }
    """
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT
            id, matricula, empresa, nome, data_admissao,
            cargo, celular, celular_raw, ativo
        FROM funcionarios
        """
    )

    mapa = {}
    for row in cursor.fetchall():
        mapa[row[1]] = {
            "id": row[0],
            "matricula": row[1],
            "empresa": row[2],
            "nome": row[3],
            "data_admissao": row[4],
            "cargo": row[5],
            "celular": row[6],
            "celular_raw": row[7],
            "ativo": bool(row[8]),
        }

    conexao.close()
    return mapa


def comparar_pdf_com_banco(lista_pdf: list[dict]) -> dict:
    """
    Compara os funcionários do PDF com os do banco.

    Retorna:
    {
      "novos": [...],
      "alterados": [...],
      "ausentes": [...],
      "iguais": [...],
      "resumo": { totais }
    }
    """
    banco = carregar_funcionarios_banco()
    pdf_map = {f["matricula"]: f for f in lista_pdf}

    novos = []
    alterados = []
    iguais = []
    ausentes = []

    # 1) Percorre o PDF
    for matricula, dados_pdf in pdf_map.items():
        if matricula not in banco:
            novos.append(dados_pdf)
            continue

        dados_banco = banco[matricula]

        # Campos que importam na comparação
        mudancas = {}

        if dados_banco["nome"] != dados_pdf["nome"]:
            mudancas["nome"] = {
                "antes": dados_banco["nome"],
                "depois": dados_pdf["nome"],
            }

        if dados_banco["cargo"] != dados_pdf["cargo"]:
            mudancas["cargo"] = {
                "antes": dados_banco["cargo"],
                "depois": dados_pdf["cargo"],
            }

        # data_admissao no banco pode vir como date
        data_banco = dados_banco["data_admissao"]
        data_pdf = dados_pdf["data_admissao"]
        if hasattr(data_banco, "strftime"):
            data_banco_str = data_banco.strftime("%Y-%m-%d")
        else:
            data_banco_str = str(data_banco)

        if data_pdf is not None and hasattr(data_pdf, "strftime"):
            data_pdf_str = data_pdf.strftime("%Y-%m-%d")
        else:
            data_pdf_str = str(data_pdf)

        if data_banco_str != data_pdf_str:
            mudancas["data_admissao"] = {
                "antes": data_banco_str,
                "depois": data_pdf_str,
            }

        celular_banco = dados_banco["celular"] or ""
        celular_pdf = dados_pdf["celular"] or ""
        if celular_banco != celular_pdf:
            mudancas["celular"] = {
                "antes": celular_banco,
                "depois": celular_pdf,
            }

        # Se estava inativo e voltou no PDF → também conta como alteração
        if not dados_banco["ativo"]:
            mudancas["ativo"] = {
                "antes": False,
                "depois": True,
            }

        if mudancas:
            alterados.append({
                "matricula": matricula,
                "nome": dados_pdf["nome"],
                "mudancas": mudancas,
                "dados_pdf": dados_pdf,
                "id_banco": dados_banco["id"],
            })
        else:
            iguais.append({
                "matricula": matricula,
                "nome": dados_pdf["nome"],
            })

    # 2) Quem está ativo no banco e NÃO veio no PDF → ausente
    for matricula, dados_banco in banco.items():
        if dados_banco["ativo"] and matricula not in pdf_map:
            ausentes.append({
                "id": dados_banco["id"],
                "matricula": matricula,
                "nome": dados_banco["nome"],
                "cargo": dados_banco["cargo"],
            })

    return {
        "novos": novos,
        "alterados": alterados,
        "ausentes": ausentes,
        "iguais": iguais,
        "resumo": {
            "total_pdf": len(lista_pdf),
            "novos": len(novos),
            "alterados": len(alterados),
            "ausentes": len(ausentes),
            "iguais": len(iguais),
        },
    }
def aplicar_importacao(resultado_diff: dict, nome_arquivo: str) -> dict:
    """
    Aplica no banco o resultado do diff:
    - insere novos
    - atualiza alterados
    - marca ausentes como ativo = 0
    - registra a importação

    Retorna um resumo do que foi gravado.
    """
    conexao = conectar()
    cursor = conexao.cursor()

    try:
        # ----- NOVOS -----
        for f in resultado_diff["novos"]:
            cursor.execute(
                """
                INSERT INTO funcionarios
                    (matricula, empresa, nome, data_admissao, cargo,
                     celular, celular_raw, ativo, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, GETDATE(), GETDATE())
                """,
                (
                    f["matricula"],
                    f["empresa"],
                    f["nome"],
                    f["data_admissao"],
                    f["cargo"],
                    f["celular"],
                    f["celular_raw"],
                ),
            )

        # ----- ALTERADOS -----
        for item in resultado_diff["alterados"]:
            f = item["dados_pdf"]
            cursor.execute(
                """
                UPDATE funcionarios
                SET
                    empresa = ?,
                    nome = ?,
                    data_admissao = ?,
                    cargo = ?,
                    celular = ?,
                    celular_raw = ?,
                    ativo = 1,
                    atualizado_em = GETDATE()
                WHERE id = ?
                """,
                (
                    f["empresa"],
                    f["nome"],
                    f["data_admissao"],
                    f["cargo"],
                    f["celular"],
                    f["celular_raw"],
                    item["id_banco"],
                ),
            )

        # ----- AUSENTES (não apaga — só desativa) -----
        for item in resultado_diff["ausentes"]:
            cursor.execute(
                """
                UPDATE funcionarios
                SET ativo = 0, atualizado_em = GETDATE()
                WHERE id = ?
                """,
                (item["id"],),
            )

        # ----- HISTÓRICO DA IMPORTAÇÃO -----
        resumo = resultado_diff["resumo"]
        cursor.execute(
            """
            INSERT INTO importacoes
                (nome_arquivo, data_importacao, total, novos, alterados, ausentes)
            VALUES (?, GETDATE(), ?, ?, ?, ?)
            """,
            (
                nome_arquivo,
                resumo["total_pdf"],
                resumo["novos"],
                resumo["alterados"],
                resumo["ausentes"],
            ),
        )

        conexao.commit()

        return {
            "mensagem": "Importação aplicada com sucesso.",
            "resumo": resumo,
        }

    except Exception as e:
        conexao.rollback()
        raise e

    finally:
        conexao.close()