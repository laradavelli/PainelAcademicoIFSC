import streamlit as st
import pandas as pd
import os

# Configuração da página
st.set_page_config(page_title="Listagem de Docentes", layout="wide")

# Configuração da sidebar
from utils import setup_sidebar_header, aplicar_css_padding
setup_sidebar_header()
aplicar_css_padding()

# ==================== CAMINHOS E CONSTANTES ====================
DOCENTES_PATH = os.path.join("dados", "Docentes.csv")
COORDENADORES_PATH = os.path.join("dados", "Coordenadores.csv")

# Colunas internas do Docentes.csv
DOCENTES_COLS = ["Docente", "SIAPE", "Colegiado", "NDE", "Email", "Coordenadoria", "Área", "Situação"]

# Opções para campos de seleção
AREAS_OPCOES = sorted(["ELET", "MEC", "MAT", "FIS", "QUI", "INF", "COM", "SHT", "ADM", "ING"])
SITUACAO_OPCOES = ["Ativo", "Afastado", "Substituto"]
COORDENADORIA_OPCOES = sorted(["EE", "CTM", "CTDS", "CSTFM", "EM", "CTE", "Outra"])
CURSOS_SIGLA = {
    "EE": "Engenharia Elétrica",
    "CTM": "Técnico em Mecânica",
    "CTDS": "Técnico em Desenvolvimento de Sistemas",
    "CSTFM": "Fabricação Mecânica",
    "EM": "Engenharia Mecânica",
    "CTE": "Técnico em Eletrotécnica",
    "Outra": "Outra Coordenação",
}


# ==================== FUNÇÕES DE PERSISTÊNCIA ====================
def carregar_docentes():
    """Carrega a planilha de docentes, normalizando colunas."""
    if os.path.exists(DOCENTES_PATH):
        df = pd.read_csv(DOCENTES_PATH, encoding='utf-8')
        # Normaliza: remove coluna-índice sem nome
        if df.columns[0] == '' or df.columns[0].startswith('Unnamed'):
            df = df.drop(df.columns[0], axis=1)
        # A coluna sem nome é o email
        unnamed_cols = [c for c in df.columns if c == '' or str(c).startswith('Unnamed')]
        if unnamed_cols:
            df = df.rename(columns={unnamed_cols[0]: 'Email'})
            for c in unnamed_cols[1:]:
                df = df.drop(c, axis=1)
        # Remove coluna 'Coordenador' legada (agora gerenciada via Coordenadores.csv)
        if 'Coordenador' in df.columns:
            df = df.drop('Coordenador', axis=1)
        # Garante todas as colunas
        for col in DOCENTES_COLS:
            if col not in df.columns:
                df[col] = ""
        df = df[DOCENTES_COLS]
        df = df.fillna("")
        return df
    return pd.DataFrame(columns=DOCENTES_COLS)


def salvar_docentes(df):
    """Salva a planilha de docentes."""
    os.makedirs("dados", exist_ok=True)
    df[DOCENTES_COLS].to_csv(DOCENTES_PATH, index=False, encoding='utf-8')


def carregar_coordenadores():
    """Carrega a planilha de coordenadores."""
    if os.path.exists(COORDENADORES_PATH):
        df = pd.read_csv(COORDENADORES_PATH, encoding='utf-8')
        if df.columns[0] == '' or df.columns[0].startswith('Unnamed'):
            df = df.drop(df.columns[0], axis=1)
        for col in ["CURSO", "SIGLA", "COORDENADOR"]:
            if col not in df.columns:
                df[col] = ""
        df = df[["CURSO", "SIGLA", "COORDENADOR"]].fillna("")
        return df
    return pd.DataFrame(columns=["CURSO", "SIGLA", "COORDENADOR"])


def salvar_coordenadores(df):
    """Salva a planilha de coordenadores."""
    os.makedirs("dados", exist_ok=True)
    df[["CURSO", "SIGLA", "COORDENADOR"]].to_csv(COORDENADORES_PATH, index=False, encoding='utf-8')


# ==================== CARREGAMENTO INICIAL ====================
df_docentes = carregar_docentes()
df_coordenadores = carregar_coordenadores()

# Título
st.title("👨‍🏫 Docentes e Coordenadores")

# ==================== MÉTRICAS ====================
coord_curso_map = {}
for _, row in df_coordenadores.iterrows():
    if str(row['COORDENADOR']).strip():
        coord_curso_map[str(row['COORDENADOR']).strip().upper()] = str(row['CURSO']).strip()

df_display = df_docentes.copy()
df_display['Coordenação'] = df_display['Docente'].apply(
    lambda n: coord_curso_map.get(str(n).strip().upper(), "")
)

total_docentes = len(df_display[df_display['Situação'] != ''])
ativos = len(df_display[df_display['Situação'] == 'Ativo'])
total_coordenadores = len(df_display[df_display['Coordenação'] != ''])

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total de Docentes", total_docentes)
with col2:
    st.metric("Docentes Ativos", ativos)
with col3:
    st.metric("Coordenadores", total_coordenadores)

st.markdown("---")

# ==================== SEÇÃO 1: REGISTRO DE NOVO DOCENTE ====================
with st.expander("✍️ Registrar Novo Docente", expanded=False):
    with st.form("novo_docente_form", clear_on_submit=True):
        st.subheader("Dados do Docente")

        col_a, col_b = st.columns(2)
        with col_a:
            nome_docente = st.text_input("Nome completo *")
            siape = st.text_input("SIAPE")
            email = st.text_input("E-mail institucional")
        with col_b:
            area = st.selectbox("Área *", options=AREAS_OPCOES, index=None, placeholder="Selecione...")
            coordenadoria = st.selectbox("Coordenadoria", options=COORDENADORIA_OPCOES, index=None, placeholder="Selecione...")
            situacao = st.selectbox("Situação *", options=SITUACAO_OPCOES, index=0)

        col_chk1, col_chk2 = st.columns(2)
        with col_chk1:
            colegiado = st.checkbox("Membro do Colegiado", value=False)
        with col_chk2:
            nde = st.checkbox("Membro do NDE", value=False)

        submitted = st.form_submit_button("➕ Registrar Docente", type="primary")

        if submitted:
            if not nome_docente.strip():
                st.error("O nome do docente é obrigatório.")
            elif not area:
                st.error("A área é obrigatória.")
            elif nome_docente.strip().upper() in df_docentes['Docente'].str.strip().str.upper().values:
                st.error(f"O docente '{nome_docente.strip()}' já está cadastrado.")
            else:
                novo = pd.DataFrame([{
                    "Docente": nome_docente.strip(),
                    "SIAPE": siape.strip(),
                    "Colegiado": str(colegiado).upper(),
                    "NDE": str(nde).upper(),
                    "Email": email.strip(),
                    "Coordenadoria": coordenadoria or "",
                    "Área": area,
                    "Situação": situacao,
                }])
                df_docentes = pd.concat([df_docentes, novo], ignore_index=True)
                salvar_docentes(df_docentes)
                st.success(f"✅ Docente '{nome_docente.strip()}' registrado com sucesso!")
                st.rerun()

# ==================== SEÇÃO 2: EDIÇÃO E EXCLUSÃO ====================
with st.expander("✏️ Editar / Excluir Docente", expanded=False):
    if df_docentes.empty:
        st.info("Nenhum docente cadastrado.")
    else:
        nomes_docentes = df_docentes['Docente'].dropna().tolist()
        docente_sel = st.selectbox(
            "Selecione o docente para editar",
            options=nomes_docentes,
            index=None,
            placeholder="Selecione um docente...",
            key="edit_docente_select"
        )

        if docente_sel:
            idx = df_docentes[df_docentes['Docente'] == docente_sel].index[0]
            row = df_docentes.loc[idx]

            with st.form("editar_docente_form"):
                st.subheader(f"Editando: {docente_sel}")

                col_a, col_b = st.columns(2)
                with col_a:
                    ed_nome = st.text_input("Nome completo", value=str(row['Docente']))
                    ed_siape = st.text_input("SIAPE", value=str(row['SIAPE']) if row['SIAPE'] else "")
                    ed_email = st.text_input("E-mail", value=str(row['Email']) if row['Email'] else "")
                with col_b:
                    ed_area_idx = AREAS_OPCOES.index(row['Área']) if row['Área'] in AREAS_OPCOES else None
                    ed_area = st.selectbox("Área", options=AREAS_OPCOES, index=ed_area_idx, placeholder="Selecione...")

                    ed_coord_idx = COORDENADORIA_OPCOES.index(row['Coordenadoria']) if row['Coordenadoria'] in COORDENADORIA_OPCOES else None
                    ed_coordenadoria = st.selectbox("Coordenadoria", options=COORDENADORIA_OPCOES, index=ed_coord_idx, placeholder="Selecione...")

                    ed_sit_idx = SITUACAO_OPCOES.index(row['Situação']) if row['Situação'] in SITUACAO_OPCOES else 0
                    ed_situacao = st.selectbox("Situação", options=SITUACAO_OPCOES, index=ed_sit_idx)

                col_chk1, col_chk2 = st.columns(2)
                with col_chk1:
                    ed_colegiado = st.checkbox("Membro do Colegiado", value=(str(row['Colegiado']).upper() == 'TRUE'))
                with col_chk2:
                    ed_nde = st.checkbox("Membro do NDE", value=(str(row['NDE']).upper() == 'TRUE'))

                col_save, col_delete = st.columns(2)
                with col_save:
                    salvar_edicao = st.form_submit_button("💾 Salvar Alterações", type="primary")
                with col_delete:
                    excluir = st.form_submit_button("🗑️ Excluir Docente", type="secondary")

                if salvar_edicao:
                    df_docentes.loc[idx, 'Docente'] = ed_nome.strip()
                    df_docentes.loc[idx, 'SIAPE'] = ed_siape.strip()
                    df_docentes.loc[idx, 'Email'] = ed_email.strip()
                    df_docentes.loc[idx, 'Área'] = ed_area or ""
                    df_docentes.loc[idx, 'Coordenadoria'] = ed_coordenadoria or ""
                    df_docentes.loc[idx, 'Situação'] = ed_situacao
                    df_docentes.loc[idx, 'Colegiado'] = str(ed_colegiado).upper()
                    df_docentes.loc[idx, 'NDE'] = str(ed_nde).upper()
                    salvar_docentes(df_docentes)
                    # Se o nome mudou, atualizar coordenadores
                    if docente_sel != ed_nome.strip():
                        mask = df_coordenadores['COORDENADOR'].str.strip().str.upper() == docente_sel.strip().upper()
                        if mask.any():
                            df_coordenadores.loc[mask, 'COORDENADOR'] = ed_nome.strip().upper()
                            salvar_coordenadores(df_coordenadores)
                    st.success("✅ Alterações salvas!")
                    st.rerun()

                if excluir:
                    nome_upper = docente_sel.strip().upper()
                    eh_coordenador = nome_upper in df_coordenadores['COORDENADOR'].str.strip().str.upper().values
                    if eh_coordenador:
                        st.error("⚠️ Este docente é coordenador de um curso. Remova a coordenação primeiro.")
                    else:
                        df_docentes = df_docentes.drop(idx).reset_index(drop=True)
                        salvar_docentes(df_docentes)
                        st.success(f"🗑️ Docente '{docente_sel}' excluído.")
                        st.rerun()

# ==================== SEÇÃO 3: GERENCIAR COORDENADORES ====================
with st.expander("🎓 Gerenciar Coordenadores", expanded=False):
    st.subheader("Coordenadores por Curso")
    st.caption("Selecione entre os docentes ativos quem coordena cada curso.")

    docentes_ativos = df_docentes[df_docentes['Situação'] == 'Ativo']['Docente'].dropna().sort_values().tolist()
    docentes_opcoes = ["(nenhum)"] + docentes_ativos

    with st.form("coordenadores_form"):
        coordenadores_novos = {}
        for sigla, curso_nome in sorted(CURSOS_SIGLA.items(), key=lambda x: x[1]):
            coord_atual = ""
            mask = df_coordenadores['SIGLA'].str.strip() == sigla
            if mask.any():
                coord_atual = str(df_coordenadores.loc[mask, 'COORDENADOR'].values[0]).strip()

            idx_sel = 0  # "(nenhum)"
            for i, nome in enumerate(docentes_opcoes):
                if nome.strip().upper() == coord_atual.upper():
                    idx_sel = i
                    break

            coordenadores_novos[sigla] = st.selectbox(
                f"{curso_nome} ({sigla})",
                options=docentes_opcoes,
                index=idx_sel,
                key=f"coord_{sigla}"
            )

        salvar_coords = st.form_submit_button("💾 Salvar Coordenadores", type="primary")

        if salvar_coords:
            novos_rows = []
            for sigla, curso_nome in sorted(CURSOS_SIGLA.items(), key=lambda x: x[1]):
                coord = coordenadores_novos.get(sigla, "(nenhum)")
                coord_nome = "" if coord == "(nenhum)" else coord.strip().upper()
                novos_rows.append({
                    "CURSO": curso_nome,
                    "SIGLA": sigla,
                    "COORDENADOR": coord_nome,
                })
            df_coordenadores = pd.DataFrame(novos_rows)
            salvar_coordenadores(df_coordenadores)
            st.success("✅ Coordenadores atualizados!")
            st.rerun()

    if not df_coordenadores.empty:
        st.markdown("**Situação atual:**")
        df_coord_display = df_coordenadores[df_coordenadores['COORDENADOR'].str.strip() != ''].copy()
        if not df_coord_display.empty:
            st.dataframe(df_coord_display, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhum coordenador atribuído.")

st.markdown("---")

# ==================== SEÇÃO 4: LISTAGEM COM FILTROS ====================
st.markdown("### 📋 Listagem de Docentes")

# Recarrega para refletir edições recentes
df_docentes = carregar_docentes()
df_coordenadores = carregar_coordenadores()

coord_curso_map = {}
for _, row in df_coordenadores.iterrows():
    if str(row['COORDENADOR']).strip():
        coord_curso_map[str(row['COORDENADOR']).strip().upper()] = str(row['CURSO']).strip()

df_display = df_docentes.copy()
df_display['Coordenação'] = df_display['Docente'].apply(
    lambda n: coord_curso_map.get(str(n).strip().upper(), "")
)

col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns(4)
with col_filtro1:
    situacao_filtro = st.multiselect(
        "Filtrar por Situação:",
        options=df_display['Situação'].dropna().unique().tolist(),
        default=[]
    )
with col_filtro2:
    area_filtro = st.multiselect(
        "Filtrar por Área:",
        options=sorted(df_display['Área'].dropna().unique().tolist()),
        default=[]
    )
with col_filtro3:
    coord_filtro = st.multiselect(
        "Filtrar por Coordenadoria:",
        options=sorted(df_display['Coordenadoria'].dropna().unique().tolist()),
        default=[]
    )
with col_filtro4:
    colegiado_filtro = st.selectbox(
        "Membro do Colegiado:",
        options=["Todos", "Sim", "Não"],
        index=0
    )

df_filtrado = df_display.copy()
if situacao_filtro:
    df_filtrado = df_filtrado[df_filtrado['Situação'].isin(situacao_filtro)]
if area_filtro:
    df_filtrado = df_filtrado[df_filtrado['Área'].isin(area_filtro)]
if coord_filtro:
    df_filtrado = df_filtrado[df_filtrado['Coordenadoria'].isin(coord_filtro)]
if colegiado_filtro == "Sim":
    df_filtrado = df_filtrado[df_filtrado['Colegiado'].astype(str).str.strip().str.lower() == 'true']
elif colegiado_filtro == "Não":
    df_filtrado = df_filtrado[df_filtrado['Colegiado'].astype(str).str.strip().str.lower() == 'false']

st.markdown(f"**{len(df_filtrado)} docentes encontrados**")
st.dataframe(
    df_filtrado[['Docente', 'SIAPE', 'Área', 'Coordenadoria', 'Situação', 'Coordenação']],
    hide_index=True,
    use_container_width=True,
    column_config={
        "Docente": st.column_config.TextColumn("Nome", width="large"),
        "SIAPE": st.column_config.TextColumn("SIAPE", width="small"),
        "Área": st.column_config.TextColumn("Área", width="small"),
        "Coordenadoria": st.column_config.TextColumn("Coord.", width="small"),
        "Situação": st.column_config.TextColumn("Situação", width="small"),
        "Coordenação": st.column_config.TextColumn("Coordenador de", width="medium"),
    }
)

csv_export = df_filtrado.to_csv(index=False, encoding='utf-8-sig')
st.download_button(
    label="📥 Baixar listagem (CSV)",
    data=csv_export,
    file_name="listagem_docentes.csv",
    mime="text/csv",
)

# ==================== SEÇÃO 5: EMITIR PORTARIA ====================
st.markdown("---")
st.markdown("### 📄 Portaria do Colegiado")

from datetime import datetime as _dt

_ano = _dt.now().year
_semestre_atual = f"{_ano}.{1 if _dt.now().month <= 6 else 2}"

# Coordenador da Engenharia Elétrica
_coord_ee = ""
if not df_coordenadores.empty:
    _row_ee = df_coordenadores[df_coordenadores['SIGLA'].str.strip() == 'EE']
    if not _row_ee.empty:
        _coord_ee = str(_row_ee.iloc[0]['COORDENADOR']).strip()

# Membros docentes do colegiado
_membros = df_docentes[df_docentes['Colegiado'].astype(str).str.strip().str.lower() == 'true']['Docente'].tolist()

_linhas_membros = "\n".join(f"    - {nome.strip().upper()}" for nome in sorted(_membros))

# Representantes discentes
_REPR_PATH = os.path.join("dados", "representantes_turma.csv")
_linhas_discentes = ""
if os.path.exists(_REPR_PATH):
    _df_repr = pd.read_csv(_REPR_PATH, dtype=str).fillna("")
    _df_repr = _df_repr[_df_repr['semestre'] == _semestre_atual]
    _df_repr['_fase_num'] = _df_repr['fase'].astype(int)
    _df_repr = _df_repr.sort_values('_fase_num')
    _repr_list = []
    for _, _r in _df_repr.iterrows():
        if _r['representante']:
            _repr_list.append(f"    - {_r['representante'].upper()} (Representante - {_r['fase']}ª fase)")
        if _r['vice']:
            _repr_list.append(f"    - {_r['vice'].upper()} (Vice-representante - {_r['fase']}ª fase)")
    _linhas_discentes = "\n".join(_repr_list)

_texto_portaria = (
    f"Designar os servidores e discentes abaixo relacionados para comporem o Colegiado "
    f"do Curso de Bacharelado em Engenharia Elétrica, semestre {_semestre_atual}, "
    f"do Câmpus Jaraguá do Sul-Rau:\n\n"
    f"I) Presidente: {_coord_ee.upper()} - Coordenador do Curso de Engenharia Elétrica;\n\n"
    f"II) Membro Técnico em Assuntos Educacionais (Pedagoga): VIVIAN CAROLINE FERNANDES IZIQUIEL;\n\n"
    f"III) Membros Docentes:\n{_linhas_membros}\n\n"
    f"IV) Representantes Discentes:\n{_linhas_discentes}\n"
)

st.text_area("Prévia da portaria:", value=_texto_portaria, height=300, disabled=True)

_emails_colegiado = df_docentes[
    df_docentes['Colegiado'].astype(str).str.strip().str.lower() == 'true'
]['Email'].dropna().tolist()
_emails_colegiado = [e.strip() for e in _emails_colegiado if str(e).strip()]
_emails_str = "; ".join(sorted(_emails_colegiado))

import streamlit.components.v1 as components

_col_portaria, _col_emails = st.columns(2)
with _col_portaria:
    st.download_button(
        label="📄 Emitir Portaria (TXT)",
        data=_texto_portaria.encode('utf-8'),
        file_name=f"portaria_colegiado_{_semestre_atual}.txt",
        mime="text/plain",
    )
with _col_emails:
    _btn_html = f"""
    <button onclick="navigator.clipboard.writeText('{_emails_str}').then(() => {{
        const el = document.getElementById('copy-msg');
        el.style.display = 'inline';
        setTimeout(() => el.style.display = 'none', 2000);
    }})"
    style="background-color:#0068c9;color:white;border:none;padding:8px 20px;
    border-radius:6px;cursor:pointer;font-size:14px;">
    📧 Copiar e-mails do Colegiado ({len(_emails_colegiado)})
    </button>
    <span id="copy-msg" style="display:none;margin-left:10px;color:#27ae60;font-size:14px;">
    ✅ Copiado!
    </span>
    """
    components.html(_btn_html, height=50)

# ==================== SEÇÃO 6: PORTARIA DO NDE ====================
st.markdown("---")
st.markdown("### 📄 Portaria do NDE")

_membros_nde = df_docentes[df_docentes['NDE'].astype(str).str.strip().str.lower() == 'true']['Docente'].tolist()
_linhas_membros_nde = "\n".join(f"    - {nome.strip().upper()}" for nome in sorted(_membros_nde))

_texto_portaria_nde = (
    f"Designar os servidores abaixo relacionados para comporem o Núcleo Docente "
    f"Estruturante (NDE) do Curso de Bacharelado em Engenharia Elétrica, "
    f"semestre {_semestre_atual}, do Câmpus Jaraguá do Sul-Rau:\n\n"
    f"I) Presidente: {_coord_ee.upper()} - Coordenador do Curso de Engenharia Elétrica;\n\n"
    f"II) Membros Docentes:\n{_linhas_membros_nde}\n"
)

st.text_area("Prévia da portaria:", value=_texto_portaria_nde, height=250, disabled=True, key="portaria_nde")

_emails_nde = df_docentes[
    df_docentes['NDE'].astype(str).str.strip().str.lower() == 'true'
]['Email'].dropna().tolist()
_emails_nde = [e.strip() for e in _emails_nde if str(e).strip()]
_emails_nde_str = "; ".join(sorted(_emails_nde))

_col_portaria_nde, _col_emails_nde = st.columns(2)
with _col_portaria_nde:
    st.download_button(
        label="📄 Emitir Portaria NDE (TXT)",
        data=_texto_portaria_nde.encode('utf-8'),
        file_name=f"portaria_nde_{_semestre_atual}.txt",
        mime="text/plain",
    )
with _col_emails_nde:
    _btn_html_nde = f"""
    <button onclick="navigator.clipboard.writeText('{_emails_nde_str}').then(() => {{
        const el = document.getElementById('copy-msg-nde');
        el.style.display = 'inline';
        setTimeout(() => el.style.display = 'none', 2000);
    }})"
    style="background-color:#0068c9;color:white;border:none;padding:8px 20px;
    border-radius:6px;cursor:pointer;font-size:14px;">
    📧 Copiar e-mails do NDE ({len(_emails_nde)})
    </button>
    <span id="copy-msg-nde" style="display:none;margin-left:10px;color:#27ae60;font-size:14px;">
    ✅ Copiado!
    </span>
    """
    components.html(_btn_html_nde, height=50)
