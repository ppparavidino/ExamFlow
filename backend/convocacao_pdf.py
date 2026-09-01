"""
Gera PDF de convocação para exame periódico.
"""

import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


def gerar_pdf_convocacao(
    nome: str,
    matricula: str,
    cargo: str,
    data_agendada: str,
    horario: str,
    local_exame: str,
) -> bytes:
    """
    Monta um PDF simples em memória e devolve os bytes.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    # Margem esquerda
    x = 2.5 * cm
    y = altura - 3 * cm

    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, "VIACAO PENDOTIBA")

    y -= 1.2 * cm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, "CONVOCACAO PARA EXAME PERIODICO")

    y -= 0.4 * cm
    c.setStrokeColorRGB(0.12, 0.30, 0.47)
    c.setLineWidth(1.5)
    c.line(x, y, largura - 2.5 * cm, y)

    y -= 1.5 * cm
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0, 0, 0)

    linhas = [
        f"Funcionario: {nome}",
        f"Matricula: {matricula}",
        f"Cargo: {cargo}",
        "",
        f"Data: {data_agendada}",
        f"Horario: {horario}",
        f"Local: {local_exame}",
        "",
        "Por favor, compareca no horario informado.",
        "Em caso de duvidas, procure o setor de enfermagem.",
    ]

    for linha in linhas:
        c.drawString(x, y, linha)
        y -= 0.75 * cm

    y -= 1 * cm
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(x, y, "Documento gerado pelo sistema ExamFlow.")

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer.read()