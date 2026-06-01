import streamlit as st
import boto3
import os
import uuid
import time
import re
import pandas as pd
import plotly.express as px
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

BASE_DIR = os.path.dirname(__file__)
caminho_logo = os.path.join(BASE_DIR, 'logo_farmazzini.png')
caminho_mascote = os.path.join(BASE_DIR, 'mascote_farmazzini.png')

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
    layout="centered"
)

try:
    bedrock_runtime = boto3.client(
        'bedrock-agent-runtime',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-2")
    )
except Exception as e:
    st.error(f"⚠️ Erro de conexão com a nuvem. Verifique as configurações: {e}")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": f"{saudacao}! Eu sou o **Vacinini**, o assistente virtual da **Farmazzini**. 💉\n\nEstou pronto para te ajudar a analisar os dados estratégicos de mercado. O que gostaria de consultar hoje?"
        }
    ]

# --- NOVA FUNÇÃO: converte tabela Markdown em DataFrame ---
def markdown_para_dataframe(texto):
    """
    Tenta extrair uma tabela Markdown do texto e converter para DataFrame.
    Retorna None se não encontrar tabela.
    """
    linhas = texto.strip().split('\n')
    linhas_tabela = [l for l in linhas if '|' in l]
    
    if len(linhas_tabela) < 3:
        return None
    
    try:
        # Remove linhas separadoras (---|---)
        linhas_dados = [l for l in linhas_tabela if not re.match(r'^\s*\|[-|\s]+\|\s*$', l)]
        
        # Extrai colunas e dados
        colunas = [c.strip() for c in linhas_dados[0].split('|') if c.strip()]
        dados = []
        for linha in linhas_dados[1:]:
            valores = [v.strip() for v in linha.split('|') if v.strip()]
            if len(valores) == len(colunas):
                dados.append(valores)
        
        if not dados:
            return None
        
        df = pd.DataFrame(dados, columns=colunas)
        
        # Tenta converter colunas numéricas
        for col in df.columns:
            df[col] = df[col].str.replace('R\\$', '').str.replace(',', '.').str.strip()
            try:
                df[col] = pd.to_numeric(df[col])
            except Exception:
                pass
        
        return df
    except Exception:
        return None

# --- NOVA FUNÇÃO: detecta tipo de gráfico ideal e renderiza ---
def renderizar_grafico(df, pergunta):
    """
    Detecta automaticamente o melhor tipo de gráfico baseado nos dados e na pergunta.
    """
    if df is None or df.empty or len(df.columns) < 2:
        return

    colunas_numericas = df.select_dtypes(include='number').columns.tolist()
    colunas_texto = df.select_dtypes(exclude='number').columns.tolist()

    if not colunas_numericas or not colunas_texto:
        return

    col_x = colunas_texto[0]
    col_y = colunas_numericas[0]

    pergunta_lower = pergunta.lower()

    # Gráfico de pizza para comparações de participação
    if any(p in pergunta_lower for p in ['participação', 'proporção', 'percentual', 'distribuição']):
        fig = px.pie(df, names=col_x, values=col_y, title=f"{col_y} por {col_x}")

    # Gráfico de linha para séries temporais
    elif any(p in pergunta_lower for p in ['mês', 'mes', 'evolução', 'histórico', 'tempo', 'dia', 'semana']):
        fig = px.line(df, x=col_x, y=col_y, title=f"{col_y} ao longo do tempo", markers=True)

    # Gráfico de barras para rankings e comparações (padrão)
    else:
        df_sorted = df.sort_values(col_y, ascending=True)
        fig = px.bar(df_sorted, x=col_y, y=col_x, orientation='h',
                     title=f"{col_y} por {col_x}",
                     color=col_y, color_continuous_scale='Blues')

    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# Sidebar
with st.sidebar:
    if img_logo_completa:
        st.image(img_logo_completa, use_container_width=True)
    else:
        st.title("💊 FARMAZZINI")

    st.markdown("---")
    st.markdown("### Sua visão estratégica do mercado farmacêutico")
    st.caption("Central de Inteligência de Dados Farmazzini")
    st.markdown("---")

    if st.button("🔄 Nova Conversa", use_container_width=True, type="secondary"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": f"Histórico limpo! **Vacinini** pronto para uma nova consulta. O que vamos analisar agora?"
            }
        ]
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

st.title("Sua Central de Inteligência Farmazzini")

st.markdown("""
<div style="background-color: #f9f9f9; padding: 15px; border-radius: 10px; border: 1px solid #eee; margin-bottom: 20px;">
    <strong>O que você gostaria de saber? Tente exemplos como:</strong><br>
    - "Qual o preço médio do Omeprazol na farmácia São João?"<br>
    - "Qual o produto mais vendido no histórico de vendas?"<br>
    - "Liste as marcas disponíveis para o medicamento Omeprazol."
</div>
""", unsafe_allow_html=True)

# Renderiza histórico — agora com gráficos salvos
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message("assistant", avatar=caminho_mascote if img_mascote else None):
            st.write(msg["content"])
            # Re-renderiza gráfico se existir no histórico
            if "dataframe" in msg and msg["dataframe"] is not None:
                renderizar_grafico(msg["dataframe"], msg.get("pergunta", ""))
    else:
        with st.chat_message("user"):
            st.write(msg["content"])

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
                        texto_seguro = full_response.replace("R$", "R\\$")
                        response_placeholder.write(texto_seguro + "▌")
                        time.sleep(0.01)

                texto_seguro_final = full_response.replace("R$", "R\\$")
                response_placeholder.write(texto_seguro_final)

                # --- NOVO: tenta gerar gráfico automaticamente ---
                df = markdown_para_dataframe(full_response)
                renderizar_grafico(df, user_prompt)

                # Salva resposta + dataframe no histórico
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": texto_seguro_final,
                    "dataframe": df,
                    "pergunta": user_prompt
                })

            except Exception as e:
                response_placeholder.error("⚠️ O sistema está temporariamente indisponível. Por favor, tente novamente em breve.")