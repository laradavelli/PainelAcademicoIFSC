import streamlit as st
import pandas as pd
import json
import os

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

SPREADSHEET_ID = "15KawxJNSE5Im_Z0zHcYL9M0np9YQjJFgLLt2Lttg6Fc"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]
CREDENTIALS_FILE = os.path.join("dados", "google_credentials.json")

# URL pública para leitura (quando a planilha está publicada na web)
PUBLISHED_ID = "2PACX-1vQv7dhuGHZV9zvfrEwpPbtEselWj7N04QzEH7ctM-uUxIKVsx1hXURDZv4OJleMha0QA507O6tgF11I"
PUBLIC_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/e/{PUBLISHED_ID}"
    "/pub?output=csv&gid=0"
)

# Índices de colunas (0-based)
COL_A_IDX = 0   # Data da Solicitação
COL_E_IDX = 4   # Curso
COL_F_IDX = 5   # Tipo de Solicitação
COL_Q_IDX = 16  # Parecer da Coord. de Curso
COL_R_IDX = 17  # Observações / justificativa da coordenação
HEADER_ROWS = 2  # Linhas 1 e 2 são cabeçalhos


# ── Credenciais e cliente gspread ────────────────────────────────────────

def _save_credentials(creds_dict):
    """Salva credenciais no arquivo local para reutilização."""
    os.makedirs(os.path.dirname(CREDENTIALS_FILE), exist_ok=True)
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds_dict, f)


def get_gspread_client():
    """Obtém cliente gspread autenticado (arquivo, upload ou secrets)."""
    if not GSPREAD_AVAILABLE:
        return None

    creds_info = None

    # 1) Arquivo local salvo
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            creds_info = json.load(f)

    # 2) Upload feito na sessão
    elif "google_creds_json" in st.session_state:
        creds_info = st.session_state["google_creds_json"]

    # 3) st.secrets (deploy no Streamlit Cloud)
    else:
        try:
            if "gcp_service_account" in st.secrets:
                creds_info = dict(st.secrets["gcp_service_account"])
        except Exception:
            pass

    if creds_info is None:
        return None

    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    return gspread.authorize(creds)


# ── Leitura de dados ─────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def fetch_sheet_gspread(_client):
    """Busca dados via gspread (autenticado — leitura + escrita)."""
    sheet = _client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet.get_all_values()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_sheet_public():
    """Busca dados via URL pública (somente leitura, sem credenciais)."""
    df = pd.read_csv(PUBLIC_CSV_URL, header=None, dtype=str, keep_default_na=False)
    return df.values.tolist()


def build_dataframe(all_values):
    """Constrói DataFrame a partir dos valores brutos da planilha."""
    if not all_values or len(all_values) <= HEADER_ROWS:
        return pd.DataFrame(), []

    row1 = all_values[0]
    row2 = all_values[1]
    num_cols = max(len(row1), len(row2))

    headers = []
    for i in range(num_cols):
        h1 = row1[i].strip() if i < len(row1) else ""
        h2 = row2[i].strip() if i < len(row2) else ""
        header = h2 if h2 else h1 if h1 else f"Col_{i+1}"
        if header in headers:
            header = f"{header}_{i+1}"
        headers.append(header)

    data = all_values[HEADER_ROWS:]
    for i, row in enumerate(data):
        if len(row) < num_cols:
            data[i] = row + [""] * (num_cols - len(row))
        elif len(row) > num_cols:
            data[i] = row[:num_cols]

    df = pd.DataFrame(data, columns=headers)
    return df, headers


# ── Página principal ─────────────────────────────────────────────────────

def main():
    st.sidebar.image(os.path.join("assets", "figConselho2.png"))
    st.sidebar.image(os.path.join("assets", "figConselho.png"))

    st.title("📝 Ajustes")
    st.write("Gerenciamento de ajustes de matrícula — Planilha Google Drive.")

    # ── Verificar dependências ───────────────────────────────────────────
    if not GSPREAD_AVAILABLE:
        st.error("⚠️ Bibliotecas necessárias não instaladas!")
        st.code("pip install gspread google-auth", language="bash")
        st.stop()

    # ── Tentar autenticação ──────────────────────────────────────────────
    client = get_gspread_client()
    write_enabled = client is not None

    # ── Painel de credenciais (na página) ────────────────────────────────
    with st.expander("⚙️ Credenciais Google"):
        if write_enabled:
            st.success("✅ Conectado (leitura e escrita)")
            if st.button("🗑️ Remover credenciais"):
                if os.path.exists(CREDENTIALS_FILE):
                    os.remove(CREDENTIALS_FILE)
                st.session_state.pop("google_creds_json", None)
                st.rerun()
        else:
            st.warning("Sem credenciais — modo somente leitura")
            st.markdown("**Faça upload do arquivo JSON da conta de serviço:**")
            uploaded = st.file_uploader(
                "Chave JSON",
                type=["json"],
                key="creds_uploader",
                label_visibility="collapsed",
            )
            if uploaded is not None:
                try:
                    creds_dict = json.load(uploaded)
                    if "client_email" not in creds_dict:
                        st.error("Arquivo inválido — não contém 'client_email'.")
                    else:
                        _save_credentials(creds_dict)
                        st.session_state["google_creds_json"] = creds_dict
                        st.success(
                            f"Credenciais salvas! Conta: `{creds_dict['client_email']}`"
                        )
                        st.info(
                            "Compartilhe a planilha com esse e-mail "
                            "(permissão de **Editor**) e recarregue a página."
                        )
                        st.rerun()
                except json.JSONDecodeError:
                    st.error("Arquivo JSON inválido.")

            with st.popover("ℹ️ Como obter o arquivo JSON"):
                st.markdown(
                    """
**É gratuito.** Siga estes passos:

1. Acesse [console.cloud.google.com](https://console.cloud.google.com/) com `luiz.radavelli@ifsc.edu.br`
2. **Criar projeto** → nome: `painel-academico` → Criar
3. No menu ☰ → **APIs e Serviços** → **Biblioteca**
   - Pesquise **Google Sheets API** → **Ativar**
   - Pesquise **Google Drive API** → **Ativar**
4. Menu ☰ → **APIs e Serviços** → **Credenciais**
   - **Criar credenciais** → **Conta de serviço**
   - Nome: `painel` → Criar e continuar → Concluído
5. Clique na conta de serviço criada → aba **Chaves**
   - **Adicionar chave** → **Criar nova chave** → **JSON** → Criar
   - O arquivo `.json` será baixado
6. **Faça upload** desse arquivo acima ☝️
7. Abra a planilha → **Compartilhar** → cole o `client_email` do JSON → **Editor**
                    """
                )

    # ── Botão atualizar ──────────────────────────────────────────────────
    if st.button("🔄 Atualizar dados"):
        fetch_sheet_gspread.clear()
        fetch_sheet_public.clear()
        st.rerun()

    # ── Carregar dados ───────────────────────────────────────────────────
    all_values = None
    with st.spinner("Carregando dados da planilha..."):
        if write_enabled:
            try:
                all_values = fetch_sheet_gspread(client)
            except Exception as e:
                st.warning(f"Erro com credenciais ({e}). Tentando leitura pública...")
                write_enabled = False

        if all_values is None:
            try:
                all_values = fetch_sheet_public()
            except Exception as e:
                st.error(
                    f"Não foi possível acessar a planilha: {e}\n\n"
                    "Verifique se a planilha está publicada na web "
                    "(Arquivo → Compartilhar → Publicar na web → CSV) "
                    "ou configure as credenciais na barra lateral."
                )
                st.stop()

    df, headers = build_dataframe(all_values)

    if df.empty:
        st.warning("Planilha sem dados.")
        st.stop()

    if not write_enabled:
        st.info(
            "📖 **Modo somente leitura** — para editar as colunas Q e R, "
            "configure as credenciais na barra lateral (⚙️)."
        )

    # ── Nomes das colunas de interesse ───────────────────────────────────
    col_a = headers[COL_A_IDX] if len(headers) > COL_A_IDX else None
    col_e = headers[COL_E_IDX] if len(headers) > COL_E_IDX else None
    col_f = headers[COL_F_IDX] if len(headers) > COL_F_IDX else None
    col_q = headers[COL_Q_IDX] if len(headers) > COL_Q_IDX else None
    col_r = headers[COL_R_IDX] if len(headers) > COL_R_IDX else None

    # ── Filtros ──────────────────────────────────────────────────────────
    st.subheader("Filtros")
    f1, f2 = st.columns(2)

    with f1:
        if col_e:
            cursos_disponiveis = sorted(
                [c for c in df[col_e].dropna().unique() if c.strip()]
            )
        else:
            cursos_disponiveis = []

        # Usar curso selecionado na Home como padrão
        curso_global = st.session_state.get("curso_selecionado", "Todos")
        opcoes_curso = ["Todos"] + cursos_disponiveis
        idx_default = 0
        if curso_global in opcoes_curso:
            idx_default = opcoes_curso.index(curso_global)
        curso_sel = st.selectbox("Curso", opcoes_curso, index=idx_default)

    with f2:
        status_sel = st.selectbox(
            "Parecer da Coord. de Curso",
            ["Todos", "Pendente (em branco)", "Deferido", "Indeferido"],
        )

    # ── Aplicar filtros ──────────────────────────────────────────────────
    mask = pd.Series(True, index=df.index)

    if curso_sel != "Todos" and col_e:
        mask &= df[col_e] == curso_sel

    if status_sel != "Todos" and col_q:
        if "Pendente" in status_sel:
            mask &= df[col_q].str.strip() == ""
        elif status_sel == "Deferido":
            mask &= df[col_q].str.strip().str.lower() == "deferido"
        elif status_sel == "Indeferido":
            mask &= df[col_q].str.strip().str.lower() == "indeferido"

    df_filtrado = df[mask].copy()

    # ── Ordenar por data decrescente (mais recentes primeiro) ────────────
    if col_a:
        df_filtrado["_data_sort"] = pd.to_datetime(
            df_filtrado[col_a], dayfirst=True, errors="coerce"
        )
        df_filtrado = df_filtrado.sort_values("_data_sort", ascending=False)
        df_filtrado = df_filtrado.drop(columns=["_data_sort"])

    st.write(f"**{len(df_filtrado)}** registro(s) encontrado(s)")

    if df_filtrado.empty:
        st.info("Nenhum registro encontrado com os filtros selecionados.")
        st.stop()

    # ── Exibição / Edição de dados ───────────────────────────────────────
    st.subheader("Dados")

    if write_enabled:
        disabled_cols = [c for c in df_filtrado.columns if c not in (col_q, col_r)]

        column_config = {}
        if col_q:
            column_config[col_q] = st.column_config.SelectboxColumn(
                col_q,
                options=["", "Deferido", "Indeferido"],
                help="Selecione o parecer da Coordenação de Curso",
            )
        if col_r:
            column_config[col_r] = st.column_config.TextColumn(
                col_r,
                help="Observações da Coordenação",
            )

        edited_df = st.data_editor(
            df_filtrado,
            column_config=column_config,
            disabled=disabled_cols,
            use_container_width=True,
            num_rows="fixed",
            key="ajustes_editor",
        )

        # ── Salvar alterações ────────────────────────────────────────────
        if st.button("💾 Salvar alterações", type="primary"):
            updates = []
            for idx in df_filtrado.index:
                if col_q:
                    old_q = df_filtrado.at[idx, col_q]
                    new_q = edited_df.at[idx, col_q]
                    if old_q != new_q:
                        updates.append((idx, COL_Q_IDX, new_q))
                if col_r:
                    old_r = df_filtrado.at[idx, col_r]
                    new_r = edited_df.at[idx, col_r]
                    if old_r != new_r:
                        updates.append((idx, COL_R_IDX, new_r))

            if updates:
                try:
                    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
                    cells = []
                    for row_idx, col_idx, value in updates:
                        sheet_row = row_idx + HEADER_ROWS + 1
                        sheet_col = col_idx + 1
                        cells.append(gspread.Cell(sheet_row, sheet_col, value))
                    sheet.update_cells(cells)
                    st.success(
                        f"✅ {len(updates)} célula(s) atualizada(s) com sucesso!"
                    )
                    fetch_sheet_gspread.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.info("Nenhuma alteração detectada.")
    else:
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    # ── Resumo / Relatório ───────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Resumo")

    # Contadores por status
    if col_q:
        total = len(df_filtrado)
        pendentes = (df_filtrado[col_q].str.strip() == "").sum()
        deferidos = (df_filtrado[col_q].str.strip().str.lower() == "deferido").sum()
        indeferidos = (df_filtrado[col_q].str.strip().str.lower() == "indeferido").sum()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", total)
        c2.metric("Pendentes", int(pendentes))
        c3.metric("Deferidos", int(deferidos))
        c4.metric("Indeferidos", int(indeferidos))

    # Contagem por tipo de solicitação
    if col_f:
        tipos = df_filtrado[col_f].str.strip()
        tipos = tipos[tipos != ""]
        if not tipos.empty:
            contagem_tipo = tipos.value_counts().reset_index()
            contagem_tipo.columns = ["Tipo de Solicitação", "Quantidade"]

            st.markdown("**Solicitações por tipo:**")
            st.dataframe(contagem_tipo, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
