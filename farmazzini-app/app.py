import streamlit as st
import boto3
import os
import uuid
import time
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image

# 1. Carrega as variáveis de ambiente com segurança
load_dotenv()

# --- CORREÇÃO DE CAMINHO PARA A NUVEM ---
# Descobre automaticamente o caminho da pasta onde este arquivo app.py está guardado
BASE_DIR = os.path.dirname(__file__)
caminho_logo = os.path.join(BASE_DIR, 'logo_farmazzini.png')
caminho_mascote = os.path.join(BASE_DIR, 'mascote_farmazzini.png')

# Pre-carregamento das imagens usando os caminhos corrigidos
try:
    img_logo_completa = Image.open(caminho_logo)
    img_mascote = Image.open(caminho_mascote)
except Exception:
    img_logo_completa = None
    img_mascote = None

# --- UX: SAUDAÇÃO DINÂMICA DO VACININI ---
hora_atual = datetime.now().hour
if hora_atual < 12:
    saudacao = "Bom dia"
elif hora_atual < 18:
    saudacao = "Boa tarde"
else:
    saudacao = "Boa noite"

# 2. Configuração da Aba do Navegador
st.set_page_config(
    page_title="Central de Inteligência Farmazzini",
    page_icon=img_mascote if img_mascote else "💊",
    layout="centered"
)

# 3. Inicializa o cliente do Bedrock Agent Runtime
try:
    bedrock_runtime = boto3.client(
        'bedrock-agent-runtime',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-2")
    )
except Exception as e:
    st.error(f"⚠️ Erro de conexão com a nuvem. Verifique as configurações: {e}")

# 4. Gerenciamento de Sessão e Histórico (Contexto)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# --- UX: APRESENTAÇÃO PERSONALIZADA DO VACININI ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": f"{saudacao}! Eu sou o **Vacinini**, o assistente virtual da **Farmazzini**. 💉\n\nEstou pronto para te ajudar a analisar os dados estratégicos de mercado. O que gostaria de consultar hoje?"
        }
    ]

# 5. Interface da Barra Lateral Personalizada (Sidebar UI)
with st.sidebar:
    if img_logo_completa:
        st.image(img_logo_completa, use_container_width=True)
    else:
        st.title("💊 FARMAZZINI")
    
    st.markdown("---")
    st.markdown("### Sua visão estratégica do mercado farmacêutico")
    st.caption("Central de Inteligência de Dados Farmazzini")
    st.markdown("---")
    
    # Botão de Nova Conversa
    if st.button("🔄 Nova Conversa", use_container_width=True, type="secondary"):
        st.session_state.messages = [
            {
                "role": "assistant", 
                "content": f"Histórico limpo! **Vacinini** pronto para uma nova consulta. O que vamos analisar agora?"
            }
        ]
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

# 6. Interface Principal de Chat (Chat UX)
st.title("Sua Central de Inteligência Farmazzini")

# --- UX: SUBSTITUIÇÃO DOS EXEMPLOS OPERACIONAIS ---
st.markdown("""
<div style="background-color: #f9f9f9; padding: 15px; border-radius: 10px; border: 1px solid #eee; margin-bottom: 20px;">
    <strong>O que você gostaria de saber? Tente exemplos como:</strong><br>
    - "Qual o preço médio do Omeprazol na farmácia São João?"<br>
    - "Qual o produto mais vendido no histórico de vendas ontem?"<br>
    - "Liste as marcas disponíveis para o medicamento Omeprazol."
</div>
""", unsafe_allow_html=True)

# Mostra as mensagens anteriores na tela usando o mascote corrigido
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message("assistant", avatar=caminho_mascote if img_mascote else None):
            st.write(msg["content"])
    else:
        with st.chat_message("user"):
            st.write(msg["content"])

# 7. Caixa de entrada do usuário (Chat Input)
if user_prompt := st.chat_input("Digite sua dúvida estratégica aqui..."):
    
    with st.chat_message("user"):
        st.write(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    
    with st.chat_message("assistant", avatar=caminho_mascote if img_mascote else None):
        response_placeholder = st.empty()
        
        with st.spinner("Vacinini analisando dados estratégicos..."):
            try:
                response = bedrock_runtime.invoke_agent(
                    agentId=os.getenv("BEDROCK_AGENT_ID"),
                    agentAliasId=os.getenv("BEDROCK_AGENT_ALIAS_ID"),
                    sessionId=st.session_state.session_id,
                    inputText=user_prompt
                )
                
                full_response = ""
                completion_stream = response.get('completion', [])
                
                for event in completion_stream:
                    if 'chunk' in event:
                        chunk_bytes = event['chunk']['bytes']
                        full_response += chunk_bytes.decode('utf-8')
                        response_placeholder.write(full_response + "▌")
                        time.sleep(0.01)
                
                response_placeholder.write(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                response_placeholder.error(f"⚠️ O sistema está temporariamente indisponível. Por favor, tente novamente em breve.")