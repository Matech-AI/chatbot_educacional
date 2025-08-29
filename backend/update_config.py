#!/usr/bin/env python3
"""
Script para atualizar automaticamente as configurações do sistema DNA da Força
"""

import os
import socket
import json
import subprocess
from pathlib import Path

def detect_server_ip():
    """
    Detecta automaticamente o IP do servidor
    """
    try:
        # Tenta obter o hostname do servidor
        hostname = socket.gethostname()
        
        # Obtém o IP associado ao hostname
        ip_address = socket.gethostbyname(hostname)
        
        # Se for localhost, tenta obter o IP externo
        if ip_address in ['127.0.0.1', 'localhost']:
            # Tenta conectar a um servidor externo para descobrir o IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                ip_address = s.getsockname()[0]
        
        return ip_address
    except Exception as e:
        print(f"Erro ao detectar IP do servidor: {e}")
        return "0.0.0.0"

def update_env_file(server_ip):
    """
    Atualiza o arquivo .env com o IP correto do servidor
    """
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists() and env_example.exists():
        # Copia o arquivo de exemplo se não existir
        with open(env_example, 'r') as f:
            content = f.read()
        
        # Atualiza as configurações
        content = content.replace("HOSTINGER=false", "HOSTINGER=true")
        content = content.replace("SERVER_IP=0.0.0.0", f"SERVER_IP={server_ip}")
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Arquivo .env criado com IP: {server_ip}")
    elif env_file.exists():
        # Atualiza o arquivo existente
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Atualiza o IP se for diferente
        if f"SERVER_IP={server_ip}" not in content:
            # Substitui qualquer SERVER_IP existente
            import re
            content = re.sub(r'SERVER_IP=.*', f'SERVER_IP={server_ip}', content)
            content = content.replace("HOSTINGER=false", "HOSTINGER=true")
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            print(f"✅ Arquivo .env atualizado com IP: {server_ip}")

def update_vite_config(server_ip):
    """
    Atualiza o vite.config.ts com o IP correto
    """
    vite_config = Path("../vite.config.ts")
    
    if vite_config.exists():
        with open(vite_config, 'r') as f:
            content = f.read()
        
        # Atualiza as configurações do Hostinger
        if f"apiTarget = 'http://{server_ip}:8000'" not in content:
            # Substitui as configurações antigas
            content = content.replace(
                "const serverIP = process.env.SERVER_IP || '0.0.0.0'",
                f"const serverIP = process.env.SERVER_IP || '{server_ip}'"
            )
            
            with open(vite_config, 'w') as f:
                f.write(content)
            
            print(f"✅ vite.config.ts atualizado com IP: {server_ip}")

def test_connectivity(server_ip):
    """
    Testa a conectividade dos serviços
    """
    print(f"\n🔍 Testando conectividade para IP: {server_ip}")
    
    services = {
        "Frontend": 3000,
        "RAG Server": 8000,
        "API Server": 8001
    }
    
    for service_name, port in services.items():
        try:
            # Testa conectividade local
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                print(f"✅ {service_name} (porta {port}): Acessível localmente")
            else:
                print(f"❌ {service_name} (porta {port}): Não acessível localmente")
        except Exception as e:
            print(f"❌ {service_name} (porta {port}): Erro ao testar - {e}")

def main():
    """
    Função principal
    """
    print("🚀 ATUALIZADOR DE CONFIGURAÇÕES - DNA DA FORÇA")
    print("=" * 50)
    
    # Detecta o IP do servidor
    server_ip = detect_server_ip()
    print(f"🌐 IP detectado: {server_ip}")
    
    # Atualiza as configurações
    update_env_file(server_ip)
    update_vite_config(server_ip)
    
    # Testa conectividade
    test_connectivity(server_ip)
    
    print(f"\n🎉 Configurações atualizadas com sucesso!")
    print(f"📍 IP do servidor: {server_ip}")
    print(f"📍 Frontend: http://{server_ip}:3000")
    print(f"📍 RAG Server: http://{server_ip}:8000")
    print(f"📍 API Server: http://{server_ip}:8001")
    
    # Salva o IP em um arquivo para uso posterior
    config_data = {
        "server_ip": server_ip,
        "hostinger": True,
        "ports": {
            "frontend": 3000,
            "rag": 8000,
            "api": 8001
        }
    }
    
    with open("server_config.json", 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print(f"\n💾 Configuração salva em: server_config.json")

if __name__ == "__main__":
    main()
