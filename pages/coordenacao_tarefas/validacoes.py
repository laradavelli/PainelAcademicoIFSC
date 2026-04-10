import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils import setup_sidebar_header, construir_disciplinas_cod_nome

# Configuração da página
st.set_page_config(
    page_title="Validação",
    page_icon="📝",
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
st.header("📝 Solicitações de Validação")

# ==================== CONFIGURAÇÃO DA PLANILHA DE SOLICITAÇÕES ====================
FILE_PATH = os.path.join("dados", "solicitacoes_validacoes.csv")
COLUMNS = [
    "data_solicitacao",
    "matricula",
    "estudante",
    "codigo_disciplina",
    "disciplina_solicitada",
    "semestre",
    "descricao",
    "professor_responsavel",
    "parecer_coordenacao",
    "nota",
    "frequencia",
    "status",
    "data_parecer",
    "memorando_enviado",          # "" ou data de envio do memorando
]

def carregar_solicitacoes():
    """Carrega a planilha de solicitações do acervo do projeto."""
    if os.path.exists(FILE_PATH):
        df = pd.read_csv(FILE_PATH)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df
    else:
        return pd.DataFrame(columns=COLUMNS)

def salvar_solicitacoes(df):
    """Salva a planilha de solicitações no acervo do projeto."""
    df.to_csv(FILE_PATH, index=False)

# Carrega solicitações já registradas
df_solicitacoes = carregar_solicitacoes()

# Filtra apenas registros de validação (exclui matrículas avulsas e TC2)
if not df_solicitacoes.empty and 'descricao' in df_solicitacoes.columns:
    _mask_val_only = ~(
        df_solicitacoes['descricao'].str.contains('avulsa', case=False, na=False) |
        df_solicitacoes['descricao'].str.contains('TC2', case=False, na=False)
    )
    df_solicitacoes = df_solicitacoes[_mask_val_only].reset_index(drop=True)

# Recupera dados do arquivo de upload (sessão) para preencher o formulário
df_principal = st.session_state.df
alunos_list = df_principal[['Matricula', 'Aluno']].drop_duplicates().sort_values('Aluno')

# Lista de disciplinas no formato padronizado 'COD - Nome'
disciplinas_list, disciplinas_cod_nome, _mapa_sigaa, _mapa_parts = construir_disciplinas_cod_nome(df_principal)

# Carrega lista de docentes (mesma fonte da página Docentes)
DOCENTES_PATH = os.path.join("dados", "Docentes.csv")
if os.path.exists(DOCENTES_PATH):
    _docentes_df = pd.read_csv(DOCENTES_PATH, encoding='utf-8')
    _docentes_df = _docentes_df.dropna(subset=['Docente'])
    docentes_list = sorted(_docentes_df['Docente'].unique())
else:
    docentes_list = []

# ==================== SEÇÃO 1: NOVA SOLICITAÇÃO ====================
@st.dialog("✍️ Registrar Nova Solicitação de Validação", width="large")
def _dialog_registrar_validacao():
    df_solicitacoes = carregar_solicitacoes()

    with st.form("nova_matricula_form", clear_on_submit=True):
        st.subheader("Dados da Solicitação")

        col1, col2, col3 = st.columns(3)

        with col1:
            aluno_selecionado = st.selectbox(
                "Selecione o Estudante",
                options=alunos_list['Aluno'],
                index=None,
                placeholder="Selecione um estudante..."
            )

        with col2:
                disciplinas_selecionadas_cod_nome = st.multiselect(
                    "Selecione as Disciplinas",
                    options=disciplinas_cod_nome,
                    placeholder="Selecione uma ou mais disciplinas..."
                )

        with col3:
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

        descricao = st.text_area("Descrição da solicitação (opcional)", height=150)

        submit_button = st.form_submit_button("✔️ Enviar Solicitação de Validação")

        if submit_button:
            campos_validos = aluno_selecionado and disciplinas_selecionadas_cod_nome and semestre_atual

            if not campos_validos:
                st.warning("Os campos 'Estudante', 'Disciplinas' e 'Semestre' são obrigatórios!")
            else:
                try:
                    matricula = alunos_list[alunos_list['Aluno'] == aluno_selecionado]['Matricula'].iloc[0]
                    agora = datetime.now().strftime("%Y-%m-%d %H:%M")

                    novas_linhas = []
                    for disciplina_cod_nome in disciplinas_selecionadas_cod_nome:
                        # Extrai código e nome usando o mapa centralizado
                        parts = _mapa_parts.get(disciplina_cod_nome)
                        if parts:
                            codigo, disciplina = parts
                        elif ' - ' in disciplina_cod_nome:
                            codigo, disciplina = disciplina_cod_nome.split(' - ', 1)
                        else:
                            codigo, disciplina = '', disciplina_cod_nome
                        novas_linhas.append({
                            "data_solicitacao": agora,
                            "matricula": matricula,
                            "estudante": aluno_selecionado,
                            "codigo_disciplina": codigo,
                            "disciplina_solicitada": disciplina,
                            "semestre": semestre_atual,
                            "descricao": descricao,
                            "parecer_coordenacao": "",
                            "nota": "",
                            "frequencia": "",
                            "status": "Pendente",
                            "data_parecer": "",
                            "memorando_enviado": "",
                        })

                    df_solicitacoes = pd.concat([df_solicitacoes, pd.DataFrame(novas_linhas)], ignore_index=True)
                    salvar_solicitacoes(df_solicitacoes)

                    qtd = len(disciplinas_selecionadas_cod_nome)
                    plural = "s" if qtd > 1 else ""
                    st.success(f"Solicitação de validação para **{aluno_selecionado}** registrada com sucesso! ({qtd} disciplina{plural})")
                    st.rerun()
                except Exception as e:
                    st.error(f"Ocorreu um erro ao salvar a solicitação: {e}")

# ==================== SEÇÃO 2: AVALIAR SOLICITAÇÃO ====================
@st.dialog("✏️ Avaliar Solicitação de Validação", width="large")
def _dialog_avaliar_validacao():
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

            st.info(f"**Disciplina Solicitada:** {solicitacao_selecionada['disciplina_solicitada']}")
            descr = solicitacao_selecionada.get('descricao', '')
            if descr:
                st.info(f"**Descrição da solicitação:**\n\n{descr}")

            with st.form("update_status_matricula_form"):
                novo_status = st.selectbox("Novo Status", ["Deferido", "Indeferido"])
                col_av1, col_av2 = st.columns(2)
                with col_av1:
                    nota = st.number_input("Nota", min_value=0.0, max_value=10.0, step=0.1, format="%.1f")
                with col_av2:
                    frequencia = st.number_input("Frequência (%)", min_value=0, max_value=100, step=1, value=75)
                professor_resp = st.selectbox(
                    "Professor Responsável",
                    options=docentes_list,
                    index=None,
                    placeholder="Selecione o professor responsável..."
                )
                parecer = st.text_area("Parecer da Coordenação / Professor")

                update_button = st.form_submit_button("Salvar Parecer")

                if update_button:
                    if not parecer:
                        st.warning("O campo 'Parecer' é obrigatório.")
                    else:
                        df_solicitacoes.loc[index_selecionado, 'status'] = novo_status
                        df_solicitacoes.loc[index_selecionado, 'nota'] = nota
                        df_solicitacoes.loc[index_selecionado, 'frequencia'] = f"{frequencia}%"
                        df_solicitacoes.loc[index_selecionado, 'professor_responsavel'] = professor_resp if professor_resp else ""
                        df_solicitacoes.loc[index_selecionado, 'parecer_coordenacao'] = parecer
                        df_solicitacoes.loc[index_selecionado, 'data_parecer'] = datetime.now().strftime("%Y-%m-%d %H:%M")

                        salvar_solicitacoes(df_solicitacoes)
                        st.success("Parecer registrado e status atualizado com sucesso!")
                        st.rerun()
    else:
        st.info("Não há solicitações com status 'Pendente' para avaliar.")

# ==================== SEÇÃO 2B: EDITAR / EXCLUIR SOLICITAÇÃO ====================
@st.dialog("🔧 Editar / Excluir Solicitação de Validação", width="large")
def _dialog_editar_validacao():
    df_solicitacoes = carregar_solicitacoes()
    if df_solicitacoes.empty:
        st.info("Nenhuma solicitação registrada para editar ou excluir.")
    else:
        todas_options_val = {
            f"{row['estudante']} — {row['disciplina_solicitada']} ({row['data_solicitacao']}) [{row['status']}]": index
            for index, row in df_solicitacoes.iterrows()
        }

        selecao_editar_val = st.selectbox(
            "Selecione a Solicitação para Editar/Excluir",
            options=todas_options_val.keys(),
            index=None,
            placeholder="Selecione uma solicitação...",
            key="sel_editar_val"
        )

        if selecao_editar_val:
            idx_editar_val = todas_options_val[selecao_editar_val]
            sol_editar_val = df_solicitacoes.loc[idx_editar_val]

            tab_editar_v, tab_excluir_v = st.tabs(["✏️ Editar", "🗑️ Excluir"])

            with tab_editar_v:
                with st.form("form_editar_val"):
                    st.subheader("Editar Dados da Solicitação")

                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        aluno_edit_v = st.selectbox(
                            "Estudante",
                            options=alunos_list['Aluno'].tolist(),
                            index=alunos_list['Aluno'].tolist().index(sol_editar_val['estudante'])
                                if sol_editar_val['estudante'] in alunos_list['Aluno'].tolist() else 0,
                            key="edit_aluno_val"
                        )
                    with col_e2:
                        # Tenta encontrar o índice da disciplina salva na lista cod_nome
                        _disc_salva_v = sol_editar_val['disciplina_solicitada']
                        _cod_salvo_v = str(sol_editar_val.get('codigo_disciplina', ''))
                        _idx_disc_v = 0
                        for _di, _item in enumerate(disciplinas_cod_nome):
                            p = _mapa_parts.get(_item, ('', ''))
                            if (p[0] and p[0] == _cod_salvo_v) or (p[1] == _disc_salva_v) or (_disc_salva_v in _item):
                                _idx_disc_v = _di
                                break
                        disc_edit_v = st.selectbox(
                            "Disciplina Solicitada",
                            options=disciplinas_cod_nome,
                            index=_idx_disc_v,
                            key="edit_disc_val"
                        )

                    col_e3, col_e4 = st.columns(2)
                    with col_e3:
                        ano_atual_e = datetime.now().year
                        semestres_e = []
                        for ano in range(ano_atual_e - 2, ano_atual_e + 3):
                            semestres_e.append(f"{ano}.1")
                            semestres_e.append(f"{ano}.2")
                        sem_val_v = str(sol_editar_val['semestre'])
                        sem_idx_v = semestres_e.index(sem_val_v) if sem_val_v in semestres_e else 0
                        semestre_edit_v = st.selectbox("Semestre", options=semestres_e, index=sem_idx_v, key="edit_sem_val")

                    with col_e4:
                        STATUS_OPCOES_EDIT_V = ["Pendente", "Deferido", "Indeferido"]
                        status_val_v = str(sol_editar_val['status']) if pd.notna(sol_editar_val['status']) else "Pendente"
                        status_idx_v = STATUS_OPCOES_EDIT_V.index(status_val_v) if status_val_v in STATUS_OPCOES_EDIT_V else 0
                        status_edit_v = st.selectbox("Status", options=STATUS_OPCOES_EDIT_V, index=status_idx_v, key="edit_status_val")

                    descricao_edit_v = st.text_area(
                        "Descrição",
                        value=str(sol_editar_val['descricao']) if pd.notna(sol_editar_val['descricao']) else "",
                        key="edit_descr_val"
                    )

                    col_e5, col_e6 = st.columns(2)
                    with col_e5:
                        nota_atual = sol_editar_val.get('nota', 0.0)
                        try:
                            nota_atual = float(nota_atual) if pd.notna(nota_atual) and str(nota_atual).strip() != '' else 0.0
                        except (ValueError, TypeError):
                            nota_atual = 0.0
                        nota_edit_v = st.number_input(
                            "Nota", min_value=0.0, max_value=10.0, step=0.1,
                            format="%.1f", value=nota_atual, key="edit_nota_val"
                        )
                    with col_e6:
                        freq_atual = sol_editar_val.get('frequencia', '75')
                        try:
                            freq_atual = int(str(freq_atual).replace('%', '').strip()) if pd.notna(freq_atual) and str(freq_atual).strip() != '' else 75
                        except (ValueError, TypeError):
                            freq_atual = 75
                        freq_edit_v = st.number_input(
                            "Frequência (%)", min_value=0, max_value=100, step=1,
                            value=freq_atual, key="edit_freq_val"
                        )

                    prof_atual_v = str(sol_editar_val.get('professor_responsavel', '')) if pd.notna(sol_editar_val.get('professor_responsavel', '')) else ""
                    prof_idx_v = docentes_list.index(prof_atual_v) if prof_atual_v in docentes_list else None
                    prof_edit_v = st.selectbox(
                        "Professor Responsável",
                        options=docentes_list,
                        index=prof_idx_v,
                        placeholder="Selecione o professor responsável...",
                        key="edit_prof_val"
                    )

                    parecer_edit_v = st.text_area(
                        "Parecer da Coordenação / Professor",
                        value=str(sol_editar_val['parecer_coordenacao']) if pd.notna(sol_editar_val['parecer_coordenacao']) else "",
                        key="edit_parecer_val"
                    )

                    btn_salvar_edit_v = st.form_submit_button("💾 Salvar Alterações")

                    if btn_salvar_edit_v:
                        try:
                            matricula_edit_v = alunos_list[alunos_list['Aluno'] == aluno_edit_v]['Matricula'].iloc[0]

                            # Extrai código e nome da disciplina selecionada
                            parts_edit_v = _mapa_parts.get(disc_edit_v)
                            if parts_edit_v:
                                codigo_edit_v, nome_edit_v = parts_edit_v
                            elif ' - ' in disc_edit_v:
                                codigo_edit_v, nome_edit_v = disc_edit_v.split(' - ', 1)
                            else:
                                codigo_edit_v, nome_edit_v = '', disc_edit_v

                            df_solicitacoes.loc[idx_editar_val, 'estudante'] = aluno_edit_v
                            df_solicitacoes.loc[idx_editar_val, 'matricula'] = matricula_edit_v
                            df_solicitacoes.loc[idx_editar_val, 'disciplina_solicitada'] = nome_edit_v
                            df_solicitacoes.loc[idx_editar_val, 'codigo_disciplina'] = codigo_edit_v
                            df_solicitacoes.loc[idx_editar_val, 'semestre'] = semestre_edit_v
                            df_solicitacoes.loc[idx_editar_val, 'descricao'] = descricao_edit_v
                            df_solicitacoes.loc[idx_editar_val, 'nota'] = nota_edit_v
                            df_solicitacoes.loc[idx_editar_val, 'frequencia'] = f"{freq_edit_v}%"
                            df_solicitacoes.loc[idx_editar_val, 'professor_responsavel'] = prof_edit_v if prof_edit_v else ""
                            df_solicitacoes.loc[idx_editar_val, 'parecer_coordenacao'] = parecer_edit_v
                            df_solicitacoes.loc[idx_editar_val, 'status'] = status_edit_v
                            if status_edit_v != "Pendente" and (pd.isna(sol_editar_val['data_parecer']) or str(sol_editar_val['data_parecer']).strip() == ""):
                                df_solicitacoes.loc[idx_editar_val, 'data_parecer'] = datetime.now().strftime("%Y-%m-%d %H:%M")

                            salvar_solicitacoes(df_solicitacoes)
                            st.success("Solicitação atualizada com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar alterações: {e}")

            with tab_excluir_v:
                st.warning(
                    f"⚠️ Tem certeza que deseja **excluir** a solicitação de "
                    f"**{sol_editar_val['estudante']}** para a disciplina "
                    f"**{sol_editar_val['disciplina_solicitada']}**?"
                )
                st.caption("Esta ação não poderá ser desfeita.")

                if st.button("🗑️ Confirmar Exclusão", type="primary", key="btn_excluir_val"):
                    df_solicitacoes = df_solicitacoes.drop(index=idx_editar_val).reset_index(drop=True)
                    salvar_solicitacoes(df_solicitacoes)
                    st.success("Solicitação excluída com sucesso!")
                    st.rerun()

# ==================== BOTÕES DE AÇÃO ====================
col_act_1, col_act_2, col_act_3 = st.columns(3)
with col_act_1:
    if st.button("✍️ Registrar Nova Solicitação", use_container_width=True):
        _dialog_registrar_validacao()
with col_act_2:
    if st.button("✏️ Avaliar Solicitação", use_container_width=True):
        _dialog_avaliar_validacao()
with col_act_3:
    if st.button("🔧 Editar / Excluir Solicitação", use_container_width=True):
        _dialog_editar_validacao()

# ==================== SEÇÃO 4: PAINEL DE CONTROLE ====================
st.header("🗂️ Consulta e Relatório das Solicitações")

if df_solicitacoes.empty:
    st.info("Nenhuma solicitação de validação registrada até o momento.")
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
        "semestre": "Semestre",
        "descricao": "Descrição",
        "professor_responsavel": "Professor Responsável",
        "parecer_coordenacao": "Parecer da Coordenação",
        "nota": "Nota",
        "frequencia": "Frequência",
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
        report_lines.append("RELATÓRIO DE SOLICITAÇÕES DE VALIDAÇÃO")
        report_lines.append(f"Semestre: {semestre_selecionado}")
        report_lines.append(f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        report_lines.append(f"Total de solicitações: {len(df_relatorio)}")
        report_lines.append("=" * 60)
        report_lines.append("")
        for _, row in df_relatorio.iterrows():
            report_lines.append("-" * 60)
            report_lines.append(f"ESTUDANTE: {row.get('estudante', 'N/A')}")
            report_lines.append(f"Matrícula: {row.get('matricula', 'N/A')}")
            report_lines.append(f"Disciplina Solicitada: {row.get('disciplina_solicitada', 'N/A')}")
            report_lines.append(f"Status: {row.get('status', 'N/A')}")
            report_lines.append(f"Data da Solicitação: {row.get('data_solicitacao', 'N/A')}")
            descr = row.get('descricao', '')
            report_lines.append(f"Descrição: {descr if descr else 'Não informada'}")
            prof_r = row.get('professor_responsavel', '')
            report_lines.append(f"Professor Responsável: {prof_r if prof_r and str(prof_r) != 'nan' else 'N/A'}")
            nota_r = row.get('nota', '')
            report_lines.append(f"Nota: {nota_r if nota_r != '' and str(nota_r) != 'nan' else 'N/A'}")
            freq_r = row.get('frequencia', '')
            report_lines.append(f"Frequência: {freq_r if freq_r and str(freq_r) != 'nan' else 'N/A'}")
            parecer = row.get('parecer_coordenacao', '')
            report_lines.append(f"Parecer da Coordenação: {parecer if parecer else 'Aguardando parecer'}")
            data_p = row.get('data_parecer', '')
            report_lines.append(f"Data do Parecer: {data_p if data_p else 'Aguardando decisão'}")
            report_lines.append("")
        return "\n".join(report_lines)

    if not df_filtrado.empty:
        nome_arquivo = f"relatorio_validacao_{semestre_selecionado.replace('.', '_') if semestre_selecionado != 'Todos' else 'todos'}.txt"
        st.download_button(
            label="📥 Gerar Relatório em .txt",
            data=gerar_relatorio_txt(df_filtrado),
            file_name=nome_arquivo,
            mime="text/plain"
        )

# ==================== SEÇÃO 3: CASOS DEFERIDOS — PENDENTES DE MEMORANDO ====================
st.markdown("---")
st.subheader("⏳ Casos Deferidos — Pendentes de Memorando")

def _is_vazio_val(val):
    if pd.isna(val):
        return True
    return str(val).strip() == ""

df_deferidos_val = df_solicitacoes[df_solicitacoes['status'] == 'Deferido'].copy() if not df_solicitacoes.empty else pd.DataFrame()
mask_pendente_memo_v = df_deferidos_val['memorando_enviado'].apply(_is_vazio_val) if not df_deferidos_val.empty else pd.Series(dtype=bool)
df_pendentes_memo_v = df_deferidos_val[mask_pendente_memo_v].copy() if not df_deferidos_val.empty else pd.DataFrame()
df_enviados_memo_v = df_deferidos_val[~mask_pendente_memo_v].copy() if not df_deferidos_val.empty else pd.DataFrame()

if df_pendentes_memo_v.empty:
    st.success("Todos os casos deferidos já tiveram memorando enviado!")
else:
    st.write(f"**{len(df_pendentes_memo_v)}** caso(s) deferido(s) aguardando emissão de memorando.")

    if 'val_memo_sel' not in st.session_state:
        st.session_state.val_memo_sel = {}

    indices_sel_memo_v = []
    for idx, row in df_pendentes_memo_v.iterrows():
        label = (
            f"📝 {row['estudante']} — "
            f"{row['codigo_disciplina']} {row['disciplina_solicitada']} "
            f"({row['semestre']})"
        )
        default_val = st.session_state.val_memo_sel.get(idx, False)
        sel = st.checkbox(label, value=default_val, key=f"val_memo_cb_{idx}")
        st.session_state.val_memo_sel[idx] = sel
        if sel:
            indices_sel_memo_v.append(idx)

    df_sel_memo_v = df_pendentes_memo_v.loc[df_pendentes_memo_v.index.isin(indices_sel_memo_v)]

    st.markdown("---")

    if not df_sel_memo_v.empty:
        def gerar_memorando_validacao(df_sel):
            lines = []
            lines.append("Solicitações de Validação")
            lines.append("")
            lines.append(
                "Considerando a planilha de solicitações para validação de UC's, "
                "a banca formada para a análise DEFERIU o(s) pedido(s), de modo que "
                "solicita-se a VALIDAÇÃO da(s) disciplina(s) para o(s) estudante(s) "
                "abaixo listados:"
            )
            lines.append("")

            agr = df_sel.groupby(['matricula', 'estudante']).apply(
                lambda g: list(zip(
                    g['codigo_disciplina'].fillna(''),
                    g['disciplina_solicitada'],
                    g['nota'].fillna(''),
                    g['frequencia'].fillna(''),
                ))
            ).reset_index(name='disciplinas')
            agr = agr.sort_values('estudante')

            for i, (_, row) in enumerate(agr.iterrows()):
                if i > 0:
                    lines.append("")
                lines.append(f"{row['matricula']} - {row['estudante']}")
                for codigo, disc, nota, freq in row['disciplinas']:
                    partes = []
                    if codigo:
                        partes.append(str(codigo))
                    partes.append(disc)
                    if nota and str(nota) != 'nan' and str(nota).strip():
                        partes.append(f"Nota: {nota}")
                    if freq and str(freq) != 'nan' and str(freq).strip():
                        partes.append(f"Frequência: {freq}")
                    lines.append("  " + " - ".join(partes))

            lines.append("")
            lines.append("Atenciosamente,")
            lines.append("Luiz Alberto Radavelli")
            lines.append("Coordenador do Curso de Bacharelado em Engenharia Elétrica")
            return "\n".join(lines)

        memorando_txt_v = gerar_memorando_validacao(df_sel_memo_v)

        with st.expander("👁️ Pré-visualização do Memorando", expanded=False):
            st.code(memorando_txt_v, language=None)

        if st.button("✅ Marcar Selecionados como Memorando Enviado", type="primary", key="btn_enviar_memo_val"):
            agora = datetime.now().strftime("%Y-%m-%d %H:%M")
            for idx in indices_sel_memo_v:
                df_solicitacoes.loc[idx, 'memorando_enviado'] = agora
            salvar_solicitacoes(df_solicitacoes)
            st.success(f"✅ {len(indices_sel_memo_v)} caso(s) marcado(s) como memorando enviado!")
            st.session_state.val_memo_sel = {}
            st.rerun()
    else:
        st.info("Selecione ao menos um caso para gerar o memorando.")

# --- Já enviados ---
st.markdown("---")
st.subheader("✅ Casos Deferidos — Memorando Já Enviado")

if df_enviados_memo_v.empty:
    st.info("Nenhum memorando enviado até o momento.")
else:
    st.write(f"**{len(df_enviados_memo_v)}** caso(s) com memorando já enviado.")

    COLUNAS_ENV_VAL = {
        "matricula": "Matrícula",
        "estudante": "Estudante",
        "codigo_disciplina": "Código",
        "disciplina_solicitada": "Disciplina",
        "semestre": "Semestre",
        "data_parecer": "Data Parecer",
        "memorando_enviado": "Memorando Enviado em",
    }
    cols_d_v = [c for c in COLUNAS_ENV_VAL.keys() if c in df_enviados_memo_v.columns]
    st.dataframe(
        df_enviados_memo_v[cols_d_v].rename(columns=COLUNAS_ENV_VAL).sort_values("Memorando Enviado em", ascending=False),
        use_container_width=True
    )

    with st.expander("🔄 Desfazer Envio de Memorando"):
        opcoes_desf_v = {
            f"{row['estudante']} — {row['disciplina_solicitada']} ({row['memorando_enviado']})": idx
            for idx, row in df_enviados_memo_v.iterrows()
        }
        sel_desf_v = st.selectbox(
            "Selecione o caso para desfazer",
            options=opcoes_desf_v.keys(),
            index=None,
            placeholder="Selecione...",
            key="sel_desfazer_val"
        )
        if sel_desf_v:
            if st.button("🔄 Confirmar: remover marcação", key="btn_desfazer_val"):
                idx_d_v = opcoes_desf_v[sel_desf_v]
                df_solicitacoes.loc[idx_d_v, 'memorando_enviado'] = ""
                salvar_solicitacoes(df_solicitacoes)
                st.success("Marcação de memorando removida com sucesso!")
                st.rerun()

