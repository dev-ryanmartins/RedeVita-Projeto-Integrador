"""
PDF Generator - Gerador Assíncrono de Relatórios PDF
Utiliza reportlab para gerar PDFs personalizados com logotipo oficial RedeVita
Design profissional e elegante com paleta de cores corporativa
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

# SVG do logotipo oficial RedeVita
REDEVITA_LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 72 56" width="50" height="50">
  <defs>
    <style>
      .cruz-borda { fill: none; stroke: #0ea5e9; stroke-width: 2.8; stroke-linecap: round; stroke-linejoin: round; }
      .coracao-vermelho { fill: #f43f5e; }
      .ecg-linha { fill: none; stroke: #ffffff; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }
    </style>
  </defs>
  <path class="cruz-borda" d="M 27 5 h 12 a 4 4 0 0 1 4 4 v 11 h 11 a 4 4 0 0 1 4 4 v 10 a 4 4 0 0 1 -4 4 h -11 v 11 a 4 4 0 0 1 -4 4 h -12 a 4 4 0 0 1 -4 -4 v -11 h -11 a 4 4 0 0 1 -4 -4 v -10 a 4 4 0 0 1 4 -4 h 11 v -11 a 4 4 0 0 1 4 -4 z" />
  <path class="coracao-vermelho" transform="translate(1, -4) scale(1.5)" d="M 40 20 C 40 13 31 11 27 17 C 23 11 14 13 14 20 C 14 29 27 37 27 37 C 27 37 40 29 40 20 Z" />
  <path class="ecg-linha" d="M 21 25 h 5 l 3.5 -11 l 5 22 l 4.5 -14 l 3.5 3 h 6" />
</svg>
"""


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
    Gera comprovantes de doação, ordens de retirada e relatórios com design profissional.
    """
    
    # Cores corporativas RedeVita
    COR_PRIMARIA = '#0ea5e9'  # Azul principal
    COR_SECUNDARIA = '#3b82f6'  # Azul secundário
    COR_TEXTO = '#1e293b'  # Cinza escuro para texto
    COR_FUNDO = '#f8fafc'  # Cinza claro para fundo
    COR_ACESSO = '#f43f5e'  # Vermelho para destaques
    
    def __init__(self):
        """Inicializa o gerador de PDFs"""
        self.marca_dagua_texto = "RedeVita - Medicamentos para Todos"
    
    def _criar_cabecalho_profissional(self, titulo: str):
        """
        Cria cabeçalho profissional com logotipo e título.
        
        Args:
            titulo: Título do documento
            
        Returns:
            Lista de elementos do cabeçalho
        """
        try:
            from reportlab.lib import colors
            from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            
            styles = getSampleStyleSheet()
            
            # Estilo para título
            titulo_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor(self.COR_TEXTO),
                spaceAfter=6,
                spaceBefore=6,
                fontName='Helvetica-Bold',
                alignment=TA_LEFT
            )
            
            # Estilo para subtítulo
            subtitulo_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#64748b'),
                spaceAfter=12,
                fontName='Helvetica',
                alignment=TA_LEFT
            )
            
            # Data atual
            data_atual = datetime.now().strftime('%d/%m/%Y às %H:%M')
            
            elementos = []
            
            # Linha de separação elegante
            elementos.append(Spacer(1, 0.3*cm))
            
            # Título do documento
            elementos.append(Paragraph(titulo, titulo_style))
            elementos.append(Paragraph(f"Emitido em: {data_atual}", subtitulo_style))
            
            # Linha de separação horizontal
            elementos.append(Spacer(1, 0.2*cm))
            
            linha = Table([['']], colWidths=[16*cm])
            linha.setStyle(TableStyle([
                ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor(self.COR_PRIMARIA)),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#e2e8f0')),
            ]))
            elementos.append(linha)
            elementos.append(Spacer(1, 0.5*cm))
            
            return elementos
            
        except Exception as e:
            logger.error(f"Erro ao criar cabeçalho: {str(e)}")
            return []
    
    def _criar_rodape_profissional(self):
        """
        Cria rodape profissional com informações do sistema.
        
        Returns:
            Lista de elementos do rodapé
        """
        try:
            from reportlab.lib import colors
            from reportlab.platypus import Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib.enums import TA_CENTER
            
            styles = getSampleStyleSheet()
            
            rodape_style = ParagraphStyle(
                'CustomFooter',
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
                rodape_style
            ))
            
            return elementos
            
        except Exception as e:
            logger.error(f"Erro ao criar rodapé: {str(e)}")
            return []
    
    def gerar_pdf_doacao(self, dados_doacao: Dict) -> bytes:
        """
        Gera PDF de comprovante de doação com design profissional.
        
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
            
            # Cria documento PDF com margens profissionais
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2.5*cm,
                bottomMargin=2*cm
            )
            
            # Estilos
            styles = getSampleStyleSheet()
            
            # Elementos do PDF
            elementos = []
            
            # Cabeçalho profissional
            elementos.extend(self._criar_cabecalho_profissional("Comprovante de Doação"))
            
            # Tabela de dados da doação com design elegante
            # Validação de dados com fallback seguro
            dados = [
                ['Doador', dados_doacao.get('doador_nome') if dados_doacao.get('doador_nome') else 'Não informado'],
                ['Medicamento', dados_doacao.get('medicamento_nome') if dados_doacao.get('medicamento_nome') else 'Não informado'],
                ['Quantidade', str(dados_doacao.get('quantidade', 0)) if dados_doacao.get('quantidade') is not None else '0'],
                ['Lote', dados_doacao.get('lote') if dados_doacao.get('lote') else 'Não informado'],
                ['Validade', dados_doacao.get('data_validade') if dados_doacao.get('data_validade') else 'Não informado'],
                ['Farmácia', dados_doacao.get('farmacia_nome') if dados_doacao.get('farmacia_nome') else 'Não informado'],
            ]
            
            tabela = Table(dados, colWidths=[5*cm, 8*cm])
            tabela.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor(self.COR_TEXTO)),
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
            
            # Caixa de agradecimento com destaque
            agradecimento_style = ParagraphStyle(
                'Agradecimento',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor(self.COR_PRIMARIA),
                spaceBefore=6,
                spaceAfter=6,
                fontName='Helvetica-Bold',
                alignment=1  # CENTER
            )
            
            mensagem_style = ParagraphStyle(
                'Mensagem',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#64748b'),
                spaceAfter=6,
                fontName='Helvetica',
                alignment=1  # CENTER
            )
            
            elementos.append(Paragraph("🎉 Agradecemos sua generosa doação!", agradecimento_style))
            elementos.append(Paragraph(
                "Sua contribuição ajudará muitas pessoas que necessitam desses medicamentos.",
                mensagem_style
            ))
            
            # Rodapé profissional
            elementos.extend(self._criar_rodape_profissional())
            
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
            # Gerar PDF de fallback em caso de erro
            return self._gerar_pdf_fallback("Comprovante de Doação", str(e))
    
    def _gerar_pdf_fallback(self, titulo: str, erro: str) -> bytes:
        """
        Gera um PDF de fallback simples em caso de erro na geração principal.
        
        Args:
            titulo: Título do documento
            erro: Mensagem de erro
            
        Returns:
            Bytes do PDF gerado
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
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
            
            # Cabeçalho profissional
            elementos.extend(self._criar_cabecalho_profissional(titulo))
            
            # Mensagem de erro em destaque
            erro_style = ParagraphStyle(
                'Erro',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#ef4444'),
                spaceBefore=12,
                spaceAfter=12,
                fontName='Helvetica-Bold',
                alignment=1  # CENTER
            )
            
            info_style = ParagraphStyle(
                'Info',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#64748b'),
                spaceAfter=12,
                fontName='Helvetica',
                alignment=1  # CENTER
            )
            
            elementos.append(Paragraph("⚠️ Ocorreu um erro ao gerar o documento completo", erro_style))
            elementos.append(Paragraph(f"Detalhes: {erro}", info_style))
            elementos.append(Spacer(1, 1*cm))
            elementos.append(Paragraph("Por favor, entre em contato com o suporte técnico.", info_style))
            
            # Rodapé profissional
            elementos.extend(self._criar_rodape_profissional())
            
            doc.build(elementos)
            
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            return pdf_bytes
            
        except Exception as fallback_error:
            logger.error(f"Erro ao gerar PDF de fallback: {str(fallback_error)}")
            # Retornar bytes vazios se tudo falhar
            return b''
    
    def gerar_pdf_retirada(self, dados_retirada: Dict) -> bytes:
        """
        Gera PDF de ordem de retirada para paciente com design profissional.
        
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
                topMargin=2.5*cm,
                bottomMargin=2*cm
            )
            
            styles = getSampleStyleSheet()
            
            elementos = []
            
            # Cabeçalho profissional
            elementos.extend(self._criar_cabecalho_profissional("Ordem de Retirada"))
            
            # Título da seção
            secao_style = ParagraphStyle(
                'Secao',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor(self.COR_PRIMARIA),
                spaceBefore=12,
                spaceAfter=6,
                fontName='Helvetica-Bold'
            )
            
            # Dados do paciente com validação
            elementos.append(Paragraph("Dados do Paciente", secao_style))
            elementos.append(Spacer(1, 0.2*cm))
            
            dados_paciente = [
                ['Nome', dados_retirada.get('paciente_nome') if dados_retirada.get('paciente_nome') else 'Não informado'],
                ['CPF', dados_retirada.get('paciente_cpf') if dados_retirada.get('paciente_cpf') else 'Não informado'],
                ['Telefone', dados_retirada.get('paciente_telefone') if dados_retirada.get('paciente_telefone') else 'Não informado'],
            ]
            
            tabela_paciente = Table(dados_paciente, colWidths=[5*cm, 8*cm])
            tabela_paciente.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor(self.COR_TEXTO)),
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
            
            # Dados do medicamento com validação
            elementos.append(Paragraph("Medicamento a Retirar", secao_style))
            elementos.append(Spacer(1, 0.2*cm))
            
            dados_medicamento = [
                ['Medicamento', dados_retirada.get('medicamento_nome') if dados_retirada.get('medicamento_nome') else 'Não informado'],
                ['Quantidade', str(dados_retirada.get('quantidade', 0)) if dados_retirada.get('quantidade') is not None else '0'],
                ['Lote', dados_retirada.get('lote') if dados_retirada.get('lote') else 'Não informado'],
                ['Validade', dados_retirada.get('data_validade') if dados_retirada.get('data_validade') else 'Não informado'],
                ['Farmácia', dados_retirada.get('farmacia_nome') if dados_retirada.get('farmacia_nome') else 'Não informado'],
            ]
            
            tabela_medicamento = Table(dados_medicamento, colWidths=[5*cm, 8*cm])
            tabela_medicamento.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor(self.COR_TEXTO)),
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
            
            # Instruções com destaque
            instrucoes_style = ParagraphStyle(
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
                instrucoes_style
            ))
            
            # Rodapé profissional
            elementos.extend(self._criar_rodape_profissional())
            
            doc.build(elementos)
            
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            return pdf_bytes
            
        except ImportError:
            logger.error("reportlab não instalado. Use: pip install reportlab")
            raise ImportError("reportlab é necessário para gerar PDFs")
        except Exception as e:
            logger.error(f"Erro ao gerar PDF de retirada: {str(e)}")
            # Gerar PDF de fallback em caso de erro
            return self._gerar_pdf_fallback("Ordem de Retirada", str(e))
    
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
