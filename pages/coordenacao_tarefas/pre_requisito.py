import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
from utils import setup_sidebar_header, construir_disciplinas_cod_nome
from data.disciplinas import NOMES

# Configuração da página
st.set_page_config(
    page_title="Controle de Pré-Requisitos",
    page_icon="🔗",
    layout="wide"
)

# Verificação de acesso
if 'arquivo_carregado' not in st.session_state or not st.session_state.arquivo_carregado:
    setup_sidebar_header()
    st.error("⚠️ Por favor, faça o upload do arquivo na página inicial primeiro! Volte para Home.")
    st.stop()

# Sidebar
setup_sidebar_header()

# Título principal
st.header("🔗 Quebra de Pré-Requisitos")

# ==================== CONFIGURAÇÃO DA PLANILHA DE SOLICITAÇÕES ====================
FILE_PATH = os.path.join("dados", "solicitacoes_prerequisito.csv")
COLUMNS = [
    "data_solicitacao",
    "matricula",
    "estudante",
    "codigo_disciplina",
    "disciplina_solicitada",
    "disciplinas_prerequisito",   # disciplinas pré-requisito (separadas por ;)
    "semestre",
    "justificativa",
    "parecer_coordenacao",
    "status",
    "data_parecer",
    "memorando_enviado",          # "" ou data de envio do memorando
]

def carregar_solicitacoes():
    """Carrega a planilha de solicitações de pré-requisitos."""
    if os.path.exists(FILE_PATH):
        df = pd.read_csv(FILE_PATH)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df
    else:
        return pd.DataFrame(columns=COLUMNS)

def salvar_solicitacoes(df):
    """Salva a planilha de solicitações de pré-requisitos."""
    df.to_csv(FILE_PATH, index=False)

# Carrega solicitações já registradas
df_solicitacoes = carregar_solicitacoes()

# Recupera dados do arquivo de upload (sessão) para preencher o formulário
df_principal = st.session_state.df
alunos_list = df_principal[['Matricula', 'Aluno']].drop_duplicates().sort_values('Aluno')

# Lista de disciplinas no formato padronizado 'COD - Nome'
disciplinas_list, disciplinas_cod_nome, _mapa_sigaa, _mapa_parts = construir_disciplinas_cod_nome(df_principal)

# Mapa de pré-requisitos a partir da matriz curricular
def _carregar_mapa_prerequisitos():
    json_path = os.path.join("data", "matriz.json")
    if not os.path.exists(json_path):
        return {}
    with open(json_path, encoding="utf-8") as f:
        dados = json.load(f)
    mapa = {}
    for disciplinas in dados.values():
        for cod, info in disciplinas.items():
            deps = list(info.get("pre", [])) + list(info.get("co", []))
            if deps:
                mapa[cod] = deps
    return mapa

_mapa_prerequisitos = _carregar_mapa_prerequisitos()

# ==================== SEÇÃO 1: NOVA SOLICITAÇÃO ====================
@st.dialog("📝 Registrar Nova Solicitação de Quebra de Pré-Requisito", width="large")
def _dialog_registrar_prereq():
    df_solicitacoes = carregar_solicitacoes()

    st.subheader("Dados da Solicitação")

    col1, col2 = st.columns(2)

    with col1:
        aluno_selecionado = st.selectbox(
            "Selecione o Estudante",
            options=alunos_list['Aluno'],
            index=None,
            placeholder="Selecione um estudante..."
        )

    with col2:
        ano_atual = datetime.now().year
        semestres_opcoes = []
        for ano in range(ano_atual - 2, ano_atual + 3):
            semestres_opcoes.append(f"{ano}.1")
            semestres_opcoes.append(f"{ano}.2")
        semestre_atual_default = f"{ano_atual}.{1 if datetime.now().month <= 6 else 2}"
        semestre_atual = st.selectbox(
            "Semestre",
            options=semestres_opcoes,
            index=semestres_opcoes.index(semestre_atual_default) if semestre_atual_default in semestres_opcoes else 0
        )

    st.markdown("---")
    st.markdown("**Disciplinas envolvidas na quebra de pré-requisito:**")

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        disciplina_matricula_cod_nome = st.selectbox(
            "Disciplina que deseja matricular-se",
            options=disciplinas_cod_nome,
            index=None,
            placeholder="Selecione a disciplina..."
        )

    # Filtra pré-requisitos conforme a disciplina selecionada
    prereqs_options = []
    if disciplina_matricula_cod_nome:
        parts_disc = _mapa_parts.get(disciplina_matricula_cod_nome)
        cod_disc = parts_disc[0] if parts_disc else ''
        prereqs_codes = _mapa_prerequisitos.get(cod_disc, [])
        prereqs_options = [f"{c} - {NOMES.get(c, c)}" for c in prereqs_codes]

    with col_d2:
        disciplinas_prerequisito_cod_nome = st.multiselect(
            "Disciplinas de pré-requisito (não cursadas)",
            options=prereqs_options,
            placeholder="Selecione as disciplinas de pré-requisito..." if prereqs_options else "Selecione primeiro a disciplina..."
        )

    justificativa = st.text_area("Justificativa do Estudante", height=150)

    submit_button = st.button("✔️ Enviar Solicitação", type="primary", use_container_width=True)

    if submit_button:
        campos_validos = aluno_selecionado and disciplina_matricula_cod_nome and disciplinas_prerequisito_cod_nome and justificativa and semestre_atual

        if not campos_validos:
            st.warning("Os campos 'Estudante', 'Disciplina para matrícula', 'Disciplinas de pré-requisito', 'Justificativa' e 'Semestre' são obrigatórios!")
        else:
            try:
                matricula = alunos_list[alunos_list['Aluno'] == aluno_selecionado]['Matricula'].iloc[0]
                agora = datetime.now().strftime("%Y-%m-%d %H:%M")

                # Extrai código e nome da disciplina de matrícula
                parts = _mapa_parts.get(disciplina_matricula_cod_nome)
                if parts:
                    codigo, disciplina_matricula = parts
                elif disciplina_matricula_cod_nome and ' - ' in disciplina_matricula_cod_nome:
                    codigo, disciplina_matricula = disciplina_matricula_cod_nome.split(' - ', 1)
                else:
                    codigo, disciplina_matricula = '', disciplina_matricula_cod_nome

                # Extrai nomes das disciplinas de pré-requisito
                disciplinas_prerequisito_nomes = []
                for d in disciplinas_prerequisito_cod_nome:
                    p = _mapa_parts.get(d)
                    if p:
                        disciplinas_prerequisito_nomes.append(p[1])
                    elif ' - ' in d:
                        _, nome = d.split(' - ', 1)
                        disciplinas_prerequisito_nomes.append(nome)
                    else:
                        disciplinas_prerequisito_nomes.append(d)

                prereqs_str = "; ".join(disciplinas_prerequisito_nomes)

                nova_linha = {
                    "data_solicitacao": agora,
                    "matricula": matricula,
                    "estudante": aluno_selecionado,
                    "codigo_disciplina": codigo,
                    "disciplina_solicitada": disciplina_matricula,
                    "disciplinas_prerequisito": prereqs_str,
                    "semestre": semestre_atual,
                    "justificativa": justificativa,
                    "parecer_coordenacao": "",
                    "status": "Pendente",
                    "data_parecer": "",
                    "memorando_enviado": "",
                }

                df_solicitacoes = pd.concat([df_solicitacoes, pd.DataFrame([nova_linha])], ignore_index=True)
                salvar_solicitacoes(df_solicitacoes)

                st.success(
                    f"Solicitação de quebra de pré-requisito para **{aluno_selecionado}** registrada com sucesso!\n\n"
                    f"**Disciplina:** {disciplina_matricula}\n\n"
                    f"**Pré-requisitos:** {prereqs_str}"
                )
                st.rerun()
            except Exception as e:
                st.error(f"Ocorreu um erro ao salvar a solicitação: {e}")

# ==================== SEÇÃO 2: AVALIAR SOLICITAÇÃO ====================
@st.dialog("✏️ Avaliar Solicitação de Quebra de Pré-Requisito", width="large")
def _dialog_avaliar_prereq():
    df_solicitacoes = carregar_solicitacoes()
    solicitacoes_pendentes = df_solicitacoes[df_solicitacoes['status'] == 'Pendente']

    if not solicitacoes_pendentes.empty:
        solicitacoes_options = {
            f"{row['estudante']} — {row['disciplina_solicitada']} ({row['data_solicitacao']})": index
            for index, row in solicitacoes_pendentes.iterrows()
        }

        selecao = st.selectbox(
            "Selecione a Solicitação Pendente para Avaliar",
            options=solicitacoes_options.keys(),
            index=None,
            placeholder="Selecione uma solicitação..."
        )

        if selecao:
            index_selecionado = solicitacoes_options[selecao]
            solicitacao_selecionada = df_solicitacoes.loc[index_selecionado]

            # Exibe informações detalhadas
            st.info(f"**Disciplina Solicitada para Matrícula:** {solicitacao_selecionada['disciplina_solicitada']}")

            prereqs_val = solicitacao_selecionada.get('disciplinas_prerequisito', '')
            if prereqs_val and str(prereqs_val).strip() and str(prereqs_val) != 'nan':
                st.info(f"**Disciplinas de Pré-Requisito (não cursadas):** {prereqs_val}")

            justif = solicitacao_selecionada.get('justificativa', '')
            if justif:
                st.info(f"**Justificativa do Estudante:**\n\n{justif}")

            with st.form("update_status_prereq_form"):
                novo_status = st.selectbox("Novo Status", ["Deferido", "Indeferido"])
                parecer = st.text_area("Parecer da Coordenação")

                update_button = st.form_submit_button("Salvar Parecer")

                if update_button:
                    if not parecer:
                        st.warning("O campo 'Parecer da Coordenação' é obrigatório.")
                    else:
                        df_solicitacoes.loc[index_selecionado, 'status'] = novo_status
                        df_solicitacoes.loc[index_selecionado, 'parecer_coordenacao'] = parecer
                        df_solicitacoes.loc[index_selecionado, 'data_parecer'] = datetime.now().strftime("%Y-%m-%d %H:%M")

                        salvar_solicitacoes(df_solicitacoes)
                        st.success("Parecer registrado e status atualizado com sucesso!")
                        st.rerun()
    else:
        st.info("Não há solicitações com status 'Pendente' para avaliar.")

# ==================== SEÇÃO 2B: EDITAR / EXCLUIR SOLICITAÇÃO ====================
@st.dialog("🔧 Editar / Excluir Solicitação de Quebra de Pré-Requisito", width="large")
def _dialog_editar_prereq():
    df_solicitacoes = carregar_solicitacoes()
    if df_solicitacoes.empty:
        st.info("Nenhuma solicitação registrada para editar ou excluir.")
    else:
        todas_options = {
            f"{row['estudante']} — {row['disciplina_solicitada']} ({row['data_solicitacao']}) [{row['status']}]": index
            for index, row in df_solicitacoes.iterrows()
        }

        selecao_editar = st.selectbox(
            "Selecione a Solicitação para Editar/Excluir",
            options=todas_options.keys(),
            index=None,
            placeholder="Selecione uma solicitação...",
            key="sel_editar_prereq"
        )

        if selecao_editar:
            idx_editar = todas_options[selecao_editar]
            sol_editar = df_solicitacoes.loc[idx_editar]

            tab_editar, tab_excluir = st.tabs(["✏️ Editar", "🗑️ Excluir"])

            with tab_editar:
                st.subheader("Editar Dados da Solicitação")

                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    aluno_edit = st.selectbox(
                        "Estudante",
                        options=alunos_list['Aluno'].tolist(),
                        index=alunos_list['Aluno'].tolist().index(sol_editar['estudante'])
                            if sol_editar['estudante'] in alunos_list['Aluno'].tolist() else 0,
                        key="edit_aluno_prereq"
                    )
                with col_e2:
                    # Tenta encontrar o índice da disciplina salva na lista cod_nome
                    _disc_salva = sol_editar['disciplina_solicitada']
                    _cod_salvo = str(sol_editar.get('codigo_disciplina', ''))
                    _idx_disc = 0
                    # Busca pelo código da disciplina ou pelo nome
                    for _di, _item in enumerate(disciplinas_cod_nome):
                        p = _mapa_parts.get(_item, ('', ''))
                        if (p[0] and p[0] == _cod_salvo) or (p[1] == _disc_salva) or (_disc_salva in _item):
                            _idx_disc = _di
                            break
                    disc_edit = st.selectbox(
                        "Disciplina Solicitada para Matrícula",
                        options=disciplinas_cod_nome,
                        index=_idx_disc,
                        key="edit_disc_prereq"
                    )

                # Filtra pré-requisitos conforme a disciplina selecionada
                prereqs_edit_options = []
                if disc_edit:
                    parts_disc_edit = _mapa_parts.get(disc_edit)
                    cod_disc_edit = parts_disc_edit[0] if parts_disc_edit else ''
                    prereqs_codes_edit = _mapa_prerequisitos.get(cod_disc_edit, [])
                    prereqs_edit_options = [f"{c} - {NOMES.get(c, c)}" for c in prereqs_codes_edit]

                # Determina defaults que existem nas opções filtradas
                prereqs_atual = str(sol_editar.get('disciplinas_prerequisito', ''))
                prereqs_default = []
                if prereqs_atual and prereqs_atual != 'nan':
                    for p_nome in prereqs_atual.split(';'):
                        p_nome = p_nome.strip()
                        for _item in prereqs_edit_options:
                            pp = _mapa_parts.get(_item, ('', ''))
                            if pp[1] == p_nome or p_nome in _item:
                                prereqs_default.append(_item)
                                break

                prereqs_edit = st.multiselect(
                    "Disciplinas de Pré-Requisito (não cursadas)",
                    options=prereqs_edit_options,
                    default=prereqs_default,
                    placeholder="Selecione as disciplinas de pré-requisito..." if prereqs_edit_options else "Selecione primeiro a disciplina...",
                    key="edit_prereqs_prereq"
                )

                col_e3, col_e4 = st.columns(2)
                with col_e3:
                    ano_atual_e = datetime.now().year
                    semestres_e = []
                    for ano in range(ano_atual_e - 2, ano_atual_e + 3):
                        semestres_e.append(f"{ano}.1")
                        semestres_e.append(f"{ano}.2")
                    sem_val = str(sol_editar['semestre'])
                    sem_idx = semestres_e.index(sem_val) if sem_val in semestres_e else 0
                    semestre_edit = st.selectbox("Semestre", options=semestres_e, index=sem_idx, key="edit_sem_prereq")

                with col_e4:
                    STATUS_OPCOES_EDIT = ["Pendente", "Deferido", "Indeferido"]
                    status_val = str(sol_editar['status']) if pd.notna(sol_editar['status']) else "Pendente"
                    status_idx = STATUS_OPCOES_EDIT.index(status_val) if status_val in STATUS_OPCOES_EDIT else 0
                    status_edit = st.selectbox("Status", options=STATUS_OPCOES_EDIT, index=status_idx, key="edit_status_prereq")

                justif_edit = st.text_area(
                    "Justificativa",
                    value=str(sol_editar['justificativa']) if pd.notna(sol_editar['justificativa']) else "",
                    key="edit_justif_prereq"
                )
                parecer_edit = st.text_area(
                    "Parecer da Coordenação",
                    value=str(sol_editar['parecer_coordenacao']) if pd.notna(sol_editar['parecer_coordenacao']) else "",
                    key="edit_parecer_prereq"
                )

                btn_salvar_edit = st.button("💾 Salvar Alterações", type="primary", use_container_width=True, key="btn_salvar_edit_prereq")

                if btn_salvar_edit:
                    try:
                        matricula_edit = alunos_list[alunos_list['Aluno'] == aluno_edit]['Matricula'].iloc[0]

                        # Extrai código e nome da disciplina selecionada
                        parts_edit = _mapa_parts.get(disc_edit)
                        if parts_edit:
                            codigo_edit, nome_edit = parts_edit
                        elif ' - ' in disc_edit:
                            codigo_edit, nome_edit = disc_edit.split(' - ', 1)
                        else:
                            codigo_edit, nome_edit = '', disc_edit

                        # Extrai nomes dos pré-requisitos selecionados
                        prereqs_nomes_edit = []
                        for pr in prereqs_edit:
                            pp = _mapa_parts.get(pr)
                            if pp:
                                prereqs_nomes_edit.append(pp[1])
                            elif ' - ' in pr:
                                prereqs_nomes_edit.append(pr.split(' - ', 1)[1])
                            else:
                                prereqs_nomes_edit.append(pr)

                        df_solicitacoes.loc[idx_editar, 'estudante'] = aluno_edit
                        df_solicitacoes.loc[idx_editar, 'matricula'] = matricula_edit
                        df_solicitacoes.loc[idx_editar, 'disciplina_solicitada'] = nome_edit
                        df_solicitacoes.loc[idx_editar, 'codigo_disciplina'] = codigo_edit
                        df_solicitacoes.loc[idx_editar, 'disciplinas_prerequisito'] = "; ".join(prereqs_nomes_edit)
                        df_solicitacoes.loc[idx_editar, 'semestre'] = semestre_edit
                        df_solicitacoes.loc[idx_editar, 'justificativa'] = justif_edit
                        df_solicitacoes.loc[idx_editar, 'parecer_coordenacao'] = parecer_edit
                        df_solicitacoes.loc[idx_editar, 'status'] = status_edit
                        if status_edit != "Pendente" and (pd.isna(sol_editar['data_parecer']) or str(sol_editar['data_parecer']).strip() == ""):
                            df_solicitacoes.loc[idx_editar, 'data_parecer'] = datetime.now().strftime("%Y-%m-%d %H:%M")

                        salvar_solicitacoes(df_solicitacoes)
                        st.success("Solicitação atualizada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar alterações: {e}")

            with tab_excluir:
                st.warning(
                    f"⚠️ Tem certeza que deseja **excluir** a solicitação de "
                    f"**{sol_editar['estudante']}** para a disciplina "
                    f"**{sol_editar['disciplina_solicitada']}**?"
                )
                st.caption("Esta ação não poderá ser desfeita.")

                if st.button("🗑️ Confirmar Exclusão", type="primary", key="btn_excluir_prereq"):
                    df_solicitacoes = df_solicitacoes.drop(index=idx_editar).reset_index(drop=True)
                    salvar_solicitacoes(df_solicitacoes)
                    st.success("Solicitação excluída com sucesso!")
                    st.rerun()

# ==================== BOTÕES DE AÇÃO ====================
col_act_1, col_act_2, col_act_3 = st.columns(3)
with col_act_1:
    if st.button("📝 Registrar Nova Solicitação", use_container_width=True):
        _dialog_registrar_prereq()
with col_act_2:
    if st.button("✏️ Avaliar Solicitação", use_container_width=True):
        _dialog_avaliar_prereq()
with col_act_3:
    if st.button("🔧 Editar / Excluir Solicitação", use_container_width=True):
        _dialog_editar_prereq()

# ==================== SEÇÃO 4: PAINEL DE CONTROLE ====================
st.header("🗂️ Consulta e Relatório das Solicitações")

if df_solicitacoes.empty:
    st.info("Nenhuma solicitação de quebra de pré-requisito registrada até o momento.")
else:
    # --- Filtros lado a lado: Semestre | Status | Estudante ---
    semestres_disponiveis = [str(s) for s in df_solicitacoes['semestre'].dropna().unique() if str(s).strip() != '']
    semestres_disponiveis = sorted(semestres_disponiveis, reverse=True)

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        semestre_selecionado = st.selectbox("Semestre", options=["Todos"] + semestres_disponiveis)
    with col_f2:
        STATUS_OPCOES = ["Pendente", "Deferido", "Indeferido"]
        status_filter = st.multiselect("Status", options=STATUS_OPCOES, default=["Pendente"])
    with col_f3:
        estudantes_opcoes = sorted(df_solicitacoes['estudante'].dropna().unique())
        aluno_filter = st.multiselect("Estudante", options=estudantes_opcoes)

    # Aplica filtros
    df_filtrado = df_solicitacoes.copy()
    if semestre_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['semestre'] == semestre_selecionado]
    if status_filter:
        df_filtrado = df_filtrado[df_filtrado['status'].isin(status_filter)]
    if aluno_filter:
        df_filtrado = df_filtrado[df_filtrado['estudante'].isin(aluno_filter)]

    # --- Tabela com rótulos amigáveis ---
    COLUNAS_EXIBICAO = {
        "data_solicitacao": "Data Solicitação",
        "matricula": "Matrícula",
        "estudante": "Estudante",
        "codigo_disciplina": "Código",
        "disciplina_solicitada": "Disciplina Solicitada",
        "disciplinas_prerequisito": "Pré-Requisitos",
        "semestre": "Semestre",
        "justificativa": "Justificativa",
        "parecer_coordenacao": "Parecer da Coordenação",
        "status": "Status",
        "data_parecer": "Data do Parecer",
    }

    st.write(f"Exibindo **{len(df_filtrado)}** de **{len(df_solicitacoes)}** solicitações.")

    # Remove coluna memorando_enviado da exibição (controle interno)
    cols_exibir = [c for c in COLUNAS_EXIBICAO.keys() if c in df_filtrado.columns]
    df_exibir = df_filtrado[cols_exibir].rename(columns=COLUNAS_EXIBICAO)
    st.dataframe(df_exibir.sort_values("Data Solicitação", ascending=False), use_container_width=True)

    # --- Relatório ---
    def gerar_relatorio_txt(df_relatorio):
        report_lines = []
        report_lines.append("RELATÓRIO DE QUEBRA DE PRÉ-REQUISITOS")
        report_lines.append(f"Semestre: {semestre_selecionado}")
        report_lines.append(f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        report_lines.append(f"Total de solicitações: {len(df_relatorio)}")
        report_lines.append("=" * 60)
        report_lines.append("")
        for _, row in df_relatorio.iterrows():
            report_lines.append("-" * 60)
            report_lines.append(f"ESTUDANTE: {row.get('estudante', 'N/A')}")
            report_lines.append(f"Matrícula: {row.get('matricula', 'N/A')}")
            codigo = row.get('codigo_disciplina', '')
            disc = row.get('disciplina_solicitada', 'N/A')
            report_lines.append(f"Disciplina Solicitada: {f'{codigo} - {disc}' if codigo else disc}")
            prereqs = row.get('disciplinas_prerequisito', '')
            report_lines.append(f"Pré-Requisitos: {prereqs if prereqs and str(prereqs) != 'nan' else 'Não informados'}")
            report_lines.append(f"Status: {row.get('status', 'N/A')}")
            report_lines.append(f"Data da Solicitação: {row.get('data_solicitacao', 'N/A')}")
            justif = row.get('justificativa', '')
            report_lines.append(f"Justificativa: {justif if justif else 'Não informada'}")
            parecer = row.get('parecer_coordenacao', '')
            report_lines.append(f"Parecer da Coordenação: {parecer if parecer else 'Aguardando parecer'}")
            data_p = row.get('data_parecer', '')
            report_lines.append(f"Data do Parecer: {data_p if data_p else 'Aguardando decisão'}")
            report_lines.append("")
        return "\n".join(report_lines)

    if not df_filtrado.empty:
        nome_arquivo = f"relatorio_pre_requisitos_{semestre_selecionado.replace('.', '_') if semestre_selecionado != 'Todos' else 'todos'}.txt"
        st.download_button(
            label="📥 Gerar Relatório em .txt",
            data=gerar_relatorio_txt(df_filtrado),
            file_name=nome_arquivo,
            mime="text/plain"
        )

# ==================== SEÇÃO 3: CASOS DEFERIDOS — PENDENTES DE MEMORANDO ====================
st.markdown("---")
st.subheader("⏳ Casos Deferidos — Pendentes de Memorando")

def _is_vazio_prereq(val):
    if pd.isna(val):
        return True
    return str(val).strip() == ""

df_deferidos_prereq = df_solicitacoes[df_solicitacoes['status'] == 'Deferido'].copy() if not df_solicitacoes.empty else pd.DataFrame()
mask_pendente_memo = df_deferidos_prereq['memorando_enviado'].apply(_is_vazio_prereq) if not df_deferidos_prereq.empty else pd.Series(dtype=bool)
df_pendentes_memo = df_deferidos_prereq[mask_pendente_memo].copy() if not df_deferidos_prereq.empty else pd.DataFrame()
df_enviados_memo = df_deferidos_prereq[~mask_pendente_memo].copy() if not df_deferidos_prereq.empty else pd.DataFrame()

if df_pendentes_memo.empty:
    st.success("Todos os casos deferidos já tiveram memorando enviado!")
else:
    st.write(f"**{len(df_pendentes_memo)}** caso(s) deferido(s) aguardando emissão de memorando.")

    if 'prereq_memo_sel' not in st.session_state:
        st.session_state.prereq_memo_sel = {}

    indices_sel_memo = []
    for idx, row in df_pendentes_memo.iterrows():
        label = (
            f"🔗 {row['estudante']} — "
            f"{row['codigo_disciplina']} {row['disciplina_solicitada']} "
            f"({row['semestre']})"
        )
        default_val = st.session_state.prereq_memo_sel.get(idx, False)
        sel = st.checkbox(label, value=default_val, key=f"prereq_memo_cb_{idx}")
        st.session_state.prereq_memo_sel[idx] = sel
        if sel:
            indices_sel_memo.append(idx)

    df_sel_memo = df_pendentes_memo.loc[df_pendentes_memo.index.isin(indices_sel_memo)]

    st.markdown("---")

    if not df_sel_memo.empty:
        def gerar_memorando_prereq(df_sel):
            lines = []
            lines.append("Quebra de Pré-Requisitos")
            lines.append("")
            lines.append(
                "Considerando as solicitações de quebra de pré-requisito protocoladas "
                "pelos estudantes e o respectivo deferimento pelo NDE ou Colegiado do Curso, "
                "solicita-se a efetivação da matrícula nas disciplinas correspondentes para "
                "os estudantes abaixo listados:"
            )
            lines.append("")

            agr = df_sel.groupby(['matricula', 'estudante']).apply(
                lambda g: list(zip(g['codigo_disciplina'].fillna(''), g['disciplina_solicitada']))
            ).reset_index(name='disciplinas')
            agr = agr.sort_values('estudante')

            for i, (_, row) in enumerate(agr.iterrows()):
                if i > 0:
                    lines.append("")
                lines.append(f"{row['matricula']} - {row['estudante']}")
                for codigo, disc in row['disciplinas']:
                    lines.append(f"  {codigo} - {disc}" if codigo else f"  {disc}")

            lines.append("")
            lines.append("Atenciosamente,")
            lines.append("Luiz Alberto Radavelli")
            lines.append("Coordenador do Curso de Bacharelado em Engenharia Elétrica")
            return "\n".join(lines)

        memorando_txt = gerar_memorando_prereq(df_sel_memo)

        with st.expander("👁️ Pré-visualização do Memorando", expanded=False):
            st.code(memorando_txt, language=None)

        if st.button("✅ Marcar Selecionados como Memorando Enviado", type="primary", key="btn_enviar_memo_prereq"):
            agora = datetime.now().strftime("%Y-%m-%d %H:%M")
            for idx in indices_sel_memo:
                df_solicitacoes.loc[idx, 'memorando_enviado'] = agora
            salvar_solicitacoes(df_solicitacoes)
            st.success(f"✅ {len(indices_sel_memo)} caso(s) marcado(s) como memorando enviado!")
            st.session_state.prereq_memo_sel = {}
            st.rerun()
    else:
        st.info("Selecione ao menos um caso para gerar o memorando.")

# --- Já enviados ---
st.markdown("---")
st.subheader("✅ Casos Deferidos — Memorando Já Enviado")

if df_enviados_memo.empty:
    st.info("Nenhum memorando enviado até o momento.")
else:
    st.write(f"**{len(df_enviados_memo)}** caso(s) com memorando já enviado.")

    COLUNAS_ENV_PREREQ = {
        "matricula": "Matrícula",
        "estudante": "Estudante",
        "codigo_disciplina": "Código",
        "disciplina_solicitada": "Disciplina",
        "semestre": "Semestre",
        "data_parecer": "Data Parecer",
        "memorando_enviado": "Memorando Enviado em",
    }
    cols_d = [c for c in COLUNAS_ENV_PREREQ.keys() if c in df_enviados_memo.columns]
    st.dataframe(
        df_enviados_memo[cols_d].rename(columns=COLUNAS_ENV_PREREQ).sort_values("Memorando Enviado em", ascending=False),
        use_container_width=True
    )

    with st.expander("🔄 Desfazer Envio de Memorando"):
        opcoes_desf = {
            f"{row['estudante']} — {row['disciplina_solicitada']} ({row['memorando_enviado']})": idx
            for idx, row in df_enviados_memo.iterrows()
        }
        sel_desf = st.selectbox(
            "Selecione o caso para desfazer",
            options=opcoes_desf.keys(),
            index=None,
            placeholder="Selecione...",
            key="sel_desfazer_prereq"
        )
        if sel_desf:
            if st.button("🔄 Confirmar: remover marcação", key="btn_desfazer_prereq"):
                idx_d = opcoes_desf[sel_desf]
                df_solicitacoes.loc[idx_d, 'memorando_enviado'] = ""
                salvar_solicitacoes(df_solicitacoes)
                st.success("Marcação de memorando removida com sucesso!")
                st.rerun()

