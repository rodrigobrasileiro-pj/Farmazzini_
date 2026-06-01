import streamlit as st
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA (Deve ser sempre a primeira linha do Streamlit)
st.set_page_config(
    page_title="Farmazzini | Central de Preços",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CSS CUSTOMIZADO (Design Profissional)
st.markdown("""
    <style>
    /* Ocultar menu padrão e rodapé do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Arredondar botões da barra lateral para parecerem abas */
    div[data-testid="stSidebarNav"] {display: none;}
    .stButton>button {
        border-radius: 10px;
        text-align: left;
        border: none;
        background-color: transparent;
    }
    .stButton>button:hover {
        background-color: #e0e0e0;
        color: #004b23;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. INICIALIZAÇÃO DO HISTÓRICO (Mock de dados para visualizar o design)
if 'historico_pesquisas' not in st.session_state:
    st.session_state.historico_pesquisas = [
        {"termo": "Dipirona Monoidratada 500mg", "data": "30/05/2026"},
        {"termo": "Vitamina C efervescente", "data": "28/05/2026"},
        {"termo": "Ibuprofeno 400mg", "data": "25/05/2026"}
    ]

# 4. BARRA LATERAL (SIDEBAR)
with st.sidebar:
    # Usando o teu logo existente
    try:
        st.image("logo_farmazzini.png", use_column_width=True)
    except:
        st.title("💊 Farmazzini")
        
    st.markdown("---")
    st.write("🕒 **Pesquisas Recentes**")
    
    # Criar um botão para cada item do histórico
    for pesquisa in st.session_state.historico_pesquisas:
        # Se o utilizador clicar, preenchemos a barra de pesquisa principal
        if st.button(f"🔍 {pesquisa['termo']}", key=pesquisa['termo'], use_container_width=True):
            st.session_state.pesquisa_atual = pesquisa['termo']

# 5. CORPO PRINCIPAL DA APLICAÇÃO
col1, col2 = st.columns([3, 1])

with col1:
    st.title("Busca de Medicamentos")
    st.markdown("Compare preços entre a **Vera Cruz** e outras redes de forma inteligente.")
    
    # Barra de pesquisa
    termo_busca = st.text_input(
        "O que procuras hoje?", 
        value=st.session_state.get('pesquisa_atual', ''),
        placeholder="Ex: Neosaldina, Roacutan..."
    )

with col2:
    # Exibir o mascote no canto superior direito para dar personalidade
    try:
        st.image("mascote_farmazzini.png", width=150)
    except:
        pass

st.markdown("---")

# 6. DEMONSTRAÇÃO DE MÉTRICAS (Design de Dashboard)
if termo_busca:
    st.subheader(f"Resultados para: {termo_busca}")
    
    # Exemplo de Cards de Informação Profissionais
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    
    with metric_col1:
        st.metric(label="🏆 Melhor Preço Encontrado", value="R$ 12,90", delta="-R$ 2,50 (Drogaria SP)")
    with metric_col2:
        st.metric(label="🏪 Farmácias Analisadas", value="2")
    with metric_col3:
        st.metric(label="📉 Preço Médio de Mercado", value="R$ 15,40")
        
    # Aqui entraria a tua tabela real vinda do Athena no futuro
    st.info("A ligação com o banco de dados da AWS será exibida aqui em formato de tabela.")