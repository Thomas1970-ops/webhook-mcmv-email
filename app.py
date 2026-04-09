"""
Webhook de Notificações MCMV com Email + WhatsApp Link (VERSÃO ASSÍNCRONA)
Recebe dados do Supabase e envia notificação por email com link para WhatsApp
Otimizado com envio assíncrono de email para evitar timeouts
"""

from flask import Flask, request, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
from dotenv import load_dotenv
import urllib.parse
from threading import Thread
import logging

load_dotenv()

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURAÇÕES EMAIL
# ============================================

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "abencoado.corretor1@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECEPTOR = os.getenv("EMAIL_RECEPTOR", "abencoado.corretor1@gmail.com")

# WhatsApp
SEU_NUMERO_WHATSAPP = os.getenv("SEU_NUMERO_WHATSAPP", "5511960853857")

# ============================================
# FUNÇÕES DE ENVIO
# ============================================

def enviar_email_sync(assunto: str, corpo_html: str, destinatario: str = EMAIL_RECEPTOR):
    """Envia email via SMTP (síncrono)"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"] = EMAIL_SENDER
        msg["To"] = destinatario
        
        # Versão texto simples
        corpo_texto = corpo_html.replace("<br>", "\n").replace("<b>", "").replace("</b>", "")
        
        parte_texto = MIMEText(corpo_texto, "plain", "utf-8")
        parte_html = MIMEText(corpo_html, "html", "utf-8")
        
        msg.attach(parte_texto)
        msg.attach(parte_html)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ Email enviado para {destinatario}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao enviar email: {str(e)}")
        return False


def enviar_email_async(assunto: str, corpo_html: str, destinatario: str = EMAIL_RECEPTOR):
    """Envia email de forma assíncrona (em thread separada)"""
    thread = Thread(
        target=enviar_email_sync,
        args=(assunto, corpo_html, destinatario),
        daemon=True
    )
    thread.start()
    return True


def gerar_link_whatsapp(numero: str, mensagem: str = ""):
    """Gera link para abrir WhatsApp com mensagem pré-preenchida"""
    numero_formatado = numero.replace("+", "").replace(" ", "").replace("-", "")
    if mensagem:
        mensagem_encoded = urllib.parse.quote(mensagem)
        return f"https://wa.me/{numero_formatado}?text={mensagem_encoded}"
    return f"https://wa.me/{numero_formatado}"


def formatar_email(dados: dict) -> tuple:
    """Formata os dados do lead em um email HTML"""
    
    record = dados.get("record", {})
    
    nome = record.get("nome", "N/A")
    whatsapp = record.get("whatsapp", "N/A")
    email = record.get("email", "N/A")
    renda = record.get("renda_mensal", 0)
    valor_imovel = record.get("valor_imovel", 0)
    entrada = record.get("entrada_propria", 0)
    fgts = record.get("saldo_fgts", 0)
    parcela = record.get("parcela_primeira", 0)
    faixa = record.get("faixa_mcmv", "N/A")
    taxa = record.get("taxa_juros_anual", 0)
    total_juros = record.get("total_juros", 0)
    total_pagar = record.get("total_pagar", 0)
    
    def formatar_moeda(valor):
        try:
            return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return f"R$ {valor}"
    
    # Link WhatsApp
    link_whatsapp = gerar_link_whatsapp(whatsapp, "Olá! Gostaria de mais informações sobre minha simulação de financiamento MCMV.")
    
    # HTML do Email
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .header {{ background-color: #1e3a8a; color: white; padding: 20px; border-radius: 5px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .section {{ margin: 20px 0; }}
            .section h2 {{ color: #1e3a8a; border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; }}
            .info-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
            .info-label {{ font-weight: bold; color: #333; }}
            .info-value {{ color: #666; }}
            .highlight {{ background-color: #fef3c7; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .button {{ display: inline-block; background-color: #25d366; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 5px 10px 0; font-weight: bold; }}
            .button-email {{ display: inline-block; background-color: #1e3a8a; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 5px 10px 0; font-weight: bold; }}
            .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚨 NOVO LEAD - SIMULADOR MCMV</h1>
            </div>
            
            <div class="section">
                <h2>👤 Dados do Cliente</h2>
                <div class="info-row">
                    <span class="info-label">Nome:</span>
                    <span class="info-value"><b>{nome}</b></span>
                </div>
                <div class="info-row">
                    <span class="info-label">WhatsApp:</span>
                    <span class="info-value"><b>{whatsapp}</b></span>
                </div>
                <div class="info-row">
                    <span class="info-label">Email:</span>
                    <span class="info-value"><b>{email}</b></span>
                </div>
            </div>
            
            <div class="section">
                <h2>📊 Dados da Simulação</h2>
                <div class="info-row">
                    <span class="info-label">Renda:</span>
                    <span class="info-value">{formatar_moeda(renda)}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Imóvel:</span>
                    <span class="info-value">{formatar_moeda(valor_imovel)}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Entrada:</span>
                    <span class="info-value">{formatar_moeda(entrada)}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">FGTS:</span>
                    <span class="info-value">{formatar_moeda(fgts)}</span>
                </div>
            </div>
            
            <div class="section">
                <h2>💰 Resultado da Simulação</h2>
                <div class="info-row">
                    <span class="info-label">Faixa MCMV:</span>
                    <span class="info-value"><b>{faixa}</b></span>
                </div>
                <div class="info-row">
                    <span class="info-label">Taxa de Juros:</span>
                    <span class="info-value"><b>{taxa}% a.a.</b></span>
                </div>
                <div class="highlight">
                    <div class="info-row">
                        <span class="info-label">Parcela:</span>
                        <span class="info-value" style="font-size: 18px; color: #1e3a8a;"><b>{formatar_moeda(parcela)}</b></span>
                    </div>
                </div>
                <div class="info-row">
                    <span class="info-label">Total de Juros:</span>
                    <span class="info-value">{formatar_moeda(total_juros)}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Total a Pagar:</span>
                    <span class="info-value">{formatar_moeda(total_pagar)}</span>
                </div>
            </div>
            
            <div class="section">
                <h2>🔗 Ações Rápidas</h2>
                <a href="{link_whatsapp}" class="button">💬 Chamar no WhatsApp</a>
                <a href="mailto:{email}" class="button-email">📧 Enviar Email</a>
            </div>
            
            <div class="footer">
                <p>Recebido em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
                <p>Zona Oeste MCMV - Simulador de Financiamento</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    assunto = f"🚨 NOVO LEAD: {nome} - Simulação MCMV"
    
    return assunto, html


# ============================================
# ROTAS
# ============================================

@app.route("/webhook/novo-lead", methods=["POST"])
def webhook_novo_lead():
    """Endpoint que recebe o webhook do Supabase"""
    
    try:
        dados = request.get_json()
        
        # Validar tipo de evento
        if dados.get("type") != "INSERT":
            return jsonify({"status": "ignorado", "motivo": "Apenas INSERT é processado"}), 200
        
        # Validar tabela
        if dados.get("table") != "simulacoes_financiamento":
            return jsonify({"status": "erro", "motivo": "Tabela inválida"}), 400
        
        # Formatar email
        assunto, corpo_html = formatar_email(dados)
        logger.info(f"📨 Email a enviar: {assunto}")
        
        # Enviar notificação de forma assíncrona
        enviar_email_async(assunto, corpo_html)
        
        # Retornar sucesso imediatamente (email será enviado em background)
        return jsonify({
            "status": "sucesso",
            "mensagem": "Notificação recebida e será processada",
            "lead": dados.get("record", {}).get("nome", "N/A")
        }), 200
            
    except Exception as e:
        logger.error(f"❌ Erro no webhook: {str(e)}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """Verificar se o servidor está online"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()}), 200


@app.route("/", methods=["GET"])
def index():
    """Página inicial"""
    return jsonify({
        "nome": "Webhook de Notificações MCMV",
        "versao": "3.1",
        "tipo": "Email + WhatsApp Link (Assíncrono)",
        "endpoints": {
            "webhook": "/webhook/novo-lead (POST)",
            "health": "/health (GET)"
        }
    }), 200


# ============================================
# EXECUTAR
# ============================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
