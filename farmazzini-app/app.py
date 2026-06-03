import streamlit as st
import boto3
import os
import uuid
import time
import re
import json
import base64
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

# --- CONFIGURAÇÕES E ASSETS ---
BASE_DIR = os.path.dirname(__file__)
caminho_logo = os.path.join(BASE_DIR, 'logo_farmazzini.png')
caminho_logo_escuro = os.path.join(BASE_DIR, 'logo_farmazzini_dark.png') 
caminho_mascote = os.path.join(BASE_DIR, 'mascote_farmazzini.png')
ARQUIVO_HISTORICO = os.path.join(BASE_DIR, 'historico_pesquisas.json')

try:
    img_logo_completa = Image.open(caminho_logo)
except Exception:
    img_logo_completa = None

try:
    img_logo_escuro = Image.open(caminho_logo_escuro)
except Exception:
    img_logo_escuro = None

try:
    img_mascote = Image.open(caminho_mascote)
except Exception:
    img_mascote = None

hora_atual = datetime.now().hour
if hora_atual < 12:
    saudacao = "Bom dia"
elif hora_atual < 18:
    saudacao = "Boa tarde"
else:
    saudacao = "Boa noite"

st.set_page_config(
    page_title="Central de Inteligência Farmazzini",
    page_icon=img_mascote if img_mascote else "💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa variável de Modo Escuro na Sessão
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# --- TELA DE CARREGAMENTO (SPLASH SCREEN) ---
def renderizar_splash_screen():
    if "splash_mostrada" not in st.session_state:
        img_b64 = ""
        try:
            with open(caminho_mascote, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
        except: pass

        img_html = f'<img src="data:image/png;base64,{img_b64}" width="250" style="margin-bottom: 20px;">' if img_b64 else '<h1>💊 Farmazzini</h1>'

        splash_html = f"""
        <style>
        #splash-screen {{
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background-color: white; z-index: 999999;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            animation: fadeOut 0.5s ease 2.5s forwards;
        }}
        @keyframes fadeOut {{
            to {{ opacity: 0; visibility: hidden; z-index: -1; }}
        }}
        .loading-bar-container {{
            width: 300px; height: 8px; background-color: #f0f0f0; border-radius: 4px; overflow: hidden;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
        }}
        .loading-bar {{
            height: 100%; background-color: #d90429; width: 0%;
            animation: loadProgress 2s ease-in-out forwards;
        }}
        @keyframes loadProgress {{
            0% {{ width: 0%; }}
            50% {{ width: 70%; }}
            100% {{ width: 100%; }}
        }}
        [data-testid="stAppViewBlockContainer"] {{ animation: delayShow 2.5s; }}
        @keyframes delayShow {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        </style>
        <div id="splash-screen">
            {img_html}
            <div style="font-family: sans-serif; color: #555; margin-bottom: 15px; font-weight: bold; letter-spacing: 1px;">
                INICIALIZANDO CENTRAL DE INTELIGÊNCIA...
            </div>
            <div class="loading-bar-container"><div class="loading-bar"></div></div>
        </div>
        """
        st.markdown(splash_html, unsafe_allow_html=True)
        st.session_state.splash_mostrada = True

renderizar_splash_screen()

# --- CSS CUSTOMIZADO (BASE + MODO ESCURO DINÂMICO) ---
estilo_base = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Botões Padrão da Sidebar (Histórico) */
    [data-testid="stSidebar"] .stButton>button[kind="secondary"] {
        width: 100%; border-radius: 8px; text-align: left; border: 1px solid transparent;
        background-color: transparent; color: inherit; padding: 10px 15px;
        justify-content: flex-start; transition: all 0.2s ease-in-out;
    }
    [data-testid="stSidebar"] .stButton>button[kind="secondary"]:hover {
        border: 1px solid #d90429; color: #d90429;
    }
    
    /* Botão Destaque: NOVA CONVERSA */
    [data-testid="stSidebar"] button[kind="primary"] {
        background-color: #d90429 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        padding: 12px 20px !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: #b00322 !important;
        box-shadow: 0 4px 8px rgba(217, 4, 41, 0.3) !important;
    }
    
    /* Estilo da "Pasta" do Expander */
    [data-testid="stExpander"] {
        border: none !important;
        background-color: transparent !important;
    }
    [data-testid="stExpander"] summary {
        padding-left: 0 !important;
    }
    [data-testid="stExpander"] summary p {
        font-weight: bold;
        font-size: 16px;
    }
    
    .highlight-box {
        background-color: #f8f9fa; padding: 20px; border-radius: 12px;
        border-left: 5px solid #d90429; margin-bottom: 25px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); color: black;
    }
    </style>
"""

estilo_escuro = """
    <style>
    /* Sobrescrita para Modo Escuro */
    .stApp { background-color: #121212; color: #ffffff; }
    [data-testid="stHeader"] { background-color: transparent; }
    [data-testid="stSidebar"] { background-color: #1e1e1e; }
    
    .highlight-box {
        background-color: #2b2b2b !important; 
        color: #ffffff !important; 
        border-left: 5px solid #d90429 !important;
    }
    
    /* CORREÇÃO DA BARRA DE DIGITAÇÃO */
    [data-testid="stBottomBlockContainer"] { background-color: #121212 !important; }
    [data-testid="stChatInput"] { background-color: #121212 !important; }
    
    [data-testid="stChatInput"] > div { background-color: #2b2b2b !important; border: 1px solid #555 !important; }
    [data-testid="stChatInput"] div { background-color: transparent !important; color: white !important; }
    
    [data-testid="stChatInput"] textarea { background-color: transparent !important; color: white !important; }
    [data-testid="stChatInput"] textarea::placeholder { color: #aaaaaa !important; }
    
    [data-testid="stChatInput"] button { background-color: transparent !important; }
    [data-testid="stChatInput"] svg { fill: white !important; }
    
    /* Força o título da "Pasta" Abas Recentes e o ícone a ficarem brancos */
    [data-testid="stExpander"] summary p, 
    [data-testid="stExpander"] summary span, 
    [data-testid="stExpander"] svg {
        color: #ffffff !important;
    }
    
    /* Textos Gerais */
    h1, h2, h3, h4, h5, h6, p, span { color: #ffffff; }
    </style>
"""

# Aplica o CSS Base e, se o toggle estiver ativo, aplica o CSS Escuro por cima
st.markdown(estilo_base, unsafe_allow_html=True)
if st.session_state.dark_mode:
    st.markdown(estilo_escuro, unsafe_allow_html=True)

# --- FUNÇÕES DE HISTÓRICO COM MEMÓRIA COMPLETA (SESSÕES) ---
def serializar_mensagens(mensagens):
    msgs_salvas = []
    for m in mensagens:
        nova_m = {"role": m["role"], "content": m["content"]}
        if "pergunta" in m: nova_m["pergunta"] = m["pergunta"]
        if "dataframe" in m and m["dataframe"] is not None:
            nova_m["dataframe"] = m["dataframe"].fillna("").to_dict(orient="records")
        msgs_salvas.append(nova_m)
    return msgs_salvas

def desserializar_mensagens(mensagens_salvas):
    msgs = []
    for m in mensagens_salvas:
        nova_m = {"role": m["role"], "content": m["content"]}
        if "pergunta" in m: nova_m["pergunta"] = m["pergunta"]
        if "dataframe" in m and m["dataframe"]:
            nova_m["dataframe"] = pd.DataFrame(m["dataframe"])
        msgs.append(nova_m)
    return msgs

def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO): return []
    try:
        with open(ARQUIVO_HISTORICO, 'r', encoding='utf-8') as f:
            historico = json.load(f)
        limite_data = datetime.now() - timedelta(days=30)
        return [sessao for sessao in historico if datetime.fromisoformat(sessao['data']) >= limite_data]
    except: return []

def salvar_sessao(session_id, mensagens):
    if len(mensagens) <= 1: return 
    
    titulo = "Nova Conversa"
    for m in mensagens:
        if m["role"] == "user":
            titulo = m["content"]
            break

    historico = carregar_historico()
    historico = [h for h in historico if h.get("session_id") != session_id]
    
    nova_sessao = {
        "session_id": session_id,
        "titulo": titulo,
        "data": datetime.now().isoformat(),
        "messages": serializar_mensagens(mensagens)
    }
    historico.insert(0, nova_sessao)
    
    with open(ARQUIVO_HISTORICO, 'w', encoding='utf-8') as f:
        json.dump(historico[:50], f, ensure_ascii=False, indent=4)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"{saudacao}! Eu sou o **Vacinini**, o assistente virtual da **Farmazzini**. 💉\n\nEstou pronto para te ajudar a analisar os dados estratégicos de mercado. O que gostaria de consultar hoje?"}
    ]

# --- CONEXÃO AWS BEDROCK ---
try:
    bedrock_runtime = boto3.client(
        'bedrock-agent-runtime',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-2")
    )
except Exception as e:
    st.error(f"⚠️ Erro de conexão com a nuvem: {e}")

# --- FUNÇÕES DE DADOS E GRÁFICOS ---
def markdown_para_dataframe(texto):
    linhas = texto.strip().split('\n')
    linhas_tabela = [l for l in linhas if '|' in l]
    if len(linhas_tabela) < 3: return None
    try:
        linhas_dados = [l for l in linhas_tabela if not re.match(r'^\s*\|[-|\s]+\|\s*$', l)]
        colunas = [c.strip() for c in linhas_dados[0].split('|') if c.strip()]
        dados = [[v.strip() for v in l.split('|') if v.strip()] for l in linhas_dados[1:] if len([v.strip() for v in l.split('|') if v.strip()]) == len(colunas)]
        if not dados: return None
        df = pd.DataFrame(dados, columns=colunas)
        for col in df.columns:
            df[col] = df[col].str.replace('R\\$', '').str.replace(',', '.').str.strip()
            try: df[col] = pd.to_numeric(df[col])
            except: pass
        return df
    except: return None

def renderizar_grafico(df, pergunta):
    if df is None or df.empty or len(df.columns) < 2: return
    colunas_num = df.select_dtypes(include='number').columns.tolist()
    colunas_txt = df.select_dtypes(exclude='number').columns.tolist()
    if not colunas_num or not colunas_txt: return
    col_x, col_y = colunas_txt[0], colunas_num[0]
    p_lower = pergunta.lower()

    if any(p in p_lower for p in ['participação', 'proporção']):
        fig = px.pie(df, names=col_x, values=col_y, title=f"Análise de {col_y}")
    elif any(p in p_lower for p in ['mês', 'evolução', 'tempo']):
        fig = px.line(df, x=col_x, y=col_y, title=f"Evolução de {col_y}", markers=True)
    else:
        fig = px.bar(df.sort_values(col_y, ascending=True), x=col_y, y=col_x, orientation='h', title=f"Comparativo: {col_y} por {col_x}", color=col_y, color_continuous_scale='Reds')

    # Ajuste de cores dinâmico para os gráficos do Plotly
    cor_texto = "white" if st.session_state.dark_mode else "black"
    
    fig.update_layout(
        showlegend=False, 
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='rgba(0,0,0,0)', 
        font_color=cor_texto,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

# --- SIDEBAR (BARRA LATERAL) ---
with st.sidebar:
    if st.session_state.dark_mode and img_logo_escuro:
        st.image(img_logo_escuro, use_container_width=True)
    elif img_logo_completa:
        st.image(img_logo_completa, use_container_width=True)
    else:
        st.title("💊 FARMAZZINI")
    
    st.markdown("<br>", unsafe_allow_html=True)
    novo_modo = st.toggle("🌙 Modo Escuro", value=st.session_state.dark_mode)
    if novo_modo != st.session_state.dark_mode:
        st.session_state.dark_mode = novo_modo
        st.rerun() 
    st.markdown("---")
    
    # Botão com 'type="primary"' para aplicar o destaque no CSS
    if st.button("➕ Nova Conversa", use_container_width=True, type="primary"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = [{"role": "assistant", "content": f"Histórico limpo! **Vacinini** pronto para uma nova consulta."}]
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Criando a "Pasta" de Abas Recentes usando Expander
    with st.expander("📂 Abas Recentes", expanded=True):
        historico_atual = carregar_historico()
        if not historico_atual:
            st.caption("Nenhuma pesquisa recente.")
        else:
            for sessao in historico_atual:
                titulo_sessao = sessao.get('titulo', sessao.get('pergunta', 'Sessão Antiga'))
                texto_botao = titulo_sessao if len(titulo_sessao) < 28 else titulo_sessao[:25] + "..."
                chave_botao = sessao.get('data', str(uuid.uuid4()))
                
                # 'kind="secondary"' é o padrão, que pega o estilo hover vermelho que definimos
                if st.button(f"💬 {texto_botao}", key=chave_botao):
                    st.session_state.session_id = sessao.get('session_id', str(uuid.uuid4()))
                    
                    if 'messages' in sessao:
                        st.session_state.messages = desserializar_mensagens(sessao['messages'])
                    else:
                        st.session_state.messages = [
                            {"role": "assistant", "content": "A recuperar formato de pesquisa antiga..."},
                            {"role": "user", "content": titulo_sessao}
                        ]
                    st.rerun()

# --- CORPO PRINCIPAL ---
col1, col2 = st.columns([4, 1])
with col1:
    st.title("Sua Central de Inteligência")
    st.markdown("""
    <div class="highlight-box">
        <strong>💡 Dicas de análise:</strong><br>
        • <i>"Qual o preço médio do Omeprazol na Vera Cruz?"</i><br>
        • <i>"Me mostre um comparativo de preços dos remédios mais vendidos."</i><br>
    </div>
    """, unsafe_allow_html=True)
with col2:
    if img_mascote: st.image(img_mascote, width=200)

# Renderiza histórico de chat
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message("assistant", avatar=caminho_mascote if img_mascote else "💊"):
            st.write(msg["content"])
            if "dataframe" in msg and msg["dataframe"] is not None:
                renderizar_grafico(msg["dataframe"], msg.get("pergunta", ""))
    else:
        with st.chat_message("user"):
            st.write(msg["content"])

# Lógica de Input 
if user_prompt := st.chat_input("Digite sua dúvida estratégica aqui..."):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"): st.write(user_prompt)

    with st.chat_message("assistant", avatar=caminho_mascote if img_mascote else "💊"):
        response_placeholder = st.empty()
        with st.spinner("Vacinini cruzando dados no Data Lake..."):
            try:
                response = bedrock_runtime.invoke_agent(
                    agentId=os.getenv("BEDROCK_AGENT_ID"),
                    agentAliasId=os.getenv("BEDROCK_AGENT_ALIAS_ID"),
                    sessionId=st.session_state.session_id,
                    inputText=user_prompt
                )

                full_response = ""
                for event in response.get('completion', []):
                    if 'chunk' in event:
                        full_response += event['chunk']['bytes'].decode('utf-8')
                        response_placeholder.write(full_response.replace("R$", "R\\$") + "▌")
                        time.sleep(0.01)

                texto_final = full_response.replace("R$", "R\\$")
                response_placeholder.write(texto_final)
                
                df = markdown_para_dataframe(full_response)
                renderizar_grafico(df, user_prompt)

                st.session_state.messages.append({
                    "role": "assistant", "content": texto_final, 
                    "dataframe": df, "pergunta": user_prompt
                })
                
                salvar_sessao(st.session_state.session_id, st.session_state.messages)

            except Exception as e:
                response_placeholder.error("⚠️ O sistema está temporariamente indisponível.")