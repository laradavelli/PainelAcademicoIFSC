import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Discentes", layout="wide")

# Verificação de acesso
if 'arquivo_carregado' not in st.session_state or not st.session_state.arquivo_carregado:
    from utils import setup_sidebar_header
    setup_sidebar_header()
    st.error("⚠️ Por favor, faça o upload do arquivo na página inicial primeiro! Volte para Home.")
    st.stop()

# Configuração da sidebar
from utils import setup_sidebar_header
setup_sidebar_header()

# Recupera os dados da sessão
df = st.session_state.df

# Padding da página
st.markdown("""
    <style>
        .block-container {
            padding-top: 2.8rem;
            padding-bottom: 0rem;
        }
    </style>
    """, unsafe_allow_html=True)

# Título da página
st.title("📋 Análise dos Estudantes")

# Agrupa dados por estudante (considerando múltiplas fases)
estudantes_info = df.groupby(['Matricula', 'Aluno']).agg({
    'Fase': lambda x: ', '.join(sorted(x.unique())),
    'Disciplina': lambda x: ', '.join(sorted(x.unique()))
}).reset_index()

estudantes_info.columns = ['Matrícula', 'Nome', 'Fase(s)', 'Disciplinas']

# Métricas gerais
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total de Discentes", len(estudantes_info))
with col2:
    st.metric("Total de Disciplinas", df['Disciplina'].nunique())
with col3:
    st.metric("Fases Ativas", df['Fase'].nunique())

# st.markdown("---")

# Filtros
st.subheader("🔍 Filtros")

# Linha 1: Filtros principais
col_fase, col_situacao, col_busca = st.columns([1, 1, 2])

with col_fase:
    fases_disponiveis = ['Todas'] + sorted(df['Fase'].unique().tolist())
    fase_filtro = st.selectbox("Filtrar por Fase:", fases_disponiveis)

with col_situacao:
    # Obtém situações únicas, tratando valores vazios/nulos
    situacoes_raw = df['Situacao'].dropna().unique().tolist()
    situacoes_raw = [s for s in situacoes_raw if s and str(s).strip()]  # Remove vazios
    situacoes_disponiveis = ['Todas'] + sorted(situacoes_raw) if situacoes_raw else ['Todas']
    situacao_filtro = st.selectbox("Filtrar por Situação:", situacoes_disponiveis)

with col_busca:
    busca_nome = st.text_input("Buscar por Nome ou Matrícula:", "")

# Linha 2: Filtros específicos de disciplina
col_disciplina, col_especiais = st.columns([2, 1])

with col_disciplina:
    disciplinas_disponiveis = sorted(df['Disciplina'].unique().tolist())
    disciplina_filtro = st.multiselect("Filtrar por Disciplina(s):", disciplinas_disponiveis)

with col_especiais:
    st.markdown("<div style='margin-bottom: 0.5rem;'><strong>Filtros Especiais:</strong></div>", unsafe_allow_html=True)
    col_tcc, col_estagio = st.columns(2)
    with col_tcc:
        filtro_tcc = st.toggle("TCC", help="Filtra estudantes matriculados em disciplinas de TCC.")
    with col_estagio:
        filtro_estagio = st.toggle("Estágio", help="Filtra estudantes matriculados em disciplinas de Estágio.")

# Agrupa situações por estudante para o filtro
if 'Situacao' in df.columns:
    situacoes_por_estudante = df.groupby(['Matricula', 'Aluno']).agg({
        'Situacao': lambda x: ', '.join(sorted(set(str(s) for s in x.dropna() if s and str(s).strip())))
    }).reset_index()
    situacoes_por_estudante.columns = ['Matrícula', 'Nome', 'Situação']
    estudantes_info = estudantes_info.merge(situacoes_por_estudante[['Matrícula', 'Situação']], on='Matrícula', how='left')

# Aplica filtros
df_filtrado = estudantes_info.copy()

if fase_filtro != 'Todas':
    # Filtra estudantes que cursam a fase selecionada (pode estar em múltiplas fases)
    df_filtrado = df_filtrado[df_filtrado['Fase(s)'].str.contains(fase_filtro, na=False)]

if situacao_filtro != 'Todas':
    # Filtra estudantes pela situação selecionada
    df_filtrado = df_filtrado[df_filtrado['Situação'].str.contains(situacao_filtro, case=False, na=False)]

if busca_nome:
    df_filtrado = df_filtrado[
        df_filtrado['Nome'].str.contains(busca_nome, case=False, na=False) | 
        df_filtrado['Matrícula'].str.contains(busca_nome, case=False, na=False)
    ]

# Filtro por disciplina específica
if disciplina_filtro:
    # Garante que o estudante esteja em TODAS as disciplinas selecionadas
    matriculas_disciplina = df[df['Disciplina'].isin(disciplina_filtro)].groupby('Matricula')['Disciplina'].nunique()
    matriculas_validas = matriculas_disciplina[matriculas_disciplina == len(disciplina_filtro)].index
    df_filtrado = df_filtrado[df_filtrado['Matrícula'].isin(matriculas_validas)]

# Filtros especiais (TCC e Estágio)
if filtro_tcc:
    matriculas_tcc = df[df['Disciplina'].str.contains("TCC|TRABALHO DE CONCLUSÃO", case=False, na=False)]['Matricula'].unique()
    df_filtrado = df_filtrado[df_filtrado['Matrícula'].isin(matriculas_tcc)]

if filtro_estagio:
    matriculas_estagio = df[df['Disciplina'].str.contains("ESTÁGIO", case=False, na=False)]['Matricula'].unique()
    df_filtrado = df_filtrado[df_filtrado['Matrícula'].isin(matriculas_estagio)]

# st.markdown("---")

# Exibe a tabela de estudantes
# st.subheader(f"📊 Lista de Discentes ({len(df_filtrado)} encontrado(s))")

# Configuração da tabela - exibe sem a coluna Situação
colunas_exibir = ['Matrícula', 'Nome', 'Fase(s)', 'Disciplinas']
df_exibir = df_filtrado[colunas_exibir] if 'Situação' in df_filtrado.columns else df_filtrado

st.dataframe(
    df_exibir,
    width="stretch",
    hide_index=True,
    column_config={
        "Matrícula": st.column_config.TextColumn("Matrícula", width="small"),
        "Nome": st.column_config.TextColumn("Nome", width="medium"),
        "Fase(s)": st.column_config.TextColumn("Fase(s)", width="small"),
        "Disciplinas": st.column_config.TextColumn("Disciplinas", width="large"),
    }
)

# Seleção de estudante para detalhamento
st.markdown("---")
st.subheader("🎓 Detalhamento por Estudante")

estudante_selecionado = ""
matricula_sel = ""

if not df_filtrado.empty:
    opcoes_estudante = df_filtrado.apply(lambda r: f"{r['Matrícula']} - {r['Nome']}", axis=1).tolist()
    estudante_selecionado = st.selectbox("Selecione um discente:", [""] + opcoes_estudante)

    if estudante_selecionado:
        matricula_sel = estudante_selecionado.split(" - ")[0].strip()
        nome_sel = " - ".join(estudante_selecionado.split(" - ")[1:]).strip()

        # Filtra dados do estudante no dataframe original
        df_estudante = df[df['Matricula'] == matricula_sel].copy()

        st.markdown(f"**Aluno(a):** {nome_sel}  &nbsp; | &nbsp; **Matrícula:** {matricula_sel}")

        # Tabela única com disciplinas ordenadas por fase
        df_detalhe = df_estudante[['Codigo', 'Disciplina', 'Fase']].copy()
        df_detalhe.columns = ['Código', 'Disciplina', 'Fase']
        df_detalhe = df_detalhe.sort_values(['Fase', 'Disciplina']).reset_index(drop=True)

        st.dataframe(
            df_detalhe,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Código": st.column_config.TextColumn("Código", width="small"),
                "Disciplina": st.column_config.TextColumn("Disciplina", width="large"),
                "Fase": st.column_config.TextColumn("Fase", width="small"),
            }
        )
else:
    st.info("Nenhum discente encontrado com os filtros aplicados.")

# Botão de download
st.markdown("---")
csv = df_filtrado.to_csv(index=False, sep=';', encoding='utf-8')
st.download_button(
    label="📥 Baixar lista filtrada (CSV)",
    data=csv,
    file_name="discentes_filtrados.csv",
    mime="text/csv",
    width="stretch"
)

# ==================== SEÇÃO: REPRESENTANTES DE TURMA ====================
st.markdown("---")

import os
from datetime import datetime as _dt

_REPR_PATH = os.path.join("dados", "representantes_turma.csv")
_ano = _dt.now().year
_semestre_atual = f"{_ano}.{1 if _dt.now().month <= 6 else 2}"

def _carregar_representantes():
    if os.path.exists(_REPR_PATH):
        _df = pd.read_csv(_REPR_PATH, dtype=str).fillna("")
        return _df[_df['semestre'] == _semestre_atual]
    return pd.DataFrame(columns=['fase', 'representante', 'vice', 'semestre'])

def _salvar_representantes(df_repr):
    if os.path.exists(_REPR_PATH):
        df_all = pd.read_csv(_REPR_PATH, dtype=str).fillna("")
        df_all = df_all[df_all['semestre'] != _semestre_atual]
    else:
        df_all = pd.DataFrame(columns=['fase', 'representante', 'vice', 'semestre'])
    df_all = pd.concat([df_all, df_repr], ignore_index=True)
    df_all.to_csv(_REPR_PATH, index=False)

_df_repr = _carregar_representantes()
_repr_map = {str(r['fase']): r.to_dict() for _, r in _df_repr.iterrows()}

# Fases com alunos matriculados
_fases_ativas = sorted(df['Fase'].dropna().unique().tolist(), key=lambda x: int(x) if str(x).isdigit() else 999)

# Cabeçalho das colunas
with st.expander("👥 Representantes de Turma (Colegiado)", expanded=False):
    _hdr = st.columns([0.5, 2, 2])
    with _hdr[0]:
        st.caption("Fase")
    with _hdr[1]:
        st.caption("Representante")
    with _hdr[2]:
        st.caption("Vice-representante")

    _novos = []
    for _fase in _fases_ativas:
        _alunos_fase = sorted(df[df['Fase'] == _fase]['Aluno'].unique().tolist())
        _opcoes = [""] + _alunos_fase
        _prev = _repr_map.get(str(_fase), {})
        _prev_rep = _prev.get('representante', '') if isinstance(_prev, dict) else ''
        _prev_vice = _prev.get('vice', '') if isinstance(_prev, dict) else ''

        _cols = st.columns([0.5, 2, 2])
        with _cols[0]:
            st.markdown(f"**{_fase}ª**")
        with _cols[1]:
            _sel_rep = st.selectbox(
                f"Representante {_fase}ª fase",
                _opcoes,
                index=_opcoes.index(_prev_rep) if _prev_rep in _opcoes else 0,
                key=f"repr_{_fase}",
                label_visibility="collapsed"
            )
        with _cols[2]:
            _sel_vice = st.selectbox(
                f"Vice {_fase}ª fase",
                _opcoes,
                index=_opcoes.index(_prev_vice) if _prev_vice in _opcoes else 0,
                key=f"vice_{_fase}",
                label_visibility="collapsed"
            )
        _novos.append({'fase': str(_fase), 'representante': _sel_rep, 'vice': _sel_vice, 'semestre': _semestre_atual})

    if st.button("💾 Salvar Representantes", type="primary"):
        _df_novo = pd.DataFrame(_novos)
        _df_novo = _df_novo[(_df_novo['representante'] != '') | (_df_novo['vice'] != '')]
        _salvar_representantes(_df_novo)
        st.success("Representantes salvos com sucesso!")
        st.rerun()

# ==================== SEÇÃO: MATRIZ CURRICULAR DO ESTUDANTE ====================
if not df_filtrado.empty and estudante_selecionado:
    from utils import renderizar_matriz_curricular
    st.markdown("---")
    st.subheader("📐 Matriz Curricular do Estudante")
    renderizar_matriz_curricular(df, matricula_sel, css_prefix="disc")
