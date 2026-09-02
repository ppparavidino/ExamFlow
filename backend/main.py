from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from backend.database import conectar
from backend.auth import verificar_senha
from fastapi.responses import FileResponse, Response
import tempfile
import os
from datetime import datetime

# ==========================================================
# MODELOS
# ==========================================================
class AgendarExame(BaseModel):
    funcionario_id: int
    tipo: str = "PERIODICO"
    data_prevista: str | None = None
    data_agendada: str
    horario: str
    local_exame: str
    observacao: str | None = None

class LoginUsuario(BaseModel):
    login: str
    senha: str

class AtualizarObservacao(BaseModel):
    observacao: str

# ==========================================================
# APP
# ==========================================================
app = FastAPI(title="ExamFlow")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# ==========================================================
# ROTAS BÁSICAS
# ==========================================================
@app.get("/")
def inicio():
    return {"sistema": "ExamFlow", "status": "ok"}

@app.get("/teste-banco")
def teste_banco():
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
        cursor.execute("""
            SELECT id, nome, login, senha_hash, email, ativo
            FROM usuarios WHERE login = ?
        """, (usuario.login,))
        resultado = cursor.fetchone()
        conexao.close()
        if not resultado:
            return {"erro": "Login ou senha inválidos."}
        if not resultado[5]:
            return {"erro": "Usuário inativo."}
        if not verificar_senha(usuario.senha, resultado[3]):
            return {"erro": "Login ou senha inválidos."}
        return {
            "mensagem": "Login realizado com sucesso.",
            "usuario": {
                "id": resultado[0],
                "nome": resultado[1],
                "login": resultado[2],
                "email": resultado[4],
            },
        }
    except Exception as e:
        print("ERRO NO LOGIN:", e)
        return {"erro": f"Erro interno no login: {str(e)}"}

# ==========================================================
# PARSER DO PDF
# ==========================================================
@app.post("/parse-pdf")
async def parse_pdf(arquivo: UploadFile = File(...)):
    if not arquivo.filename.lower().endswith(".pdf"):
        return {"erro": "Envie um arquivo PDF."}
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await arquivo.read())
            caminho_tmp = tmp.name
        from backend.parser import extrair_funcionarios_pdf
        lista = extrair_funcionarios_pdf(caminho_tmp)
        amostra = []
        for f in lista[:3]:
            amostra.append({
                "matricula": f["matricula"],
                "nome": f["nome"],
                "cargo": f["cargo"],
                "data_admissao": f["data_admissao"].strftime("%d/%m/%Y"),
                "celular": f["celular"],
            })
        return {"total": len(lista), "amostra": amostra}
    except Exception as e:
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
        return {
            "resumo": diff["resumo"],
            "novos_amostra": [
                {"matricula": f["matricula"], "nome": f["nome"], "cargo": f["cargo"]}
                for f in diff["novos"][:5]
            ],
            "alterados_amostra": [
                {"matricula": a["matricula"], "nome": a["nome"], "mudancas": a["mudancas"]}
                for a in diff["alterados"][:5]
            ],
            "ausentes_amostra": [
                {"matricula": a["matricula"], "nome": a["nome"]}
                for a in diff["ausentes"][:5]
            ],
            "nome_arquivo": arquivo.filename,
        }
    except Exception as e:
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
        return {"erro": f"Falha ao confirmar importação: {str(e)}"}
    finally:
        if caminho_tmp and os.path.exists(caminho_tmp):
            os.remove(caminho_tmp)

# ==========================================================
# EXAMES PENDENTES
# ==========================================================
@app.get("/exames/pendentes")
def exames_pendentes(ano: int, mes: int):
    if mes < 1 or mes > 12:
        return {"erro": "Mês inválido (1 a 12)."}
    if ano < 2020 or ano > 2100:
        return {"erro": "Ano inválido."}
    try:
        from backend.exames_regras import listar_pendentes_do_mes
        lista = listar_pendentes_do_mes(ano, mes)
        return {"ano": ano, "mes": mes, "total": len(lista), "pendentes": lista}
    except Exception as e:
        return {"erro": f"Falha ao listar pendentes: {str(e)}"}

# ==========================================================
# AGENDAR EXAME
# ==========================================================
@app.post("/exames/agendar")
def agendar_exame(dados: AgendarExame):
    try:
        data_agendada = datetime.strptime(dados.data_agendada, "%d/%m/%Y").date()
        horario = datetime.strptime(dados.horario, "%H:%M").time()
        data_prevista = None
        if dados.data_prevista:
            data_prevista = datetime.strptime(dados.data_prevista, "%d/%m/%Y").date()
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT id, nome FROM funcionarios WHERE id = ? AND ativo = 1", (dados.funcionario_id,))
        func = cursor.fetchone()
        if not func:
            conexao.close()
            return {"erro": "Funcionário não encontrado ou inativo."}
        cursor.execute("""
            INSERT INTO exames
                (funcionario_id, tipo, data_prevista, data_agendada,
                 horario, local_exame, status, observacao, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, 'AGENDADO', ?, GETDATE())
        """, (dados.funcionario_id, dados.tipo, data_prevista, data_agendada,
              horario, dados.local_exame.strip(), dados.observacao))
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
        return {"erro": f"Falha ao agendar: {str(e)}"}

# ==========================================================
# EXAMES AGENDADOS
# ==========================================================
@app.get("/exames/agendados")
def exames_agendados(pagina: int = 1, por_pagina: int = 20):
    if pagina < 1:
        pagina = 1
    if por_pagina < 1 or por_pagina > 100:
        por_pagina = 20
    try:
        from backend.whatsapp import montar_link_whatsapp
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT COUNT(*) FROM exames WHERE status IN ('AGENDADO', 'CONFIRMADO')")
        total = cursor.fetchone()[0]
        total_paginas = max(1, (total + por_pagina - 1) // por_pagina)
        if pagina > total_paginas:
            pagina = total_paginas
        offset = (pagina - 1) * por_pagina
        cursor.execute("""
            SELECT
                e.id, f.matricula, f.nome, f.cargo, f.celular,
                e.data_agendada, e.horario, e.local_exame,
                e.status, e.criado_em, e.observacao, e.confirmado_em
            FROM exames e
            INNER JOIN funcionarios f ON f.id = e.funcionario_id
            WHERE e.status IN ('AGENDADO', 'CONFIRMADO')
            ORDER BY e.criado_em DESC, e.id DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """, (offset, por_pagina))
        lista = []
        for row in cursor.fetchall():
            data_agendada = row[5]
            data_str = data_agendada.strftime("%d/%m/%Y") if hasattr(data_agendada, "strftime") else str(data_agendada)
            link = montar_link_whatsapp(celular=row[4], nome=row[2], data_agendada=data_str)
            lista.append({
                "exame_id": row[0],
                "matricula": row[1],
                "nome": row[2],
                "cargo": row[3],
                "celular": row[4],
                "data_agendada": data_str,
                "horario": "07:00 - 15:00",
                "local_exame": "Dual Saúde - Rua Almirante Teffé, 669 - Centro, Niterói",
                "status": row[8],
                "observacao": row[10] or "",
                "confirmado_em": row[11].strftime("%d/%m/%Y %H:%M") if row[11] else None,
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
        return {"erro": f"Falha ao listar agendados: {str(e)}"}

# ==========================================================
# CANCELAR EXAME
# ==========================================================
@app.put("/exames/{exame_id}/cancelar")
def cancelar_exame(exame_id: int):
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT e.id, f.nome 
            FROM exames e
            INNER JOIN funcionarios f ON f.id = e.funcionario_id
            WHERE e.id = ? AND e.status = 'AGENDADO'
        """, (exame_id,))
        exame = cursor.fetchone()
        if not exame:
            conexao.close()
            return {"erro": "Exame não encontrado ou já foi realizado/cancelado."}
        cursor.execute("""
            UPDATE exames SET status = 'CANCELADO', atualizado_em = GETDATE()
            WHERE id = ?
        """, (exame_id,))
        conexao.commit()
        conexao.close()
        return {"mensagem": f"Exame de {exame[1]} foi CANCELADO com sucesso!"}
    except Exception as e:
        return {"erro": f"Falha ao cancelar exame: {str(e)}"}

# ==========================================================
# CONFIRMAR AGENDAMENTO
# ==========================================================
@app.put("/exames/{exame_id}/confirmar")
def confirmar_agendamento(exame_id: int):
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT e.id, f.nome, e.observacao
            FROM exames e
            INNER JOIN funcionarios f ON f.id = e.funcionario_id
            WHERE e.id = ? AND e.status = 'AGENDADO'
        """, (exame_id,))
        exame = cursor.fetchone()
        if not exame:
            conexao.close()
            return {"erro": "Exame não encontrado ou não está agendado."}
        
        obs_atual = exame[2] or ""
        if "✅ Confirmado" not in obs_atual:
            nova_obs = f"✅ Confirmado - Mensagem enviada via WhatsApp\n{obs_atual}".strip()
        else:
            nova_obs = obs_atual
        
        cursor.execute("""
            UPDATE exames 
            SET status = 'CONFIRMADO',
                observacao = ?,
                confirmado_em = GETDATE(),
                atualizado_em = GETDATE()
            WHERE id = ?
        """, (nova_obs, exame_id))
        
        conexao.commit()
        conexao.close()
        return {"mensagem": f"✅ Agendamento de {exame[1]} confirmado com sucesso!"}
    except Exception as e:
        return {"erro": f"Falha ao confirmar: {str(e)}"}

# ==========================================================
# ATUALIZAR OBSERVAÇÃO (CORRIGIDO)
# ==========================================================
@app.put("/exames/{exame_id}/observacao")
def atualizar_observacao(exame_id: int, dados: AtualizarObservacao):
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        
        # Verifica se o exame existe (NÃO seleciona nome da tabela exames)
        cursor.execute("SELECT id FROM exames WHERE id = ?", (exame_id,))
        exame = cursor.fetchone()
        if not exame:
            conexao.close()
            return {"erro": "Exame não encontrado."}
        
        # Atualiza a observação
        cursor.execute("""
            UPDATE exames 
            SET observacao = ?,
                atualizado_em = GETDATE()
            WHERE id = ?
        """, (dados.observacao, exame_id))
        
        conexao.commit()
        conexao.close()
        
        return {
            "mensagem": "✅ Observação atualizada com sucesso!",
            "observacao": dados.observacao
        }
    except Exception as e:
        print("ERRO AO ATUALIZAR OBSERVAÇÃO:", e)
        return {"erro": f"Falha ao atualizar observação: {str(e)}"}

# ==========================================================
# PDF DE CONVOCAÇÃO
# ==========================================================
@app.get("/exames/{exame_id}/pdf")
def exame_pdf(exame_id: int):
    try:
        from backend.convocacao_pdf import gerar_pdf_convocacao
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT f.nome, f.matricula, f.cargo, e.data_agendada, e.horario, e.local_exame
            FROM exames e
            INNER JOIN funcionarios f ON f.id = e.funcionario_id
            WHERE e.id = ?
        """, (exame_id,))
        row = cursor.fetchone()
        conexao.close()
        if not row:
            return {"erro": "Exame não encontrado."}
        data_agendada = row[3]
        horario = row[4]
        data_str = data_agendada.strftime("%d/%m/%Y") if hasattr(data_agendada, "strftime") else str(data_agendada)
        horario_str = horario.strftime("%H:%M") if hasattr(horario, "strftime") else str(horario)[:5]
        pdf_bytes = gerar_pdf_convocacao(
            nome=row[0], matricula=row[1], cargo=row[2],
            data_agendada=data_str, horario=horario_str,
            local_exame=row[5] or "Dual Saúde"
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="convocacao_{row[1]}.pdf"'}
        )
    except Exception as e:
        return {"erro": f"Falha ao gerar PDF: {str(e)}"}

# ==========================================================
# RELATÓRIO PDF (CORRIGIDO - TABELA MELHORADA)
# ==========================================================
@app.get("/exames/relatorio-pdf")
def relatorio_agendados_pdf():
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        import io

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("""
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
        """)
        dados = cursor.fetchall()
        conexao.close()

        if not dados:
            return {"erro": "Nenhum exame agendado ou confirmado para gerar relatório."}

        # Usar página em paisagem (landscape) para caber mais colunas
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), 
                                leftMargin=1*cm, rightMargin=1*cm,
                                topMargin=1.5*cm, bottomMargin=1*cm)
        
        styles = getSampleStyleSheet()
        elements = []

        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=1,
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph("RELATÓRIO DE EXAMES AGENDADOS", title_style))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 10))

        # Cabeçalho da tabela
        data = [["Matrícula", "Nome", "Cargo", "Data", "Local", "Status", "Observação"]]
        
        for row in dados:
            # Formata a data
            data_agendada = row[3]
            if hasattr(data_agendada, "strftime"):
                data_str = data_agendada.strftime("%d/%m/%Y")
            else:
                data_str = str(data_agendada)
            
            # Formata o status
            status = row[5]
            if status == 'AGENDADO':
                status_text = '⏳ Pendente'
                status_color = colors.orange
            elif status == 'CONFIRMADO':
                status_text = '✅ Confirmado'
                status_color = colors.green
            elif status == 'CANCELADO':
                status_text = '❌ Cancelado'
                status_color = colors.red
            else:
                status_text = status
                status_color = colors.black
            
            # Formata a observação
            obs = row[6] or ""
            if "confirmado" in obs.lower():
                obs = "✅ Mensagem enviada"
            elif obs == "":
                obs = "—"
            
            # Formata o local
            local = row[4] or "Dual Saúde"
            # Limita o tamanho do local para não quebrar a tabela
            if len(local) > 35:
                local = local[:35] + "..."
            
            data.append([
                str(row[0]),  # Matrícula
                str(row[1])[:30],  # Nome (limitado a 30 caracteres)
                str(row[2])[:25],  # Cargo (limitado a 25 caracteres)
                data_str,  # Data
                local,  # Local
                status_text,  # Status
                obs[:25]  # Observação (limitado a 25 caracteres)
            ])

        # Larguras das colunas
        col_widths = [2.5*cm, 5.5*cm, 4*cm, 2.5*cm, 5*cm, 2.8*cm, 3.5*cm]
        
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4e78')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            # Linhas de dados
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c0c0c0')),
            # Padding
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            # Alinhamento do status
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"Total de registros: {len(dados)}", styles['Normal']))

        doc.build(elements)
        buffer.seek(0)
        
        return Response(
            content=buffer.read(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="relatorio_agendados_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf"'
            }
        )
        
    except Exception as e:
        print("ERRO NO RELATÓRIO PDF:", e)
        return {"erro": f"Falha ao gerar relatório: {str(e)}"}