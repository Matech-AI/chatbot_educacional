import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from pathlib import Path

# Carregar variáveis de ambiente
load_dotenv()

# Configurações de e-mail
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USER)

# Verificar se as configurações de e-mail estão definidas
EMAIL_CONFIGURED = all([EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD])

# Arquivo para armazenar tokens de autenticação
AUTH_TOKENS_FILE = Path(__file__).parent / "auth_tokens.json"

def generate_temp_password(length=10):
    """Gera uma senha temporária aleatória"""
    characters = string.ascii_letters + string.digits + "!@#$%&*"
    # Garantir pelo menos um caractere de cada tipo
    password = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice("!@#$%&*")
    ]
    # Preencher o restante da senha
    password.extend(random.choice(characters) for _ in range(length - 4))
    # Embaralhar a senha
    random.shuffle(password)
    return ''.join(password)

def generate_auth_token(length=32):
    """Gera um token de autenticação aleatório"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def send_email(to_email, subject, html_content):
    """Envia um e-mail usando SMTP"""
    if not EMAIL_CONFIGURED:
        print("⚠️ Configurações de e-mail não definidas. E-mail não enviado.")
        return False
    
    try:
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Adicionar conteúdo HTML
        msg.attach(MIMEText(html_content, 'html'))
        
        # Conectar ao servidor SMTP
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        # Enviar e-mail
        server.send_message(msg)
        server.quit()
        
        print(f"✅ E-mail enviado com sucesso para {to_email}")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {str(e)}")
        return False

def send_auth_email(user_email, username, auth_token, base_url="http://localhost:3000"):
    """Envia e-mail de autenticação com link para aprovação"""
    subject = "Confirmação de Cadastro - Sistema Educacional"
    
    # URL de autenticação
    auth_url = f"{base_url}/auth/verify?token={auth_token}&username={username}"
    
    # Conteúdo HTML do e-mail
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4a5568; color: white; padding: 10px 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f8f9fa; }}
            .button {{ display: inline-block; background-color: #4a5568; color: white; padding: 10px 20px; 
                      text-decoration: none; border-radius: 4px; margin-top: 20px; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Confirmação de Cadastro</h2>
            </div>
            <div class="content">
                <p>Olá,</p>
                <p>Seu cadastro foi realizado com sucesso no Sistema Educacional. Para confirmar seu acesso, 
                   clique no botão abaixo:</p>
                <p style="text-align: center;">
                    <a href="{auth_url}" class="button">Confirmar Cadastro</a>
                </p>
                <p>Ou copie e cole o seguinte link no seu navegador:</p>
                <p>{auth_url}</p>
                <p>Este link expirará em 24 horas.</p>
                <p>Se você não solicitou este cadastro, por favor ignore este e-mail.</p>
            </div>
            <div class="footer">
                <p>Este é um e-mail automático, por favor não responda.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user_email, subject, html_content)

def send_temp_password_email(user_email, username, temp_password):
    """Envia e-mail com senha temporária"""
    subject = "Sua Senha Temporária - Sistema Educacional"
    
    # Conteúdo HTML do e-mail
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4a5568; color: white; padding: 10px 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f8f9fa; }}
            .password-box {{ background-color: #e2e8f0; padding: 10px; border-radius: 4px; 
                           font-family: monospace; margin: 20px 0; text-align: center; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Sua Senha Temporária</h2>
            </div>
            <div class="content">
                <p>Olá {username},</p>
                <p>Sua conta foi criada no Sistema Educacional. Aqui está sua senha temporária:</p>
                <div class="password-box">
                    <strong>{temp_password}</strong>
                </div>
                <p>Por favor, faça login e altere sua senha o mais rápido possível.</p>
                <p>Esta senha expirará em 24 horas.</p>
            </div>
            <div class="footer">
                <p>Este é um e-mail automático, por favor não responda.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user_email, subject, html_content)