import streamlit as st
import boto3
import os
import uuid
import time
import re
import json
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

# --- CONFIGURAÇÕES E ASSETS ---
BASE_DIR = os.path.dirname(__file__)
caminho_logo = os.path.join(BASE_DIR, 'logo_farmazzini.png')
caminho_mascote = os.path.join(BASE_DIR, 'mascote_farmazzini.png')
ARQUIVO_HISTORICO = os.path.join(BASE_DIR, 'historico_pesquisas.json')

try:
    img_logo_completa = Image.open(caminho_logo)
    img_mascote = Image.open(caminho_mascote)
except Exception:
    img_logo_completa = None
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
    layout="wide", # Alterado para 'wide' para aproveitar melhor o ecrã com os gráficos
    initial_sidebar_state="expanded"
)

# --- CSS CUSTOMIZADO (DESIGN PROFISSIONAL) ---
st.markdown("""
    <style>
    /* Ocultar elementos padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Estilizar botões da barra lateral (estilo abas do Gemini) */
    [data-testid="stSidebar"] .stButton>button {
        width: 100%;
        border-radius: 8px;
        text-align: left;
        border: 1px solid transparent;
        background-color: transparent;
        color: #333;
        padding: 10px 15px;
        justify-content: flex-start;
        transition: all 0.2s ease-in-out;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background-color: #f0f2f6;
        border: 1px solid #e0e0e0;
        color: #004b23; /* Verde escuro profissional */
    }
    
    /* Caixa de destaque principal */
    .highlight-box {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #004b23;
        margin-bottom: 25px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE HISTÓRICO (30 DIAS) ---
def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO):
        return []
    try:
        with open(ARQUIVO_HISTORICO, 'r', encoding='utf-8') as f:
            historico = json.load(f)
            
        # Filtrar apenas os últimos 30 dias
        limite_data = datetime.now() - timedelta(days=30)
        historico_filtrado = []
        for item in historico:
            data_item = datetime.fromisoformat(item['data'])
            if data_item >= limite_data:
                historico_filtrado.append(item)
                
        return historico_filtrado
    except Exception:
        return []

def salvar_historico(pergunta):
    historico = carregar_historico()
    # Evitar duplicados seguidos
    if not historico or historico[0]['pergunta'] != pergunta:
        novo_item = {
            "pergunta": pergunta,
            "data": datetime.now().isoformat()
        }
        historico.insert(0, novo_item) # Adiciona no topo
        
        with open(ARQUIVO_HISTORICO, 'w', encoding='utf-8') as f:
            json.dump(historico[:50], f, ensure_ascii=False, indent=4) # Guarda o top 50
    return historico

# Inicializa variáveis de sessão
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": f"{saudacao}! Eu sou o **Vacinini**, o assistente virtual da **Farmazzini**. 💉\n\nEstou pronto para te ajudar a analisar os dados estratégicos de mercado. O que gostaria de consultar hoje?"
        }
    ]

if "pesquisa_acionada" not in st.session_state:
    st.session_state.pesquisa_acionada = None

# --- CONEXÃO AWS BEDROCK ---
try:
    bedrock_runtime = boto3.client(
        'bedrock-agent-runtime',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-2")
    )
except Exception as e:
    st.error(f"⚠️ Erro de conexão com a nuvem. Verifique as configurações: {e}")


# --- FUNÇÃO: converte tabela Markdown em DataFrame ---
def markdown_para_dataframe(texto):
    linhas = texto.strip().split('\n')
    linhas_tabela = [l for l in linhas if '|' in l]
    
    if len(linhas_tabela) < 3:
        return None
    
    try:
        linhas_dados = [l for l in linhas_tabela if not re.match(r'^\s*\|[-|\s]+\|\s*$', l)]
        colunas = [c.strip() for c in linhas_dados[0].split('|') if c.strip()]
        dados = []
        for linha in linhas_dados[1:]:
            valores = [v.strip() for v in linha.split('|') if v.strip()]
            if len(valores) == len(colunas):
                dados.append(valores)
        
        if not dados:
            return None
        
        df = pd.DataFrame(dados, columns=colunas)
        
        for col in df.columns:
            df[col] = df[col].str.replace('R\\$', '').str.replace(',', '.').str.strip()
            try:
                df[col] = pd.to_numeric(df[col])
            except Exception:
                pass
        return df
    except Exception:
        return None

# --- FUNÇÃO: detecta tipo de gráfico ideal e renderiza ---
def renderizar_grafico(df, pergunta):
    if df is None or df.empty or len(df.columns) < 2:
        return

    colunas_numericas = df.select_dtypes(include='number').columns.tolist()
    colunas_texto = df.select_dtypes(exclude='number').columns.tolist()

    if not colunas_numericas or not colunas_texto:
        return

    col_x = colunas_texto[0]
    col_y = colunas_numericas[0]
    pergunta_lower = pergunta.lower()

    if any(p in pergunta_lower for p in ['participação', 'proporção', 'percentual', 'distribuição']):
        fig = px.pie(df, names=col_x, values=col_y, title=f"Análise de {col_y}")
    elif any(p in pergunta_lower for p in ['mês', 'mes', 'evolução', 'histórico', 'tempo', 'dia', 'semana']):
        fig = px.line(df, x=col_x, y=col_y, title=f"Evolução de {col_y}", markers=True)
    else:
        df_sorted = df.sort_values(col_y, ascending=True)
        fig = px.bar(df_sorted, x=col_y, y=col_x, orientation='h',
                     title=f"Comparativo: {col_y} por {col_x}",
                     color=col_y, color_continuous_scale='Greens') # Trocado para verde para combinar com farmácia

    fig.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

# --- SIDEBAR (BARRA LATERAL) ---
with st.sidebar:
    if img_logo_completa:
        st.image(img_logo_completa, use_container_width=True)
    else:
        st.title("💊 FARMAZZINI")

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("➕ Nova Conversa", use_container_width=True, type="primary"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": f"Histórico limpo! **Vacinini** pronto para uma nova consulta. O que vamos analisar agora?"
            }
        ]
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    st.markdown("---")
    st.markdown("### 🕒 Recentes (30 dias)")
    
    # Carregar e exibir histórico
    historico_atual = carregar_historico()
    if not historico_atual:
        st.caption("Nenhuma pesquisa recente.")
    else:
        for item in historico_atual:
            # Encurtar texto muito longo para o botão
            texto_botao = item['pergunta'] if len(item['pergunta']) < 28 else item['pergunta'][:25] + "..."
            if st.button(f"💬 {texto_botao}", key=item['data']):
                st.session_state.pesquisa_acionada = item['pergunta']

# --- CORPO PRINCIPAL ---
st.title("Sua Central de Inteligência")

# Caixa de destaque profissional
st.markdown("""
<div class="highlight-box">
    <strong>💡 Dicas de análise:</strong><br>
    • <i>"Qual o preço médio do Omeprazol na Vera Cruz?"</i><br>
    • <i>"Me mostre um comparativo de preços dos remédios mais vendidos."</i><br>
</div>
""", unsafe_allow_html=True)

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

# Lógica de Input (aceita tanto o input manual quanto o clique no histórico)
user_prompt = st.chat_input("Digite sua dúvida estratégica aqui...")

# Se o utilizador clicou na sidebar, usa essa pesquisa
if st.session_state.pesquisa_acionada:
    user_prompt = st.session_state.pesquisa_acionada
    st.session_state.pesquisa_acionada = None # Limpa o gatilho

if user_prompt:
    # Salva no histórico de 30 dias
    salvar_historico(user_prompt)

    with st.chat_message("user"):
        st.write(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

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
                completion_stream = response.get('completion', [])

                for event in completion_stream:
                    if 'chunk' in event:
                        chunk_bytes = event['chunk']['bytes']
                        full_response += chunk_bytes.decode('utf-8')
                        texto_seguro = full_response.replace("R$", "R\\$")
                        response_placeholder.write(texto_seguro + "▌")
                        time.sleep(0.01)

                texto_seguro_final = full_response.replace("R$", "R\\$")
                response_placeholder.write(texto_seguro_final)

                df = markdown_para_dataframe(full_response)
                renderizar_grafico(df, user_prompt)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": texto_seguro_final,
                    "dataframe": df,
                    "pergunta": user_prompt
                })

            except Exception as e:
                response_placeholder.error("⚠️ O sistema está temporariamente indisponível. Por favor, verifique sua conexão ou tente novamente em breve.")