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

load_dotenv()

# --- CONFIGURAÇÕES E ASSETS ---
BASE_DIR = os.path.dirname(__file__)
caminho_logo = os.path.join(BASE_DIR, 'logo_farmazzini.png')
caminho_logo_escuro = os.path.join(BASE_DIR, 'logo_farmazzini_dark.png') 
caminho_mascote = os.path.join(BASE_DIR, 'mascote_farmazzini.png')
caminho_avatar_usuario = os.path.join(BASE_DIR, 'avatar_usuario.png') 
ARQUIVO_HISTORICO = os.path.join(BASE_DIR, 'historico_pesquisas.json') # <-- A linha que eu tinha apagado sem querer!

# Função auxiliar para converter imagens em Base64 (remove o hover do Streamlit)
def get_image_b64(caminho):
    if os.path.exists(caminho):
        try:
            with open(caminho, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except:
            return None
    return None

logo_b64 = get_image_b64(caminho_logo)
logo_escuro_b64 = get_image_b64(caminho_logo_escuro)
mascote_b64 = get_image_b64(caminho_mascote)
avatar_usuario_b64 = get_image_b64(caminho_avatar_usuario)

hora_atual = datetime.now().hour
if hora_atual < 12:
    saudacao = "Bom dia"
elif hora_atual < 18:
    saudacao = "Boa tarde"
else:
    saudacao = "Boa noite"

st.set_page_config(
    page_title="Central de Inteligência Farmazzini",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa variáveis de Sessão
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "confirmar_delete" not in st.session_state:
    st.session_state.confirmar_delete = None

# --- TELA DE CARREGAMENTO (SPLASH SCREEN) ---
def renderizar_splash_screen():
    if "splash_mostrada" not in st.session_state:
        img_html = f'<img src="data:image/png;base64,{mascote_b64}" width="250" style="margin-bottom: 20px;">' if mascote_b64 else '<h1>💊 Farmazzini</h1>'

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
        </style