import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from pathlib import Path

# Após carregar as variáveis de ambiente
load_dotenv()

# Configurações de e-mail
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USER)

# Verificar se as configurações de e-mail estão definidas
EMAIL_CONFIGURED = all([EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD])

# Arquivo para armazenar tokens de autenticação
AUTH_TOKENS_FILE = Path(__file__).parent.parent / "data" / "auth_tokens.json"

# Determinar a URL base com base no ambiente
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
if ENVIRONMENT == "production":
    DEFAULT_BASE_URL = "https://dna-forca-frontend.vercel.app"
else:
    DEFAULT_BASE_URL = "http://localhost:3000"


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
        print(f"⚠️ Configurações de e-mail não definidas. E-mail não enviado.")
        print(f"⚠️ EMAIL_HOST: {EMAIL_HOST}, EMAIL_PORT: {EMAIL_PORT}, EMAIL_USER: {EMAIL_USER}, EMAIL_PASSWORD: {'*' * len(EMAIL_PASSWORD) if EMAIL_PASSWORD else 'vazio'}")
        return False

    try:
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email
        msg['Subject'] = subject

        # Adicionar conteúdo HTML
        msg.attach(MIMEText(html_content, 'html'))

        print(
            f"🔄 Tentando conectar ao servidor SMTP: {EMAIL_HOST}:{EMAIL_PORT}")
        # Conectar ao servidor SMTP
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.set_debuglevel(1)  # Ativar depuração
        print(f"🔄 Iniciando TLS")
        server.starttls()
        print(f"🔄 Tentando login com usuário: {EMAIL_USER}")
        server.login(EMAIL_USER, EMAIL_PASSWORD)

        # Enviar e-mail
        print(f"🔄 Enviando e-mail para: {to_email}")
        server.send_message(msg)
        server.quit()

        print(f"✅ E-mail enviado com sucesso para {to_email}")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {str(e)}")
        print(f"❌ Detalhes do erro: {type(e).__name__}")
        # Adicionar mais detalhes sobre o erro
        import traceback
        print(f"❌ Traceback completo: {traceback.format_exc()}")
        return False


def send_auth_email(user_email, username, auth_token, base_url=None):
    """Envia e-mail de autenticação com link para aprovação"""
    if base_url is None:
        base_url = DEFAULT_BASE_URL
        
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
            .button {{ display: inline-block; background-color: #e53e3e; color: white; padding: 12px 24px; 
                      text-decoration: none; border-radius: 4px; margin-top: 20px; font-weight: bold; }}
            .info-box {{ background-color: #ebf8ff; border-left: 4px solid #3182ce; padding: 15px; margin: 20px 0; }}
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
                <div class="info-box">
                    <p><strong>Informações importantes:</strong></p>
                    <p>Se você foi cadastrado como <strong>aluno</strong>, após confirmar seu cadastro:</p>
                    <ul>
                        <p>1. Você receberá uma senha temporária por email</p>
                        <p>2. Você terá acesso apenas ao chatbot educacional</p>
                        <p>3. Na primeira vez que fizer login, você será direcionado para criar uma nova senha</p>
                    </ul>
                </div>
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
    subject = "Senha Temporária - Sistema Educacional"

    # Conteúdo HTML do e-mail
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4a5568; color: white; padding: 10px 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f8f9fa; }}
            .password-box {{ background-color: #f3f4f6; border: 1px solid #d1d5db; padding: 15px; 
                           text-align: center; font-size: 18px; font-family: monospace; margin: 20px 0; }}
            .info-box {{ background-color: #ebf8ff; border-left: 4px solid #3182ce; padding: 15px; margin: 20px 0; }}
            .warning {{ background-color: #fffaf0; border-left: 4px solid #ed8936; padding: 15px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Senha Temporária</h2>
            </div>
            <div class="content">
                <p>Olá <strong>{username}</strong>,</p>
                <p>Sua senha temporária para acesso ao Sistema Educacional foi gerada com sucesso.</p>
                
                <div class="password-box">
                    {temp_password}
                </div>
                
                <div class="warning">
                    <p><strong>Importante:</strong> Esta é uma senha temporária. Ao fazer login, você será solicitado a alterá-la 
                    para uma senha permanente de sua escolha. Alterar esta senha também ativará sua conta automaticamente.</p>
                </div>
                
                <div class="info-box">
                    <p><strong>Instruções:</strong></p>
                    <ol>
                        <li>Acesse o sistema usando seu nome de usuário e a senha temporária acima</li>
                        <li>Você será solicitado a criar uma nova senha</li>
                        <li>Após alterar sua senha, sua conta será ativada automaticamente</li>
                    </ol>
                </div>
                
                <p>Por razões de segurança, esta senha expirará em 24 horas.</p>
            </div>
            <div class="footer">
                <p>Este é um e-mail automático, por favor não responda.</p>
                <p>Sistema Educacional - DNA da Força</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(user_email, subject, html_content)


def send_password_reset_email(user_email, username, reset_token, base_url=None):
    """Envia e-mail com link para reset de senha"""
    if base_url is None:
        base_url = DEFAULT_BASE_URL
        
    subject = "Redefinição de Senha - Sistema Educacional"

    # URL de reset de senha
    reset_url = f"{base_url}/reset-password?token={reset_token}&username={username}"

    # Conteúdo HTML do e-mail
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4a5568; color: white; padding: 10px 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f8f9fa; }}
            .button {{ display: inline-block; background-color: #e53e3e; color: white; padding: 12px 24px; 
                      text-decoration: none; border-radius: 4px; margin-top: 20px; font-weight: bold; }}
            .info-box {{ background-color: #ebf8ff; border-left: 4px solid #3182ce; padding: 15px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Redefinição de Senha</h2>
            </div>
            <div class="content">
                <p>Olá <strong>{username}</strong>,</p>
                <p>Recebemos uma solicitação para redefinir sua senha no Sistema Educacional.</p>
                <p style="text-align: center;">
                    <a href="{reset_url}" class="button">Redefinir Senha</a>
                </p>
                <p>Ou copie e cole o seguinte link no seu navegador:</p>
                <p>{reset_url}</p>
                <div class="info-box">
                    <p><strong>Informações importantes:</strong></p>
                    <p>Este link expirará em 24 horas.</p>
                    <p>Se você não solicitou esta redefinição de senha, por favor ignore este e-mail.</p>
                </div>
            </div>
            <div class="footer">
                <p>Este é um e-mail automático, por favor não responda.</p>
                <p>Sistema Educacional - DNA da Força</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(user_email, subject, html_content)
