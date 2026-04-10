import streamlit as st
import pandas as pd
from streamlit_elements import elements, mui
from PIL import UnidentifiedImageError
from utils import (
    setup_sidebar_header, 
    aplicar_css_padding, 
    get_foto_path,
    normalizar_dados,
    create_plotly_chart,
    preparar_dados_radar,
    CORES_GRAFICO,
    renderizar_matriz_curricular
)

# Configuração da página
st.set_page_config(page_title="Conselho de Classe", layout="wide")

# Verificação de acesso
if 'arquivo_carregado' not in st.session_state or not st.session_state.arquivo_carregado:
    setup_sidebar_header()
    st.error("⚠️ Por favor, faça o upload do arquivo na página inicial primeiro! Volte para Home.")
    st.stop()

# Configurar sidebar e CSS
setup_sidebar_header()
aplicar_css_padding()

# Recupera os dados da sessão
df = st.session_state.df

# Controle do índice do estudante atual
if "indice" not in st.session_state:
    st.session_state.indice = 0

# Linha 1: Seleção de fases (label ao lado do campo)
col_label, col_selector = st.columns([2, 2])
with col_label:
    st.markdown("### 📋 Selecione a(s) fase(s)")
with col_selector:
    fase = st.multiselect("", sorted(df["Fase"].unique()), key="fase_selector", label_visibility="collapsed")

if not fase:
    st.warning("Por favor, selecione pelo menos uma fase.")
    st.stop()

# Filtra dados da fase
dados_fase = df[df["Fase"].isin(fase)]
estudantes = dados_fase.drop_duplicates(subset=["Matricula", "Aluno"])[["Matricula", "Aluno"]].values.tolist()

# Reinicia índice se mudar a fase
if "fase_atual" not in st.session_state or st.session_state.fase_atual != fase:
    st.session_state.fase_atual = fase
    st.session_state.indice = 0

# Verifica se há estudantes
if not estudantes:
    st.warning("Nenhum estudante encontrado para as fases selecionadas.")
    st.stop()

# Funções de navegação
def proximo_estudante():
    if st.session_state.indice < len(estudantes) - 1:
        st.session_state.indice += 1

def anterior_estudante():
    if st.session_state.indice > 0:
        st.session_state.indice -= 1

def _slider_changed():
    st.session_state.indice = st.session_state.slider_estudante

# Sincroniza o slider com o índice atual (antes de renderizar o widget)
st.session_state.slider_estudante = st.session_state.indice

# Barra de seleção de estudante com slider
st.markdown("**Selecione o estudante:**")
st.slider(
    "",
    min_value=0,
    max_value=len(estudantes) - 1,
    format="Estudante %d de " + str(len(estudantes)),
    label_visibility="collapsed",
    key="slider_estudante",
    on_change=_slider_changed,
)

# Estudante atual
matricula, aluno = estudantes[st.session_state.indice]

# Linha 2: Nome do estudante com botões de navegação na mesma linha
col_nome, col_anterior, col_proximo = st.columns([4, 2, 2])

with col_nome:
    st.subheader(aluno)

with col_anterior:
    if st.session_state.indice > 0:
        st.button("⬅️ Anterior", on_click=anterior_estudante, width="stretch", type="secondary")

with col_proximo:
    if st.session_state.indice < len(estudantes) - 1:
        st.button("Próximo ➡️", on_click=proximo_estudante, width="stretch", type="secondary")

# Caminho da foto e preparação dos dados
foto_path = get_foto_path(matricula)
disciplinas = dados_fase[dados_fase["Matricula"] == matricula].copy()

# Normaliza dados usando função compartilhada
disciplinas = normalizar_dados(disciplinas)

# Prepara dados para o gráfico radar (todas as disciplinas)
dados_radar = preparar_dados_radar(disciplinas)

# Controle de tipo de visualização
if "tipo_grafico" not in st.session_state:
    st.session_state.tipo_grafico = "Colunas"

# Layout: Foto + Botões de escolha + Gráfico
col_foto, col_grafico = st.columns([2, 2])

with col_foto:
    st.caption(f"Matrícula: {matricula}")
    if foto_path:
        try:
            st.image(foto_path, width=180)
        except (UnidentifiedImageError, Exception):
            st.markdown("👤")
    else:
        st.markdown("👤")
    
with col_grafico:
    if st.session_state.tipo_grafico == "Colunas":
        # Gráfico de Colunas usando função compartilhada (todas as disciplinas)
        if not disciplinas.empty:
            fig = create_plotly_chart(disciplinas)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma disciplina encontrada para este estudante.")
    
    else:
        # Gráfico Radar
        from streamlit_elements import nivo
        with elements("radar_chart"):
            with mui.Box(sx={"height": 400}):
                nivo.Radar(
                    data=dados_radar,
                    keys=["Nota", "Faltas"],
                    indexBy="disciplina",
                    valueFormat=">-.1f",
                    margin={ "top": 50, "right": 100, "bottom": 50, "left": 100 },
                    borderColor={ "from": "color" },
                    gridLabelOffset=36,
                    dotSize=8,
                    dotColor={ "theme": "background" },
                    dotBorderWidth=2,
                    motionConfig="wobbly",
                    maxValue=10,
                    colors=[CORES_GRAFICO['radar_nota'], CORES_GRAFICO['radar_faltas']],
                    legends=[
                        {
                            "anchor": "top-left",
                            "direction": "column",
                            "translateX": -50,
                            "translateY": -40,
                            "itemWidth": 80,
                            "itemHeight": 20,
                            "itemTextColor": "#999",
                            "symbolSize": 12,
                            "symbolShape": "circle",
                            "effects": [{"on": "hover", "style": {"itemTextColor": "#000"}}]
                        }
                    ],
                    theme={
                        "background": "#FFFFFF",
                        "textColor": "#31333F",
                        "tooltip": {
                            "container": {
                                "background": "#FFFFFF",
                                "color": "#31333F",
                            }
                        }
                    }
                )

# Botões de escolha do tipo de gráfico
st.markdown("---")
st.markdown("**Tipo de visualização:**")
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("📊 Colunas", width="stretch", type="primary" if st.session_state.tipo_grafico == "Colunas" else "secondary"):
        st.session_state.tipo_grafico = "Colunas"
        st.rerun()
with col_btn2:
    if st.button("🎯 Radar", width="stretch", type="primary" if st.session_state.tipo_grafico == "Radar" else "secondary"):
        st.session_state.tipo_grafico = "Radar"
        st.rerun()

# ==================== SEÇÃO: MATRIZ CURRICULAR DO ESTUDANTE ====================
st.markdown("---")
st.subheader("📐 Matriz Curricular do Estudante")
renderizar_matriz_curricular(df, matricula, css_prefix="ci", apenas_matriculadas=True)
