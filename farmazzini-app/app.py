import streamlit as st
import boto3
import os
import uuid
import time
from dotenv import load_dotenv
from PIL import Image

# 1. Carrega as variáveis de ambiente com segurança
load_dotenv()

# Pre-carregamento das imagens para evitar erros
try:
    img_logo_completa = Image.open('logo_farmazzini.png') # Texto + Ícone
    img_mascote = Image.open('mascote_farmazzini.png')   # Apenas a Vacina Circular
except Exception:
    img_logo_completa = None
    img_mascote = None

# 2. Configuração Exclusiva de UI/UX (Aba do Navegador)
# --- UX: Usamos o mascote (vacina) para o ícone da aba, é mais limpo ---
st.set_page_config(
    page_title="Central de Inteligência Farmazzini",
    page_icon=img_mascote if img_mascote else "💊",
    layout="centered"
)

# 3. Inicializa o cliente do Bedrock Agent Runtime
try:
    # --- UI: Mantemos o spinner com o termo não técnico ---
    with st.spinner("Conectando à Central de Inteligência..."):
        bedrock_runtime = boto3.client(
            'bedrock-agent-runtime',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-2")
        )
except Exception as e:
    st.error(f"⚠️ Erro de conexão com a nuvem. Verifique o arquivo .env: {e}")

# 4. Gerenciamento de Sessão e Histórico (Contexto)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Mensagem inicial personalizada e mais amigável
if "messages" not in st.session_state:
    # --- UX: O mascote (assistant) já aparece aqui com a mensagem inicial ---
    st.session_state.messages = [
        {"role": "assistant", "content": "Olá! Sou a sua **Central de Inteligência Farmazzini**. Como posso te ajudar a analisar os dados de mercado hoje?"}
    ]

# 5. Interface da Barra Lateral Personalizada (Sidebar UI)
with st.sidebar:
    # --- UI: Insere a logo COMPLETA (texto + ícone) no topo ---
    if img_logo_completa:
        st.image(img_logo_completa, use_container_width=True)
    else:
        st.title("💊 FARMAZZINI")
    
    st.markdown("---")
    # --- UI/UX: Texto institucional simples, sem termos técnicos ---
    st.markdown("### Sua visão estratégica do mercado farmacêutico")
    st.caption("Central de Inteligência de Dados Farmazzini")
    
    st.markdown("---")
    
    # Botão de Nova Conversa (UX: Limpar contexto rápido)
    if st.button("🔄 Nova Conversa", use_container_width=True, type="secondary"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Histórico limpo! Como posso te ajudar agora?"}
        ]
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

# 6. Interface Principal de Chat (Chat UX)
st.title("Sua Central de Inteligência Farmazzini")

# --- UX: Bloco de exemplos de perguntas clean ---
st.markdown("""
<div style="background-color: #f9f9f9; padding: 15px; border-radius: 10px; border: 1px solid #eee; margin-bottom: 20px;">
    <strong>O que você gostaria de saber? Tente exemplos como:</strong><br>
    - "Qual o preço da Tadalafila na farmácia São João?"<br>
    - "Qual o produto mais vendido no histórico de vendas de ontem?"<br>
    - "Liste 5 produtos que temos na base do mercado."
</div>
""", unsafe_allow_html=True)

# Mostra as mensagens anteriores na tela
# --- UX MESTRE: Renderizamos as mensagens do assistente usando o mascote (vacina circular) como avatar ---
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        # Usamos o mascote específico como avatar para o assistente
        with st.chat_message("assistant", avatar="mascote_farmazzini.png" if img_mascote else None):
            st.write(msg["content"])
    else:
        # Usuário mantém o ícone padrão
        with st.chat_message("user"):
            st.write(msg["content"])

# 7. Caixa de entrada do usuário (Chat Input)
if user_prompt := st.chat_input("Digite sua dúvida estratégica aqui..."):
    
    # Exibe a pergunta do usuário
    with st.chat_message("user"):
        st.write(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    
    # Exibe a resposta da IA usando o mascote
    # --- UX: A resposta que está sendo gerada também usa o mascote ---
    with st.chat_message("assistant", avatar="mascote_farmazzini.png" if img_mascote else None):
        # Placeholder para o efeito de streaming
        response_placeholder = st.empty()
        
        # UX: Spinner amigável
        with st.spinner("Analisando dados estratégicos..."):
            try:
                # Invocação do Agente AWS
                response = bedrock_runtime.invoke_agent(
                    agentId=os.getenv("BEDROCK_AGENT_ID"),
                    agentAliasId=os.getenv("BEDROCK_AGENT_ALIAS_ID"),
                    sessionId=st.session_state.session_id,
                    inputText=user_prompt
                )
                
                # Coleta a resposta bruta
                full_response = ""
                completion_stream = response.get('completion', [])
                
                # UX MESTRE: Efeito de streaming (digitação)
                for event in completion_stream:
                    if 'chunk' in event:
                        chunk_bytes = event['chunk']['bytes']
                        full_response += chunk_bytes.decode('utf-8')
                        # Atualiza o placeholder a cada chunk (efeito visual ótimo)
                        response_placeholder.write(full_response + "▌")
                        # Pequeno delay para simular a digitação (opcional)
                        time.sleep(0.01)
                
                # Mostra a resposta final sem o cursor
                response_placeholder.write(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                # UX: Tratamento de erro elegante
                response_placeholder.error(f"⚠️ O sistema está temporariamente indisponível. Por favor, tente novamente em breve.")