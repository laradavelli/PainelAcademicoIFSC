import streamlit as st
import pandas as pd
import os
from datetime import datetime

def carregar_df(path, columns=None):
    if os.path.exists(path):
        df = pd.read_csv(path)
        if columns:
            for col in columns:
                if col not in df.columns:
                    df[col] = ""
        return df
    else:
        if columns:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame()


# ── Ajustes: leitura da planilha pública ─────────────────────────────────
PUBLISHED_ID = "2PACX-1vQv7dhuGHZV9zvfrEwpPbtEselWj7N04QzEH7ctM-uUxIKVsx1hXURDZv4OJleMha0QA507O6tgF11I"
AJUSTES_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/e/{PUBLISHED_ID}"
    "/pub?output=csv&gid=0"
)
AJUSTES_HEADER_ROWS = 2
COL_A_IDX = 0   # Data da Solicitação
COL_E_IDX = 4   # Curso
COL_F_IDX = 5   # Tipo de Solicitação

@st.cache_data(ttl=300, show_spinner=False)
def carregar_ajustes():
    """Carrega dados de ajustes da planilha pública e adiciona coluna 'semestre'."""
    try:
        df_raw = pd.read_csv(
            AJUSTES_CSV_URL, header=None, dtype=str, keep_default_na=False
        )
    except Exception:
        return pd.DataFrame()

    if len(df_raw) <= AJUSTES_HEADER_ROWS:
        return pd.DataFrame()

    # Construir cabeçalhos a partir das linhas 1 e 2
    row1 = df_raw.iloc[0].tolist()
    row2 = df_raw.iloc[1].tolist()
    num_cols = len(row1)
    headers = []
    for i in range(num_cols):
        h1 = str(row1[i]).strip() if i < len(row1) else ""
        h2 = str(row2[i]).strip() if i < len(row2) else ""
        header = h2 if h2 else h1 if h1 else f"Col_{i+1}"
        if header in headers:
            header = f"{header}_{i+1}"
        headers.append(header)

    df = df_raw.iloc[AJUSTES_HEADER_ROWS:].copy()
    df.columns = headers

    # Derivar semestre a partir da data de solicitação (coluna A)
    col_a = headers[COL_A_IDX]
    datas = pd.to_datetime(df[col_a], dayfirst=True, errors="coerce")
    df["semestre"] = datas.apply(
        lambda d: f"{d.year}.{1 if d.month <= 6 else 2}" if pd.notna(d) else None
    )
    return df


def main():
    # Sidebar com logos (padrão visual)
    st.sidebar.image(os.path.join("assets", "figConselho2.png"))
    st.sidebar.image(os.path.join("assets", "figConselho.png"))

    st.title("📊 Relatório Geral de Atividades")
    st.write("Selecione o semestre para emitir o relatório consolidado de atividades realizadas.")


    # Caminhos dos arquivos
    path_validacoes = os.path.join("dados", "solicitacoes_validacoes.csv")
    path_prereq = os.path.join("dados", "solicitacoes_prerequisito.csv")
    path_matriculas = os.path.join("dados", "solicitacoes_matricula_avulsa.csv")
    path_protocolos = os.path.join("dados", "protocolos_sipac.csv")

    # Carregar DataFrames
    df_validacoes = carregar_df(path_validacoes)
    df_prereq = carregar_df(path_prereq)
    df_matriculas = carregar_df(path_matriculas)
    df_protocolos = carregar_df(path_protocolos)
    df_ajustes = carregar_ajustes()

    # Filtrar ajustes pelo curso selecionado globalmente
    curso_global = st.session_state.get("curso_selecionado", "Todos")
    if curso_global != "Todos" and not df_ajustes.empty:
        col_e_name = df_ajustes.columns[COL_E_IDX] if len(df_ajustes.columns) > COL_E_IDX else None
        if col_e_name:
            df_ajustes = df_ajustes[df_ajustes[col_e_name].astype(str) == curso_global]

    # Descobrir todos os semestres disponíveis
    semestres = set()
    for df in [df_validacoes, df_prereq, df_matriculas, df_protocolos, df_ajustes]:
        if not df.empty and "semestre" in df.columns:
            semestres.update(str(s) for s in df["semestre"].dropna().unique())
    semestres = sorted(list(semestres), reverse=True)

    semestre = st.selectbox("Selecione o semestre", options=semestres, index=0 if semestres else None)

    if semestre:
        st.subheader(f"Resumo dos processos no semestre {semestre}")
        total_validacoes = df_validacoes[df_validacoes["semestre"].astype(str) == semestre].shape[0] if not df_validacoes.empty and "semestre" in df_validacoes.columns else 0
        total_prereq = df_prereq[df_prereq["semestre"].astype(str) == semestre].shape[0] if not df_prereq.empty and "semestre" in df_prereq.columns else 0
        total_matriculas = df_matriculas[df_matriculas["semestre"].astype(str) == semestre].shape[0] if not df_matriculas.empty and "semestre" in df_matriculas.columns else 0
        total_protocolos = df_protocolos[df_protocolos["semestre"].astype(str) == semestre].shape[0] if not df_protocolos.empty and "semestre" in df_protocolos.columns else 0
        total_ajustes = df_ajustes[df_ajustes["semestre"].astype(str) == semestre].shape[0] if not df_ajustes.empty and "semestre" in df_ajustes.columns else 0

        total_atividades = total_validacoes + total_prereq + total_matriculas + total_protocolos + total_ajustes

        col1, col2 = st.columns([1, 1])
        # Definir cores padronizadas para as demandas
        cores_padrao = {
            "Validações": "#1f77b4",
            "Quebra de Pré-requisito": "#ff7f0e",
            "Solicitações de Matrícula": "#2ca02c",
            "Protocolos SIPAC": "#d62728",
            "Ajustes": "#9467bd",
        }
        with col1:
            st.markdown(f"- **Validações:** {total_validacoes}")
            st.markdown(f"- **Quebra de Pré-requisito:** {total_prereq}")
            st.markdown(f"- **Solicitações de Matrícula:** {total_matriculas}")
            st.markdown(f"- **Protocolos SIPAC:** {total_protocolos}")
            st.markdown(f"- **Ajustes:** {total_ajustes}")
            st.markdown(f"\n**Total de atividades registradas:** {total_atividades}")
        with col2:
            import plotly.graph_objects as go
            pie_data = pd.DataFrame({
                "Atividade": list(cores_padrao.keys()),
                "Quantidade": [total_validacoes, total_prereq, total_matriculas, total_protocolos, total_ajustes]
            })
            fig = go.Figure(data=[go.Pie(
                labels=pie_data["Atividade"],
                values=pie_data["Quantidade"],
                marker=dict(colors=[cores_padrao[a] for a in pie_data["Atividade"]]),
                hole=0.4,
                pull=[0.05]*5,
                textinfo='percent',
                showlegend=False
            )])
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), width=250, height=250, showlegend=False)
            st.plotly_chart(fig, use_container_width=False)

        # Gráfico de evolução por semestre (colunas)
        # linha separadora
        st.markdown("<hr>", unsafe_allow_html=True)
        # Legenda horizontal customizada
        st.markdown("""
<div style='display: flex; justify-content: center; gap: 32px; margin-bottom: 0.5em;'>
  <span style='display: flex; align-items: center; gap: 0.5em;'>
    <span style='width: 18px; height: 18px; background: #1f77b4; display: inline-block; border-radius: 3px;'></span>
    Validações
  </span>
  <span style='display: flex; align-items: center; gap: 0.5em;'>
    <span style='width: 18px; height: 18px; background: #ff7f0e; display: inline-block; border-radius: 3px;'></span>
    Quebra de Pré-requisito
  </span>
  <span style='display: flex; align-items: center; gap: 0.5em;'>
    <span style='width: 18px; height: 18px; background: #2ca02c; display: inline-block; border-radius: 3px;'></span>
    Solicitações de Matrícula
  </span>
  <span style='display: flex; align-items: center; gap: 0.5em;'>
    <span style='width: 18px; height: 18px; background: #d62728; display: inline-block; border-radius: 3px;'></span>
    Protocolos SIPAC
  </span>
  <span style='display: flex; align-items: center; gap: 0.5em;'>
    <span style='width: 18px; height: 18px; background: #9467bd; display: inline-block; border-radius: 3px;'></span>
    Ajustes
  </span>
</div>
        """, unsafe_allow_html=True)
        # linha separadora
        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader("Evolução das Atividades por Semestre")
        semestres_evol = sorted(list(set(semestres)))
        import altair as alt

        # Dados das demandas (sem Ajustes) — coluna esquerda empilhada
        demandas_names = ["Validações", "Quebra de Pré-requisito", "Solicitações de Matrícula", "Protocolos SIPAC"]
        demandas_dfs = [df_validacoes, df_prereq, df_matriculas, df_protocolos]
        rows_demandas = []
        for s in semestres_evol:
            for name, df_d in zip(demandas_names, demandas_dfs):
                qtd = df_d[df_d["semestre"].astype(str) == s].shape[0] if not df_d.empty and "semestre" in df_d.columns else 0
                rows_demandas.append({"Semestre": s, "Atividade": name, "Quantidade": qtd, "Grupo": "Demandas"})
        df_dem = pd.DataFrame(rows_demandas)

        # Dados de Ajustes — coluna direita
        rows_ajustes = []
        for s in semestres_evol:
            qtd = df_ajustes[df_ajustes["semestre"].astype(str) == s].shape[0] if not df_ajustes.empty and "semestre" in df_ajustes.columns else 0
            rows_ajustes.append({"Semestre": s, "Atividade": "Ajustes", "Quantidade": qtd, "Grupo": "Ajustes"})
        df_aj = pd.DataFrame(rows_ajustes)

        df_evol_all = pd.concat([df_dem, df_aj], ignore_index=True)

        color_scale = alt.Scale(domain=list(cores_padrao.keys()), range=list(cores_padrao.values()))

        chart = alt.Chart(df_evol_all).mark_bar().encode(
            x=alt.X('Grupo:N', title=None, axis=alt.Axis(labels=False, ticks=False)),
            y=alt.Y('Quantidade:Q', title='Quantidade', stack='zero'),
            color=alt.Color('Atividade:N', scale=color_scale, legend=None),
            column=alt.Column('Semestre:N', title='Semestre', header=alt.Header(labelOrient='bottom')),
            tooltip=['Semestre', 'Atividade', 'Quantidade'],
            order=alt.Order('Atividade:N'),
        ).properties(
            width=80,
            height=300
        ).configure_facet(
            spacing=15
        )
        st.altair_chart(chart, use_container_width=False)

        # Exibir detalhes em expansores
        if total_validacoes > 0:
            with st.expander("Validações", expanded=False):
                st.dataframe(df_validacoes[df_validacoes["semestre"].astype(str) == semestre], use_container_width=True, hide_index=True)
        if total_prereq > 0:
            with st.expander("Quebra de Pré-requisito", expanded=False):
                st.dataframe(df_prereq[df_prereq["semestre"].astype(str) == semestre], use_container_width=True, hide_index=True)
        if total_matriculas > 0:
            with st.expander("Solicitações de Matrícula", expanded=False):
                st.dataframe(df_matriculas[df_matriculas["semestre"].astype(str) == semestre], use_container_width=True, hide_index=True)
        if total_protocolos > 0:
            with st.expander("Protocolos SIPAC", expanded=False):
                st.dataframe(df_protocolos[df_protocolos["semestre"].astype(str) == semestre], use_container_width=True, hide_index=True)
        if total_ajustes > 0:
            with st.expander("Ajustes", expanded=False):
                df_aj_sem = df_ajustes[df_ajustes["semestre"].astype(str) == semestre].copy()
                # Mostrar colunas relevantes (sem a coluna auxiliar 'semestre')
                cols_mostrar = [c for c in df_aj_sem.columns if c != "semestre"]
                st.dataframe(df_aj_sem[cols_mostrar], use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
