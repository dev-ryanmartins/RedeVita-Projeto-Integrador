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
            elementos.append(Paragraph(self.texto_marca_dagua, estilo_rodape))
            elementos.append(Spacer(1, 0.3*cm))

            return elementos
        except Exception as e:
            logger.error(f"Erro ao criar rodapé: {str(e)}")
            return []

    def gerar_pdf_doacao(self, dados_doacao: Dict) -> Optional[bytes]:
        try:
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import cm
            from io import BytesIO

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=(21*cm, 29.7*cm), rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

            elementos = []
            elementos.extend(self.criar_cabecalho("Recibo de Doação"))

            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_LEFT

            styles = getSampleStyleSheet()
            estilo_normal = ParagraphStyle(
                'NormalCustom',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor(COR_TEXTO),
                spaceAfter=6,
                fontName='Helvetica',
                alignment=TA_LEFT
            )

            elementos.append(Paragraph(f"<b>Doador:</b> {dados_doacao.get('doador', 'N/A')}", estilo_normal))
            elementos.append(Paragraph(f"<b>Medicamento:</b> {dados_doacao.get('medicamento', 'N/A')}", estilo_normal))
            elementos.append(Paragraph(f"<b>Quantidade:</b> {dados_doacao.get('quantidade', 'N/A')}", estilo_normal))
            elementos.append(Paragraph(f"<b>Data:</b> {dados_doacao.get('data', 'N/A')}", estilo_normal))

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

    def gerar_pdf_retirada(self, dados_retirada: Dict) -> Optional[bytes]:
        try:
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import cm
            from io import BytesIO

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=(21*cm, 29.7*cm), rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

            elementos = []
            elementos.extend(self.criar_cabecalho("Comprovante de Retirada"))

            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_LEFT

            styles = getSampleStyleSheet()
            estilo_normal = ParagraphStyle(
                'NormalCustom',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor(COR_TEXTO),
                spaceAfter=6,
                fontName='Helvetica',
                alignment=TA_LEFT
            )

            elementos.append(Paragraph(f"<b>Usuário:</b> {dados_retirada.get('usuario', 'N/A')}", estilo_normal))
            elementos.append(Paragraph(f"<b>Medicamento:</b> {dados_retirada.get('medicamento', 'N/A')}", estilo_normal))
            elementos.append(Paragraph(f"<b>Quantidade:</b> {dados_retirada.get('quantidade', 'N/A')}", estilo_normal))
            elementos.append(Paragraph(f"<b>Data:</b> {dados_retirada.get('data', 'N/A')}", estilo_normal))

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

    def gerar_pdf_impacto_social(self, dados_impacto: Dict) -> Optional[bytes]:
        try:
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from io import BytesIO

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=(21*cm, 29.7*cm), rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

            elementos = []
            elementos.extend(self.criar_cabecalho("Relatório de Impacto Social"))

            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_LEFT

            styles = getSampleStyleSheet()
            estilo_normal = ParagraphStyle(
                'NormalCustom',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor(COR_TEXTO),
                spaceAfter=6,
                fontName='Helvetica',
                alignment=TA_LEFT
            )

            estilo_fonte = ParagraphStyle(
                'FontePequena',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#94a3b8'),
                spaceBefore=12,
                fontName='Helvetica',
                leading=12
            )
            
            elementos.append(Paragraph(
                "<b>Fonte dos dados:</b> Sistema RedeVita - Banco de Dados Interno. "
                "Métricas calculadas com base em doações, estoque e registros operacionais.",
                estilo_fonte
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
            logger.error(f"Erro ao gerar PDF de impacto social: {str(e)}")
            raise

    def gerar_pdf_async(self, tipo_documento: str, dados: Dict, callback=None):
        """Gera PDF de forma assíncrona usando thread pool"""
        def _gerar():
            try:
                if tipo_documento == 'doacao':
                    pdf_bytes = self.gerar_pdf_doacao(dados)
                elif tipo_documento == 'retirada':
                    pdf_bytes = self.gerar_pdf_retirada(dados)
                elif tipo_documento == 'recibo_entrega':
                    pdf_bytes = self.gerar_recibo_entrega(dados)
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

    def gerar_recibo_entrega(self, dados_entrega: Dict) -> Optional[bytes]:
        """
        Gera PDF de recibo de entrega institucional.
        
        Args:
            dados_entrega: Dicionário com dados da entrega
                - entrega_id: ID da entrega
                - reserva_id: ID da reserva
                - farmacia_origem: Nome da farmácia doadora
                - cnpj_origem: CNPJ da farmácia doadora
                - instituicao_destino: Nome da instituição receptora
                - cnpj_destino: CNPJ da instituição receptora
                - medicamento_nome: Nome do medicamento
                - medicamento_lote: Lote do medicamento
                - medicamento_validade: Data de validade
                - quantidade: Quantidade entregue
                - recebido_por: Nome do usuário que recebeu
                - recebido_em: Data/hora do recebimento
                - observacoes: Observações do recebimento (opcional)
                
        Returns:
            bytes: Conteúdo do PDF ou None em caso de erro
        """
        try:
            from reportlab.lib import colors
            from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib.enums import TA_LEFT, TA_CENTER
            from reportlab.pdfgen import canvas
            from io import BytesIO
            
            buffer = BytesIO()
            doc = canvas.Canvas(buffer, pagesize=(21*cm, 29.7*cm))
            
            # Cores
            cor_azul = colors.HexColor(COR_AZUL_PRINCIPAL)
            cor_texto = colors.HexColor(COR_TEXTO)
            cor_cinza = colors.HexColor('#64748b')
            
            # Cabeçalho com título
            doc.setFont('Helvetica-Bold', 16)
            doc.setFillColor(cor_azul)
            doc.drawString(2*cm, 27*cm, "RECIBO DE ENTREGA")
            
            doc.setFont('Helvetica', 10)
            doc.setFillColor(cor_cinza)
            doc.drawString(2*cm, 26.5*cm, f"Entrega #{dados_entrega.get('entrega_id', 'N/A')}")
            doc.drawString(2*cm, 26.2*cm, f"Reserva #{dados_entrega.get('reserva_id', 'N/A')}")
            
            # Linha separadora
            doc.setStrokeColor(cor_azul)
            doc.setLineWidth(2)
            doc.line(2*cm, 25.8*cm, 19*cm, 25.8*cm)
            
            # Seção de Origem
            y_pos = 25*cm
            doc.setFont('Helvetica-Bold', 12)
            doc.setFillColor(cor_texto)
            doc.drawString(2*cm, y_pos, "ORIGEM")
            
            y_pos -= 0.5*cm
            doc.setFont('Helvetica', 10)
            doc.setFillColor(cor_cinza)
            doc.drawString(2*cm, y_pos, f"Farmácia: {dados_entrega.get('farmacia_origem', 'N/A')}")
            y_pos -= 0.4*cm
            doc.drawString(2*cm, y_pos, f"CNPJ: {dados_entrega.get('cnpj_origem', 'N/A')}")
            
            # Seção de Destino
            y_pos -= 0.8*cm
            doc.setFont('Helvetica-Bold', 12)
            doc.setFillColor(cor_texto)
            doc.drawString(2*cm, y_pos, "DESTINO")
            
            y_pos -= 0.5*cm
            doc.setFont('Helvetica', 10)
            doc.setFillColor(cor_cinza)
            doc.drawString(2*cm, y_pos, f"Instituição: {dados_entrega.get('instituicao_destino', 'N/A')}")
            y_pos -= 0.4*cm
            doc.drawString(2*cm, y_pos, f"CNPJ: {dados_entrega.get('cnpj_destino', 'N/A')}")
            
            # Seção de Medicamento
            y_pos -= 0.8*cm
            doc.setFont('Helvetica-Bold', 12)
            doc.setFillColor(cor_texto)
            doc.drawString(2*cm, y_pos, "MEDICAMENTO")
            
            y_pos -= 0.5*cm
            doc.setFont('Helvetica', 10)
            doc.setFillColor(cor_cinza)
            doc.drawString(2*cm, y_pos, f"Nome: {dados_entrega.get('medicamento_nome', 'N/A')}")
            y_pos -= 0.4*cm
            doc.drawString(2*cm, y_pos, f"Lote: {dados_entrega.get('medicamento_lote', 'N/A')}")
            y_pos -= 0.4*cm
            validade = dados_entrega.get('medicamento_validade', 'N/A')
            if isinstance(validade, datetime):
                validade = validade.strftime('%d/%m/%Y')
            doc.drawString(2*cm, y_pos, f"Validade: {validade}")
            y_pos -= 0.4*cm
            doc.drawString(2*cm, y_pos, f"Quantidade: {dados_entrega.get('quantidade', 'N/A')} unidades")
            
            # Seção de Recebimento
            y_pos -= 0.8*cm
            doc.setFont('Helvetica-Bold', 12)
            doc.setFillColor(cor_texto)
            doc.drawString(2*cm, y_pos, "RECEBIMENTO")
            
            y_pos -= 0.5*cm
            doc.setFont('Helvetica', 10)
            doc.setFillColor(cor_cinza)
            doc.drawString(2*cm, y_pos, f"Recebido por: {dados_entrega.get('recebido_por', 'N/A')}")
            y_pos -= 0.4*cm
            recebido_em = dados_entrega.get('recebido_em', 'N/A')
            if isinstance(recebido_em, datetime):
                recebido_em = recebido_em.strftime('%d/%m/%Y às %H:%M')
            doc.drawString(2*cm, y_pos, f"Data/Hora: {recebido_em}")
            
            # Observações se existirem
            observacoes = dados_entrega.get('observacoes')
            if observacoes:
                y_pos -= 0.8*cm
                doc.setFont('Helvetica-Bold', 12)
                doc.setFillColor(cor_texto)
                doc.drawString(2*cm, y_pos, "OBSERVAÇÕES")
                
                y_pos -= 0.5*cm
                doc.setFont('Helvetica', 10)
                doc.setFillColor(cor_cinza)
                # Quebra observações em linhas se necessário
                lines = []
                line = ""
                for word in observacoes.split():
                    if len(line + word) > 80:
                        lines.append(line)
                        line = word + " "
                    else:
                        line += word + " "
                if line:
                    lines.append(line)
                
                for line in lines[:5]:  # Máximo 5 linhas
                    doc.drawString(2*cm, y_pos, line)
                    y_pos -= 0.4*cm
            
            # Rodapé
            y_pos = 3*cm
            doc.setFont('Helvetica', 9)
            doc.setFillColor(cor_cinza)
            doc.drawString(2*cm, y_pos, "Este documento é comprovativo de recebimento e não substitui prescrição médica.")
            y_pos -= 0.4*cm
            doc.drawString(2*cm, y_pos, "Emitido automaticamente pelo sistema RedeVita.")
            
            # Marca d'água
            doc.setFont('Helvetica', 8)
            doc.setFillColor(colors.lightgrey)
            doc.drawCentredString(10.5*cm, 1.5*cm, "RedeVita - Medicamentos para Todos")
            
            doc.save()
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Erro ao gerar recibo de entrega: {str(e)}")
            return None


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


def gerar_recibo_entrega_async(dados_entrega: Dict, callback=None):
    """Gera PDF de recibo de entrega de forma assíncrona"""
    gerador = obter_gerador_pdf()
    return gerador.gerar_pdf_async('recibo_entrega', dados_entrega, callback)
