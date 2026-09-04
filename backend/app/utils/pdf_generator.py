"""
PDF Generator - Gerador Assíncrono de Relatórios PDF
Utiliza reportlab para gerar PDFs personalizados com marca d'água do RedeVita
Disciplina: Programação Backend com Script - Geração de Documentos
"""

import logging
import threading
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

logger = logging.getLogger(__name__)

# Executor global para geração assíncrona de PDFs
_pdf_executor = ThreadPoolExecutor(max_workers=2)


@dataclass
class PDFConfig:
    """Configuração para geração de PDF"""
    titulo: str
    tipo: str  # 'doacao', 'retirada', 'relatorio'
    marca_dagua: bool = True
    cabecalho: bool = True
    rodape: bool = True


class PDFGenerator:
    """
    Gerador de PDFs assíncrono para o RedeVita.
    Gera comprovantes de doação, ordens de retirada e relatórios.
    """
    
    def __init__(self):
        """Inicializa o gerador de PDFs"""
        self.marca_dagua_texto = "RedeVita - Medicamentos para Todos"
    
    def gerar_pdf_doacao(self, dados_doacao: Dict) -> bytes:
        """
        Gera PDF de comprovante de doação.
        
        Args:
            dados_doacao: Dicionário com dados da doação
        
        Returns:
            Bytes do PDF gerado
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # Cria buffer de memória
            buffer = BytesIO()
            
            # Cria documento PDF
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # Estilos
            styles = getSampleStyleSheet()
            titulo_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#3b82f6'),
                spaceAfter=12
            )
            
            # Elementos do PDF
            elementos = []
            
            # Título
            elementos.append(Paragraph("Comprovante de Doação - RedeVita", titulo_style))
            elementos.append(Spacer(1, 0.5*cm))
            
            # Data de emissão
            data_emissao = datetime.now().strftime('%d/%m/%Y %H:%M')
            elementos.append(Paragraph(f"<b>Data de Emissão:</b> {data_emissao}", styles['Normal']))
            elementos.append(Spacer(1, 0.5*cm))
            
            # Tabela de dados da doação
            dados = [
                ['Doador', dados_doacao.get('doador_nome', 'N/A')],
                ['Medicamento', dados_doacao.get('medicamento_nome', 'N/A')],
                ['Quantidade', str(dados_doacao.get('quantidade', 0))],
                ['Lote', dados_doacao.get('lote', 'N/A')],
                ['Validade', dados_doacao.get('data_validade', 'N/A')],
                ['Farmácia', dados_doacao.get('farmacia_nome', 'N/A')],
            ]
            
            tabela = Table(dados, colWidths=[5*cm, 8*cm])
            tabela.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            
            elementos.append(tabela)
            elementos.append(Spacer(1, 1*cm))
            
            # Mensagem de agradecimento
            elementos.append(Paragraph(
                "<b>Agradecemos sua generosa doação!</b><br/>"
                "Sua contribuição ajudará muitas pessoas que necessitam desses medicamentos.",
                styles['Normal']
            ))
            
            # Marca d'água
            if True:  # Sempre adiciona marca d'água
                from reportlab.lib.enums import TA_CENTER
                elementos.append(Spacer(1, 2*cm))
                elementos.append(Paragraph(
                    self.marca_dagua_texto,
                    ParagraphStyle('Watermark', parent=styles['Normal'], 
                                  textColor=colors.grey, fontSize=8, alignment=TA_CENTER)
                ))
            
            # Constrói o PDF
            doc.build(elementos)
            
            # Obtém bytes do PDF
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
        """
        Gera PDF de ordem de retirada para paciente.
        
        Args:
            dados_retirada: Dicionário com dados da retirada
        
        Returns:
            Bytes do PDF gerado
        """
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
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            styles = getSampleStyleSheet()
            titulo_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#3b82f6'),
                spaceAfter=12
            )
            
            elementos = []
            
            # Título
            elementos.append(Paragraph("Ordem de Retirada - RedeVita", titulo_style))
            elementos.append(Spacer(1, 0.5*cm))
            
            # Data de emissão
            data_emissao = datetime.now().strftime('%d/%m/%Y %H:%M')
            elementos.append(Paragraph(f"<b>Data de Emissão:</b> {data_emissao}", styles['Normal']))
            elementos.append(Spacer(1, 0.5*cm))
            
            # Dados do paciente
            elementos.append(Paragraph("<b>Dados do Paciente:</b>", styles['Heading2']))
            elementos.append(Spacer(1, 0.3*cm))
            
            dados_paciente = [
                ['Nome', dados_retirada.get('paciente_nome', 'N/A')],
                ['CPF', dados_retirada.get('paciente_cpf', 'N/A')],
                ['Telefone', dados_retirada.get('paciente_telefone', 'N/A')],
            ]
            
            tabela_paciente = Table(dados_paciente, colWidths=[5*cm, 8*cm])
            tabela_paciente.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            
            elementos.append(tabela_paciente)
            elementos.append(Spacer(1, 0.5*cm))
            
            # Dados do medicamento
            elementos.append(Paragraph("<b>Medicamento a Retirar:</b>", styles['Heading2']))
            elementos.append(Spacer(1, 0.3*cm))
            
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
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            
            elementos.append(tabela_medicamento)
            elementos.append(Spacer(1, 1*cm))
            
            # Instruções
            elementos.append(Paragraph(
                "<b>Instruções:</b><br/>"
                "1. Apresente este documento na farmácia parceira.<br/>"
                "2. Leve documento de identificação com foto.<br/>"
                "3. A retirada deve ser feita em até 7 dias.",
                styles['Normal']
            ))
            
            # Marca d'água
            from reportlab.lib.enums import TA_CENTER
            elementos.append(Spacer(1, 2*cm))
            elementos.append(Paragraph(
                self.marca_dagua_texto,
                ParagraphStyle('Watermark', parent=styles['Normal'], 
                              textColor=colors.grey, fontSize=8, alignment=TA_CENTER)
            ))
            
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
    
    def gerar_pdf_async(self, tipo: str, dados: Dict, callback=None):
        """
        Gera PDF de forma assíncrona usando thread pool.
        
        Args:
            tipo: Tipo de PDF ('doacao' ou 'retirada')
            dados: Dados para gerar o PDF
            callback: Função de callback opcional quando o PDF estiver pronto
        """
        def _gerar():
            try:
                if tipo == 'doacao':
                    pdf_bytes = self.gerar_pdf_doacao(dados)
                elif tipo == 'retirada':
                    pdf_bytes = self.gerar_pdf_retirada(dados)
                else:
                    raise ValueError(f"Tipo de PDF não suportado: {tipo}")
                
                if callback:
                    callback(pdf_bytes, None)
                
                return pdf_bytes
            except Exception as e:
                logger.error(f"Erro na geração assíncrona de PDF: {str(e)}")
                if callback:
                    callback(None, e)
                raise
        
        _pdf_executor.submit(_gerar)


# Instância global do gerador
_pdf_generator: Optional[PDFGenerator] = None


def obter_gerador_pdf() -> PDFGenerator:
    """
    Obtém a instância global do gerador de PDF.
    """
    global _pdf_generator
    if _pdf_generator is None:
        _pdf_generator = PDFGenerator()
    return _pdf_generator


def gerar_pdf_doacao_async(dados_doacao: Dict, callback=None):
    """
    Gera PDF de doação de forma assíncrona.
    
    Args:
        dados_doacao: Dados da doação
        callback: Função callback opcional
    """
    gerador = obter_gerador_pdf()
    return gerador.gerar_pdf_async('doacao', dados_doacao, callback)


def gerar_pdf_retirada_async(dados_retirada: Dict, callback=None):
    """
    Gera PDF de retirada de forma assíncrona.
    
    Args:
        dados_retirada: Dados da retirada
        callback: Função callback opcional
    """
    gerador = obter_gerador_pdf()
    return gerador.gerar_pdf_async('retirada', dados_retirada, callback)
