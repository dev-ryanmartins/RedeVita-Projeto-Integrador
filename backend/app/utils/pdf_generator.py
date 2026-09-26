import logging
from datetime import datetime
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

logger = logging.getLogger(__name__)

_executor_pdf = ThreadPoolExecutor(max_workers=2)

COR_AZUL_PRINCIPAL = '#0ea5e9'
COR_AZUL_SECUNDARIO = '#3b82f6'
COR_TEXTO = '#1e293b'
COR_FUNDO = '#f8fafc'
COR_DESTAQUE = '#f43f5e'


class PDFGenerator:

    def __init__(self):
        self.texto_marca_dagua = "RedeVita - Medicamentos para Todos"

    def criar_cabecalho(self, titulo_documento: str):
        try:
            from reportlab.lib import colors
            from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib.enums import TA_LEFT

            styles = getSampleStyleSheet()

            estilo_titulo = ParagraphStyle(
                'TituloDoc',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor(COR_TEXTO),
                spaceAfter=6,
                spaceBefore=6,
                fontName='Helvetica-Bold',
                alignment=TA_LEFT
            )

            estilo_subtitulo = ParagraphStyle(
                'SubtituloDoc',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#64748b'),
                spaceAfter=12,
                fontName='Helvetica',
                alignment=TA_LEFT
            )

            data_hoje = datetime.now().strftime('%d/%m/%Y às %H:%M')

            elementos = []
            elementos.append(Spacer(1, 0.3*cm))
            elementos.append(Paragraph(titulo_documento, estilo_titulo))
            elementos.append(Paragraph(f"Emitido em: {data_hoje}", estilo_subtitulo))
            elementos.append(Spacer(1, 0.2*cm))

            linha = Table([['']], colWidths=[16*cm])
            linha.setStyle(TableStyle([
                ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor(COR_AZUL_PRINCIPAL)),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#e2e8f0')),
            ]))
            elementos.append(linha)
            elementos.append(Spacer(1, 0.5*cm))

            return elementos

        except Exception as e:
            logger.error(f"Erro ao criar cabeçalho: {str(e)}")
            return []

    def criar_rodape(self):
        try:
            from reportlab.lib import colors
            from reportlab.platypus import Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib.enums import TA_CENTER

            styles = getSampleStyleSheet()

            estilo_rodape = ParagraphStyle(
                'RodapeDoc',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#94a3b8'),
                spaceBefore=12,
                fontName='Helvetica',
                alignment=TA_CENTER
            )

            elementos = []
            elementos.append(Spacer(1, 1*cm))
            elementos.append(Paragraph(
                "RedeVita - Sistema de Gestão de Medicamentos | "
                "Documento Oficial | Não válido como prescrição médica",
                estilo_rodape
            ))

            return elementos

        except Exception as e:
            logger.error(f"Erro ao criar rodapé: {str(e)}")
            return []

    def gerar_pdf_doacao(self, dados_doacao: Dict) -> bytes:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm

            buffer = BytesIO()

            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2.5*cm,
                bottomMargin=2*cm
            )

            styles = getSampleStyleSheet()
            elementos = []

            elementos.extend(self.criar_cabecalho("Comprovante de Doação"))

            dados_tabela = [
                ['Doador', dados_doacao.get('doador_nome', 'N/A')],
                ['Medicamento', dados_doacao.get('medicamento_nome', 'N/A')],
                ['Quantidade', str(dados_doacao.get('quantidade', 0))],
                ['Lote', dados_doacao.get('lote', 'N/A')],
                ['Validade', dados_doacao.get('data_validade', 'N/A')],
                ['Farmácia', dados_doacao.get('farmacia_nome', 'N/A')],
            ]

            tabela = Table(dados_tabela, colWidths=[5*cm, 8*cm])
            tabela.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor(COR_TEXTO)),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (0, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))

            elementos.append(tabela)
            elementos.append(Spacer(1, 1*cm))

            estilo_agradecimento = ParagraphStyle(
                'Agradecimento',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor(COR_AZUL_PRINCIPAL),
                spaceBefore=6,
                spaceAfter=6,
                fontName='Helvetica-Bold',
                alignment=1
            )

            estilo_mensagem = ParagraphStyle(
                'Mensagem',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#64748b'),
                spaceAfter=6,
                fontName='Helvetica',
                alignment=1
            )

            elementos.append(Paragraph("🎉 Agradecemos sua generosa doação!", estilo_agradecimento))
            elementos.append(Paragraph(
                "Sua contribuição ajudará muitas pessoas que necessitam desses medicamentos.",
                estilo_mensagem
            ))

            elementos.extend(self.criar_rodape())

            doc.build(elementos)

            pdf_bytes = buffer.getvalue()
            buffer.close()

            return pdf_bytes

        except ImportError:
            logger.error("reportlab não instalado. Use: pip install reportlab")
            raise ImportError("reportlab é necessário para gerar PDFs")
        except Exception as e:
            logger.error(f"Erro ao gerar PDF de doação: {str(e)}")
            raise

    def gerar_pdf_retirada(self, dados_retirada: Dict) -> bytes:
        """Gera a ordem de retirada em PDF"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm

            buffer = BytesIO()

            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2.5*cm,
                bottomMargin=2*cm
            )

            styles = getSampleStyleSheet()
            elementos = []

            elementos.extend(self.criar_cabecalho("Ordem de Retirada"))

            estilo_secao = ParagraphStyle(
                'Secao',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor(COR_AZUL_PRINCIPAL),
                spaceBefore=12,
                spaceAfter=6,
                fontName='Helvetica-Bold'
            )

            elementos.append(Paragraph("Dados do Paciente", estilo_secao))
            elementos.append(Spacer(1, 0.2*cm))

            dados_paciente = [
                ['Nome', dados_retirada.get('paciente_nome', 'N/A')],
                ['CPF', dados_retirada.get('paciente_cpf', 'N/A')],
                ['Telefone', dados_retirada.get('paciente_telefone', 'N/A')],
            ]

            tabela_paciente = Table(dados_paciente, colWidths=[5*cm, 8*cm])
            tabela_paciente.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor(COR_TEXTO)),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))

            elementos.append(tabela_paciente)
            elementos.append(Spacer(1, 0.5*cm))

            elementos.append(Paragraph("Medicamento a Retirar", estilo_secao))
            elementos.append(Spacer(1, 0.2*cm))

            dados_medicamento = [
                ['Medicamento', dados_retirada.get('medicamento_nome', 'N/A')],
                ['Quantidade', str(dados_retirada.get('quantidade', 0))],
                ['Lote', dados_retirada.get('lote', 'N/A')],
                ['Validade', dados_retirada.get('data_validade', 'N/A')],
                ['Farmácia', dados_retirada.get('farmacia_nome', 'N/A')],
            ]

            tabela_medicamento = Table(dados_medicamento, colWidths=[5*cm, 8*cm])
            tabela_medicamento.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor(COR_TEXTO)),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))

            elementos.append(tabela_medicamento)
            elementos.append(Spacer(1, 0.8*cm))

            estilo_instrucoes = ParagraphStyle(
                'Instrucoes',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#64748b'),
                spaceBefore=6,
                spaceAfter=6,
                fontName='Helvetica',
                leading=14
            )

            elementos.append(Paragraph(
                "<b>Instruções:</b><br/>"
                "1. Apresente este documento na farmácia parceira.<br/>"
                "2. Leve documento de identificação com foto.<br/>"
                "3. A retirada deve ser feita em até 7 dias.",
                estilo_instrucoes
            ))

            elementos.extend(self.criar_rodape())

            doc.build(elementos)

            pdf_bytes = buffer.getvalue()
            buffer.close()

            return pdf_bytes

        except ImportError:
            logger.error("reportlab não instalado. Use: pip install reportlab")
            raise ImportError("reportlab é necessário para gerar PDFs")
        except Exception as e:
            logger.error(f"Erro ao gerar PDF de retirada: {str(e)}")
            raise

    def gerar_pdf_async(self, tipo_documento: str, dados: Dict, callback=None):
        """Gera PDF de forma assíncrona usando thread pool"""
        def _gerar():
            try:
                if tipo_documento == 'doacao':
                    pdf_bytes = self.gerar_pdf_doacao(dados)
                elif tipo_documento == 'retirada':
                    pdf_bytes = self.gerar_pdf_retirada(dados)
                else:
                    raise ValueError(f"Tipo de PDF não suportado: {tipo_documento}")

                if callback:
                    callback(pdf_bytes, None)

                return pdf_bytes
            except Exception as e:
                logger.error(f"Erro na geração assíncrona de PDF: {str(e)}")
                if callback:
                    callback(None, e)
                raise

        _executor_pdf.submit(_gerar)


_gerador_pdf: Optional[PDFGenerator] = None


def obter_gerador_pdf() -> PDFGenerator:
    """Retorna a instância única do gerador de PDF"""
    global _gerador_pdf
    if _gerador_pdf is None:
        _gerador_pdf = PDFGenerator()
    return _gerador_pdf


def gerar_pdf_doacao_async(dados_doacao: Dict, callback=None):
    """Gera PDF de doação de forma assíncrona"""
    gerador = obter_gerador_pdf()
    return gerador.gerar_pdf_async('doacao', dados_doacao, callback)


def gerar_pdf_retirada_async(dados_retirada: Dict, callback=None):
    """Gera PDF de retirada de forma assíncrona"""
    gerador = obter_gerador_pdf()
    return gerador.gerar_pdf_async('retirada', dados_retirada, callback)
