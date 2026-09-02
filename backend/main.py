from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from backend.database import conectar
from backend.auth import verificar_senha
from fastapi.responses import FileResponse, Response
import tempfile
import os

class AgendarExame(BaseModel):
    funcionario_id: int
    tipo: str = "PERIODICO"
    data_prevista: str | None = None   # dd/mm/aaaa
    data_agendada: str                # dd/mm/aaaa
    horario: str                       # HH:MM
    local_exame: str
    observacao: str | None = None

class LoginUsuario(BaseModel):
    login: str
    senha: str

app = FastAPI(title="ExamFlow")

# CORS — liberado para desenvolvimento local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/frontend",
    StaticFiles(directory="frontend"),
    name="frontend",
)


@app.get("/")
def inicio():
    return {
        "sistema": "ExamFlow",
        "status": "ok",
        "mensagem": "API ExamFlow funcionando",
    }


@app.get("/teste-banco")
def teste_banco():
    """Testa a conexão com o SQL Express."""
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT 1 AS ok")
        row = cursor.fetchone()
        conexao.close()
        return {"banco": "ok", "resultado": row[0] if row else None}
    except Exception as e:
        return {"banco": "erro", "detalhe": str(e)}


# ==========================================================
# LOGIN
# ==========================================================
@app.post("/login")
def login_usuario(usuario: LoginUsuario):
    try:
        conexao = conectar()
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT id, nome, login, senha_hash, email, ativo
            FROM usuarios
            WHERE login = ?
            """,
            (usuario.login,),
        )

        resultado = cursor.fetchone()
        conexao.close()

        if not resultado:
            return {"erro": "Login ou senha inválidos."}

        # pyodbc retorna tupla:
        # [0]=id [1]=nome [2]=login [3]=senha_hash [4]=email [5]=ativo
        user_id = resultado[0]
        nome = resultado[1]
        login = resultado[2]
        senha_hash = resultado[3]
        email = resultado[4]
        ativo = resultado[5]

        if not ativo:
            return {"erro": "Usuário inativo."}

        if not verificar_senha(usuario.senha, senha_hash):
            return {"erro": "Login ou senha inválidos."}

        return {
            "mensagem": "Login realizado com sucesso.",
            "usuario": {
                "id": user_id,
                "nome": nome,
                "login": login,
                "email": email,
            },
        }

    except Exception as e:
        print("ERRO NO LOGIN:", e)
        return {"erro": f"Erro interno no login: {str(e)}"}
# ==========================================================
# PARSER DO PDF (teste — ainda não grava no banco)
# ==========================================================
@app.post("/parse-pdf")
async def parse_pdf(arquivo: UploadFile = File(...)):
    if not arquivo.filename.lower().endswith(".pdf"):
        return {"erro": "Envie um arquivo PDF."}

    # Salva temporariamente para o pdfplumber abrir
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            conteudo = await arquivo.read()
            tmp.write(conteudo)
            caminho_tmp = tmp.name

        from backend.parser import extrair_funcionarios_pdf

        lista = extrair_funcionarios_pdf(caminho_tmp)

        # Amostra dos 3 primeiros (para conferência)
        amostra = []
        for f in lista[:3]:
            amostra.append({
                "matricula": f["matricula"],
                "nome": f["nome"],
                "cargo": f["cargo"],
                "data_admissao": f["data_admissao"].strftime("%d/%m/%Y"),
                "celular": f["celular"],
            })

        return {
            "total": len(lista),
            "amostra": amostra,
            "mensagem": f"{len(lista)} funcionários extraídos do PDF.",
        }

    except Exception as e:
        print("ERRO NO PARSE-PDF:", e)
        return {"erro": f"Falha ao ler o PDF: {str(e)}"}

    finally:
        if "caminho_tmp" in locals() and os.path.exists(caminho_tmp):
            os.remove(caminho_tmp)

# ==========================================================
# IMPORTAÇÃO
# ==========================================================
@app.post("/importacao/preview")
async def importacao_preview(arquivo: UploadFile = File(...)):
    if not arquivo.filename.lower().endswith(".pdf"):
        return {"erro": "Envie um arquivo PDF."}

    caminho_tmp = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await arquivo.read())
            caminho_tmp = tmp.name

        from backend.parser import extrair_funcionarios_pdf
        from backend.importacao import comparar_pdf_com_banco

        lista = extrair_funcionarios_pdf(caminho_tmp)
        diff = comparar_pdf_com_banco(lista)

        # Amostra pequena para a tela
        return {
            "resumo": diff["resumo"],
            "novos_amostra": [
                {"matricula": f["matricula"], "nome": f["nome"], "cargo": f["cargo"]}
                for f in diff["novos"][:5]
            ],
            "alterados_amostra": [
                {
                    "matricula": a["matricula"],
                    "nome": a["nome"],
                    "mudancas": a["mudancas"],
                }
                for a in diff["alterados"][:5]
            ],
            "ausentes_amostra": [
                {"matricula": a["matricula"], "nome": a["nome"]}
                for a in diff["ausentes"][:5]
            ],
            "nome_arquivo": arquivo.filename,
        }

    except Exception as e:
        print("ERRO NO PREVIEW:", e)
        return {"erro": f"Falha no preview: {str(e)}"}

    finally:
        if caminho_tmp and os.path.exists(caminho_tmp):
            os.remove(caminho_tmp)


@app.post("/importacao/confirmar")
async def importacao_confirmar(arquivo: UploadFile = File(...)):
    if not arquivo.filename.lower().endswith(".pdf"):
        return {"erro": "Envie um arquivo PDF."}

    caminho_tmp = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await arquivo.read())
            caminho_tmp = tmp.name

        from backend.parser import extrair_funcionarios_pdf
        from backend.importacao import comparar_pdf_com_banco, aplicar_importacao

        lista = extrair_funcionarios_pdf(caminho_tmp)
        diff = comparar_pdf_com_banco(lista)
        resultado = aplicar_importacao(diff, arquivo.filename)

        return resultado

    except Exception as e:
        print("ERRO NA CONFIRMAÇÃO:", e)
        return {"erro": f"Falha ao confirmar importação: {str(e)}"}

    finally:
        if caminho_tmp and os.path.exists(caminho_tmp):
            os.remove(caminho_tmp)

# ==========================================================
# EXAMES PENDENTES
# ==========================================================
@app.get("/exames/pendentes")
def exames_pendentes(ano: int, mes: int):
    """
    Lista funcionários com exame previsto no mês/ano.
    Exemplo: /exames/pendentes?ano=2026&mes=8
    """
    if mes < 1 or mes > 12:
        return {"erro": "Mês inválido (1 a 12)."}

    if ano < 2020 or ano > 2100:
        return {"erro": "Ano inválido."}

    try:
        from backend.exames_regras import listar_pendentes_do_mes

        lista = listar_pendentes_do_mes(ano, mes)

        return {
            "ano": ano,
            "mes": mes,
            "total": len(lista),
            "pendentes": lista,
        }

    except Exception as e:
        print("ERRO EM EXAMES PENDENTES:", e)
        return {"erro": f"Falha ao listar pendentes: {str(e)}"}


    # ==========================================================
# AGENDAR EXAME
# ==========================================================
@app.post("/exames/agendar")
def agendar_exame(dados: AgendarExame):
    try:
        from datetime import datetime

        data_agendada = datetime.strptime(dados.data_agendada, "%d/%m/%Y").date()
        horario = datetime.strptime(dados.horario, "%H:%M").time()

        data_prevista = None
        if dados.data_prevista:
            data_prevista = datetime.strptime(dados.data_prevista, "%d/%m/%Y").date()

        conexao = conectar()
        cursor = conexao.cursor()

        # Confere se o funcionário existe e está ativo
        cursor.execute(
            "SELECT id, nome FROM funcionarios WHERE id = ? AND ativo = 1",
            (dados.funcionario_id,),
        )
        func = cursor.fetchone()
        if not func:
            conexao.close()
            return {"erro": "Funcionário não encontrado ou inativo."}

        cursor.execute(
            """
            INSERT INTO exames
                (funcionario_id, tipo, data_prevista, data_agendada,
                 horario, local_exame, status, observacao, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, 'AGENDADO', ?, GETDATE())
            """,
            (
                dados.funcionario_id,
                dados.tipo,
                data_prevista,
                data_agendada,
                horario,
                dados.local_exame.strip(),
                dados.observacao,
            ),
        )

        conexao.commit()
        conexao.close()

        return {
            "mensagem": "Exame agendado com sucesso.",
            "funcionario": func[1],
            "data_agendada": dados.data_agendada,
            "horario": dados.horario,
            "local_exame": dados.local_exame,
        }

    except ValueError:
        return {"erro": "Data ou horário em formato inválido. Use dd/mm/aaaa e HH:MM."}
    except Exception as e:
        print("ERRO AO AGENDAR:", e)
        return {"erro": f"Falha ao agendar: {str(e)}"}


   # ==========================================================
# EXAMES AGENDADOS + LINK WHATSAPP
# ==========================================================
@app.get("/exames/agendados")
def exames_agendados(pagina: int = 1, por_pagina: int = 20):
    """
    Lista exames agendados, do mais recente para o mais antigo.
    """
    if pagina < 1:
        pagina = 1
    if por_pagina < 1 or por_pagina > 100:
        por_pagina = 20

    try:
        from backend.whatsapp import montar_link_whatsapp

        conexao = conectar()
        cursor = conexao.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM exames WHERE status = 'AGENDADO'"
        )
        total = cursor.fetchone()[0]

        total_paginas = max(1, (total + por_pagina - 1) // por_pagina)
        if pagina > total_paginas:
            pagina = total_paginas

        offset = (pagina - 1) * por_pagina

        cursor.execute(
            """
            SELECT
                e.id,
                f.matricula,
                f.nome,
                f.cargo,
                f.celular,
                e.data_agendada,
                e.horario,
                e.local_exame,
                e.status,
                e.criado_em,
                e.observacao
            FROM exames e
            INNER JOIN funcionarios f ON f.id = e.funcionario_id
            WHERE e.status = 'AGENDADO'
            ORDER BY e.criado_em DESC, e.id DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """,
            (offset, por_pagina),
        )

        lista = []
        for row in cursor.fetchall():
            data_agendada = row[5]
            horario = row[6]

            data_str = (
                data_agendada.strftime("%d/%m/%Y")
                if hasattr(data_agendada, "strftime")
                else str(data_agendada)
            )
            horario_str = (
                horario.strftime("%H:%M")
                if hasattr(horario, "strftime")
                else str(horario)[:5]
            )

            link = montar_link_whatsapp(
                celular=row[4],
                nome=row[2],
                data_agendada=data_str,
            )

            lista.append({
                "exame_id": row[0],
                "matricula": row[1],
                "nome": row[2],
                "cargo": row[3],
                "celular": row[4],
                "data_agendada": data_str,
                "horario": horario_str,
                "local_exame": row[7] or "Dual Saúde",
                "status": row[8],
                "observacao": row[10] or "",
                "whatsapp_link": link,
            })

        conexao.close()

        return {
            "total": total,
            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_paginas": total_paginas,
            "agendados": lista,
        }

    except Exception as e:
        print("ERRO EM EXAMES AGENDADOS:", e)
        return {"erro": f"Falha ao listar agendados: {str(e)}"}


# ==========================================================
# CANCELAR EXAME (versão sem atualizado_em)
# ==========================================================
@app.put("/exames/{exame_id}/cancelar")
def cancelar_exame(exame_id: int):
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        
        # Verifica se o exame existe e está agendado
        cursor.execute(
            """
            SELECT e.id, f.nome 
            FROM exames e
            INNER JOIN funcionarios f ON f.id = e.funcionario_id
            WHERE e.id = ? AND e.status = 'AGENDADO'
            """,
            (exame_id,)
        )
        
        exame = cursor.fetchone()
        if not exame:
            conexao.close()
            return {"erro": "Exame não encontrado ou já foi realizado/cancelado."}
        
        # Atualiza status para CANCELADO (sem atualizado_em)
        cursor.execute(
            """
            UPDATE exames 
            SET status = 'CANCELADO'
            WHERE id = ?
            """,
            (exame_id,)
        )
        
        conexao.commit()
        conexao.close()
        
        return {
            "mensagem": f"Exame de {exame[1]} foi CANCELADO com sucesso!",
            "exame_id": exame_id,
            "funcionario": exame[1]
        }
        
    except Exception as e:
        print("ERRO AO CANCELAR EXAME:", e)
        return {"erro": f"Falha ao cancelar exame: {str(e)}"}
    

    # ==========================================================
# PDF DE CONVOCAÇÃO
# ==========================================================
@app.get("/exames/{exame_id}/pdf")
def exame_pdf(exame_id: int):
    try:
        from backend.convocacao_pdf import gerar_pdf_convocacao

        conexao = conectar()
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT
                f.nome,
                f.matricula,
                f.cargo,
                e.data_agendada,
                e.horario,
                e.local_exame
            FROM exames e
            INNER JOIN funcionarios f ON f.id = e.funcionario_id
            WHERE e.id = ?
            """,
            (exame_id,),
        )

        row = cursor.fetchone()
        conexao.close()

        if not row:
            return {"erro": "Exame não encontrado."}

        data_agendada = row[3]
        horario = row[4]

        data_str = (
            data_agendada.strftime("%d/%m/%Y")
            if hasattr(data_agendada, "strftime")
            else str(data_agendada)
        )
        horario_str = (
            horario.strftime("%H:%M")
            if hasattr(horario, "strftime")
            else str(horario)[:5]
        )

        pdf_bytes = gerar_pdf_convocacao(
            nome=row[0],
            matricula=row[1],
            cargo=row[2],
            data_agendada=data_str,
            horario=horario_str,
            local_exame=row[5] or "",
        )

        nome_arquivo = f"convocacao_{row[1]}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{nome_arquivo}"'
            },
        )

    except Exception as e:
        print("ERRO AO GERAR PDF:", e)
        return {"erro": f"Falha ao gerar PDF: {str(e)}"}



    # ==========================================================
# CONFIRMAR AGENDAMENTO (enviar mensagem)
# ==========================================================
@app.put("/exames/{exame_id}/confirmar")
def confirmar_agendamento(exame_id: int):
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        
        cursor.execute(
            """
            UPDATE exames 
            SET observacao = 'Mensagem enviada via WhatsApp - confirmado',
                atualizado_em = GETDATE()
            WHERE id = ? AND status = 'AGENDADO'
            """,
            (exame_id,)
        )
        
        if cursor.rowcount == 0:
            conexao.close()
            return {"erro": "Exame não encontrado ou não está agendado."}
        
        conexao.commit()
        conexao.close()
        
        return {"mensagem": "✅ Agendamento confirmado e mensagem enviada!"}
        
    except Exception as e:
        print("ERRO AO CONFIRMAR AGENDAMENTO:", e)
        return {"erro": f"Falha ao confirmar: {str(e)}"}


# ==========================================================
# RELATÓRIO PDF DE TODOS OS AGENDADOS
# ==========================================================
@app.get("/exames/relatorio-pdf")
def relatorio_agendados_pdf():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from datetime import datetime
        import io

        conexao = conectar()
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT 
                f.matricula,
                f.nome,
                f.cargo,
                e.data_agendada,
                e.local_exame,
                e.status,
                e.observacao
            FROM exames e
            INNER JOIN funcionarios f ON f.id = e.funcionario_id
            WHERE e.status IN ('AGENDADO', 'CONFIRMADO')
            ORDER BY e.data_agendada, f.nome
            """
        )

        dados = cursor.fetchall()
        conexao.close()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                leftMargin=1*cm, rightMargin=1*cm,
                                topMargin=1*cm, bottomMargin=1*cm)
        
        styles = getSampleStyleSheet()
        elements = []

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=1,
            spaceAfter=20
        )
        elements.append(Paragraph("RELATÓRIO DE EXAMES AGENDADOS", title_style))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 10))

        data = [["Matrícula", "Nome", "Cargo", "Data", "Local", "Status", "Obs"]]
        
        for row in dados:
            data_agendada = row[3].strftime("%d/%m/%Y") if hasattr(row[3], "strftime") else str(row[3])
            status = row[5]
            if status == 'AGENDADO':
                status = '⏳ Pendente'
            elif status == 'CONFIRMADO':
                status = '✅ Confirmado'
            elif status == 'CANCELADO':
                status = '❌ Cancelado'
            
            obs = row[6] or ""
            if "confirmado" in obs.lower():
                obs = "✅ Mensagem enviada"
            
            data.append([
                str(row[0]),
                str(row[1])[:30],
                str(row[2])[:25],
                data_agendada,
                str(row[4])[:30] or "Dual Saúde",
                status,
                obs[:20]
            ])

        table = Table(data, colWidths=[2.5*cm, 5*cm, 4*cm, 2.5*cm, 4*cm, 2.5*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))

        elements.append(table)
        doc.build(elements)

        buffer.seek(0)
        return Response(
            content=buffer.read(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="relatorio_agendados.pdf"'
            }
        )

    except Exception as e:
        print("ERRO NO RELATÓRIO PDF:", e)
        return {"erro": f"Falha ao gerar relatório: {str(e)}"}
# Nas próximas etapas:
# - importação do PDF
# - dashboard
# - agendamento
# - WhatsApp / PDF
