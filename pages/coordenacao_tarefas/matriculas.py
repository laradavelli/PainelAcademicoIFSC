import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils import setup_sidebar_header, construir_disciplinas_cod_nome

# Configuração da página
st.set_page_config(
    page_title="Matrículas - Memorandos",
    page_icon="📨",
    layout="wide"
)

# Verificação de acesso
if 'arquivo_carregado' not in st.session_state or not st.session_state.arquivo_carregado:
    setup_sidebar_header()
    st.error("⚠️ Por favor, faça o upload do arquivo na página inicial primeiro! Volte para Home.")
    st.stop()


# Sidebar
setup_sidebar_header()

# ========== MATRÍCULA AVULSA ==========
st.header("📨 Matrículas — Emissão de Memorandos")

# ==================== CONFIGURAÇÃO E MIGRAÇÃO ====================
MAT_AVULSA_CSV = os.path.join("dados", "solicitacoes_matricula_avulsa.csv")
MAT_AVULSA_COLS = [
    "data_solicitacao", "matricula", "estudante", "codigo_disciplina",
    "disciplina_solicitada", "semestre", "descricao", "professor_responsavel",
    "parecer_coordenacao", "nota", "frequencia", "status", "data_parecer",
    "memorando_enviado",
]

# Migração: move registros de matrícula avulsa/TC2 do CSV compartilhado para o exclusivo
_SHARED_CSV = os.path.join("dados", "solicitacoes_validacoes.csv")
if os.path.exists(_SHARED_CSV):
    _df_shared = pd.read_csv(_SHARED_CSV)
    if 'descricao' in _df_shared.columns and not _df_shared.empty:
        _mask_mig = (
            _df_shared['descricao'].str.contains('avulsa', case=False, na=False) |
            _df_shared['descricao'].str.contains('TC2', case=False, na=False)
        )
        if _mask_mig.any():
            _df_to_move = _df_shared[_mask_mig]
            if os.path.exists(MAT_AVULSA_CSV):
                _df_existing = pd.read_csv(MAT_AVULSA_CSV)
                _df_all = pd.concat([_df_existing, _df_to_move], ignore_index=True)
            else:
                _df_all = _df_to_move.copy()
            _df_all.to_csv(MAT_AVULSA_CSV, index=False)
            _df_shared[~_mask_mig].to_csv(_SHARED_CSV, index=False)

def carregar_matriculas_avulsas():
    if os.path.exists(MAT_AVULSA_CSV):
        df = pd.read_csv(MAT_AVULSA_CSV)
        for col in MAT_AVULSA_COLS:
            if col not in df.columns:
                df[col] = ""
        return df
    return pd.DataFrame(columns=MAT_AVULSA_COLS)

def salvar_matriculas_avulsas(df):
    df.to_csv(MAT_AVULSA_CSV, index=False)

# Carregar lista de discentes
try:
    df_discentes = st.session_state.df
except Exception:
    df_discentes = None

if df_discentes is not None and not df_discentes.empty:
    # Preparar listas para seleção
    alunos_list = df_discentes[['Matricula', 'Aluno']].drop_duplicates().sort_values('Aluno')
    opcoes_estudantes = alunos_list['Aluno'].tolist()
    disciplinas_list, disciplinas_cod_nome, _mapa_sigaa, _mapa_parts = construir_disciplinas_cod_nome(df_discentes)

    # Carregar lista de docentes
    DOCENTES_PATH = os.path.join("dados", "Docentes.csv")
    if os.path.exists(DOCENTES_PATH):
        _docentes_df = pd.read_csv(DOCENTES_PATH, encoding='utf-8')
        _docentes_df = _docentes_df.dropna(subset=['Docente'])
        docentes_list = sorted(_docentes_df['Docente'].unique())
    else:
        docentes_list = []

    from datetime import datetime
    ano_atual = datetime.now().year
    semestres_opcoes = []
    for ano in range(ano_atual - 2, ano_atual + 3):
        semestres_opcoes.append(f"{ano}.1")
        semestres_opcoes.append(f"{ano}.2")
    semestre_atual_default = f"{ano_atual}.{1 if datetime.now().month <= 6 else 2}"

    @st.dialog("✍️ Registrar Nova Solicitação de Matrícula Avulsa", width="large")
    def _dialog_registrar_matricula():
        with st.form("form_matricula_avulsa", clear_on_submit=True):
            st.subheader("Dados da Solicitação")
            col1, col2, col3 = st.columns(3)
            with col1:
                estudante_sel = st.selectbox(
                    "Selecione o Estudante",
                    options=opcoes_estudantes,
                    index=None,
                    placeholder="Selecione um estudante..."
                )
            with col2:
                disciplinas_selecionadas = st.multiselect(
                    "Selecione as Disciplinas",
                    options=disciplinas_cod_nome,
                    placeholder="Selecione uma ou mais disciplinas..."
                )
            with col3:
                semestre_sel = st.selectbox(
                    "Semestre",
                    options=semestres_opcoes,
                    index=semestres_opcoes.index(semestre_atual_default) if semestre_atual_default in semestres_opcoes else 0
                )

            # Só permite TC2 isoladamente
            is_tc2 = False
            if disciplinas_selecionadas:
                if len(disciplinas_selecionadas) == 1:
                    _sel_item = disciplinas_selecionadas[0].upper()
                    if "TC2" in _sel_item or "TRABALHO DE CONCLUSÃO DE CURSO II" in _sel_item:
                        is_tc2 = True

            if is_tc2:
                st.markdown("---")
                st.markdown("**Informações para TC2**")
                titulo_trabalho = st.text_input("Título do Trabalho")
                orientador = st.selectbox("Nome do Orientador", [""] + docentes_list)
                coorientador = st.selectbox("Nome do Coorientador (opcional)", ["Nenhum"] + docentes_list)
            else:
                titulo_trabalho = ""
                orientador = ""
                coorientador = "Nenhum"

            submit = st.form_submit_button("Enviar solicitação de matrícula")

            if submit:
                campos_validos = estudante_sel and disciplinas_selecionadas and semestre_sel
                if not campos_validos:
                    st.warning("Os campos 'Estudante', 'Disciplinas' e 'Semestre' são obrigatórios!")
                elif is_tc2:
                    if not titulo_trabalho or not orientador:
                        st.warning("Para TC2, preencha o título do trabalho e o orientador.")
                    else:
                        try:
                            matricula = alunos_list[alunos_list['Aluno'] == estudante_sel]['Matricula'].iloc[0]
                            agora = datetime.now().strftime("%Y-%m-%d %H:%M")

                            # Extrai código e nome da disciplina TC2
                            _p_tc2 = _mapa_parts.get(disciplinas_selecionadas[0])
                            if _p_tc2:
                                _cod_tc2, _nome_tc2 = _p_tc2
                            elif ' - ' in disciplinas_selecionadas[0]:
                                _cod_tc2, _nome_tc2 = disciplinas_selecionadas[0].split(' - ', 1)
                            else:
                                _cod_tc2, _nome_tc2 = '', disciplinas_selecionadas[0]

                            registro = {
                                "data_solicitacao": agora,
                                "matricula": matricula,
                                "estudante": estudante_sel,
                                "codigo_disciplina": _cod_tc2,
                                "disciplina_solicitada": _nome_tc2,
                                "semestre": semestre_sel,
                                "descricao": f"TC2 - Título: {titulo_trabalho} | Orientador: {orientador} | Coorientador: {coorientador if coorientador != 'Nenhum' else ''}",
                                "parecer_coordenacao": "Deferido automaticamente",
                                "nota": "",
                                "frequencia": "",
                                "status": "Deferido",
                                "data_parecer": agora,
                                "professor_responsavel": orientador,
                                "memorando_enviado": "",
                            }
                            if os.path.exists(MAT_AVULSA_CSV):
                                df_valid = pd.read_csv(MAT_AVULSA_CSV)
                            else:
                                df_valid = pd.DataFrame()
                            df_valid = pd.concat([df_valid, pd.DataFrame([registro])], ignore_index=True)
                            df_valid.to_csv(MAT_AVULSA_CSV, index=False)
                            st.success("Solicitação registrada com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao registrar solicitação: {e}")
                else:
                    try:
                        matricula = alunos_list[alunos_list['Aluno'] == estudante_sel]['Matricula'].iloc[0]
                        agora = datetime.now().strftime("%Y-%m-%d %H:%M")
                        novas_linhas = []
                        for disc_cod_nome in disciplinas_selecionadas:
                            # Extrai código e nome
                            _p_disc = _mapa_parts.get(disc_cod_nome)
                            if _p_disc:
                                _cod_d, _nome_d = _p_disc
                            elif ' - ' in disc_cod_nome:
                                _cod_d, _nome_d = disc_cod_nome.split(' - ', 1)
                            else:
                                _cod_d, _nome_d = '', disc_cod_nome

                            registro = {
                                "data_solicitacao": agora,
                                "matricula": matricula,
                                "estudante": estudante_sel,
                                "codigo_disciplina": _cod_d,
                                "disciplina_solicitada": _nome_d,
                                "semestre": semestre_sel,
                                "descricao": "Matrícula avulsa via painel",
                                "parecer_coordenacao": "Deferido automaticamente",
                                "nota": "",
                                "frequencia": "",
                                "status": "Deferido",
                                "data_parecer": agora,
                                "professor_responsavel": "",
                                "memorando_enviado": "",
                            }
                            novas_linhas.append(registro)
                        if os.path.exists(MAT_AVULSA_CSV):
                            df_valid = pd.read_csv(MAT_AVULSA_CSV)
                        else:
                            df_valid = pd.DataFrame()
                        df_valid = pd.concat([df_valid, pd.DataFrame(novas_linhas)], ignore_index=True)
                        df_valid.to_csv(MAT_AVULSA_CSV, index=False)
                        st.success("Solicitação registrada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao registrar solicitação: {e}")
    # ==================== SEÇÃO 2B: EDITAR / EXCLUIR SOLICITAÇÃO DE MATRÍCULA AVULSA ====================
    @st.dialog("🔧 Editar / Excluir Solicitação de Matrícula Avulsa", width="large")
    def _dialog_editar_matricula():
        if os.path.exists(MAT_AVULSA_CSV):
            df_valid_edit = pd.read_csv(MAT_AVULSA_CSV)
            df_avulsa = df_valid_edit.copy()
        else:
            df_valid_edit = pd.DataFrame()
            df_avulsa = pd.DataFrame()

        if df_avulsa.empty:
            st.info("Nenhuma solicitação de matrícula avulsa registrada para editar ou excluir.")
        else:
            todas_options_mat = {
                f"{row['estudante']} — {row['disciplina_solicitada']} ({row['data_solicitacao']}) [{row['status']}]": index
                for index, row in df_avulsa.iterrows()
            }

            selecao_editar_mat = st.selectbox(
                "Selecione a Solicitação para Editar/Excluir",
                options=todas_options_mat.keys(),
                index=None,
                placeholder="Selecione uma solicitação...",
                key="sel_editar_mat"
            )

            if selecao_editar_mat:
                idx_editar_mat = todas_options_mat[selecao_editar_mat]
                sol_editar_mat = df_valid_edit.loc[idx_editar_mat]

                tab_editar_m, tab_excluir_m = st.tabs(["✏️ Editar", "🗑️ Excluir"])

                with tab_editar_m:
                    with st.form("form_editar_mat"):
                        st.subheader("Editar Dados da Solicitação")

                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            aluno_edit_m = st.selectbox(
                                "Estudante",
                                options=opcoes_estudantes,
                                index=opcoes_estudantes.index(sol_editar_mat['estudante'])
                                    if sol_editar_mat['estudante'] in opcoes_estudantes else 0,
                                key="edit_aluno_mat"
                            )
                        with col_e2:
                            # Tenta encontrar o índice da disciplina salva na lista cod_nome
                            _disc_salva_m = sol_editar_mat['disciplina_solicitada']
                            _cod_salvo_m = str(sol_editar_mat.get('codigo_disciplina', ''))
                            _idx_disc_m = 0
                            for _di, _item in enumerate(disciplinas_cod_nome):
                                p = _mapa_parts.get(_item, ('', ''))
                                if (p[0] and p[0] == _cod_salvo_m) or (p[1] == _disc_salva_m) or (_disc_salva_m in _item):
                                    _idx_disc_m = _di
                                    break
                            disc_edit_m = st.selectbox(
                                "Disciplina Solicitada",
                                options=disciplinas_cod_nome,
                                index=_idx_disc_m,
                                key="edit_disc_mat"
                            )

                        col_e3, col_e4 = st.columns(2)
                        with col_e3:
                            sem_val_m = str(sol_editar_mat['semestre'])
                            sem_idx_m = semestres_opcoes.index(sem_val_m) if sem_val_m in semestres_opcoes else 0
                            semestre_edit_m = st.selectbox("Semestre", options=semestres_opcoes, index=sem_idx_m, key="edit_sem_mat")

                        with col_e4:
                            STATUS_OPCOES_EDIT_M = ["Pendente", "Deferido", "Indeferido"]
                            status_val_m = str(sol_editar_mat['status']) if pd.notna(sol_editar_mat['status']) else "Pendente"
                            status_idx_m = STATUS_OPCOES_EDIT_M.index(status_val_m) if status_val_m in STATUS_OPCOES_EDIT_M else 0
                            status_edit_m = st.selectbox("Status", options=STATUS_OPCOES_EDIT_M, index=status_idx_m, key="edit_status_mat")

                        descricao_edit_m = st.text_area(
                            "Descrição",
                            value=str(sol_editar_mat['descricao']) if pd.notna(sol_editar_mat['descricao']) else "",
                            key="edit_descr_mat"
                        )

                        prof_atual_m = str(sol_editar_mat.get('professor_responsavel', '')) if pd.notna(sol_editar_mat.get('professor_responsavel', '')) else ""
                        prof_idx_m = docentes_list.index(prof_atual_m) if prof_atual_m in docentes_list else None
                        prof_edit_m = st.selectbox(
                            "Professor Responsável",
                            options=docentes_list,
                            index=prof_idx_m,
                            placeholder="Selecione o professor responsável...",
                            key="edit_prof_mat"
                        )

                        parecer_edit_m = st.text_area(
                            "Parecer da Coordenação",
                            value=str(sol_editar_mat['parecer_coordenacao']) if pd.notna(sol_editar_mat['parecer_coordenacao']) else "",
                            key="edit_parecer_mat"
                        )

                        btn_salvar_edit_m = st.form_submit_button("💾 Salvar Alterações")

                        if btn_salvar_edit_m:
                            try:
                                matricula_edit_m = alunos_list[alunos_list['Aluno'] == aluno_edit_m]['Matricula'].iloc[0]

                                # Extrai código e nome da disciplina selecionada
                                parts_edit_m = _mapa_parts.get(disc_edit_m)
                                if parts_edit_m:
                                    codigo_edit_m, nome_edit_m = parts_edit_m
                                elif ' - ' in disc_edit_m:
                                    codigo_edit_m, nome_edit_m = disc_edit_m.split(' - ', 1)
                                else:
                                    codigo_edit_m, nome_edit_m = '', disc_edit_m

                                df_valid_edit.loc[idx_editar_mat, 'estudante'] = aluno_edit_m
                                df_valid_edit.loc[idx_editar_mat, 'matricula'] = matricula_edit_m
                                df_valid_edit.loc[idx_editar_mat, 'disciplina_solicitada'] = nome_edit_m
                                df_valid_edit.loc[idx_editar_mat, 'codigo_disciplina'] = codigo_edit_m
                                df_valid_edit.loc[idx_editar_mat, 'semestre'] = semestre_edit_m
                                df_valid_edit.loc[idx_editar_mat, 'descricao'] = descricao_edit_m
                                df_valid_edit.loc[idx_editar_mat, 'professor_responsavel'] = prof_edit_m if prof_edit_m else ""
                                df_valid_edit.loc[idx_editar_mat, 'parecer_coordenacao'] = parecer_edit_m
                                df_valid_edit.loc[idx_editar_mat, 'status'] = status_edit_m
                                if status_edit_m != "Pendente" and (pd.isna(sol_editar_mat['data_parecer']) or str(sol_editar_mat['data_parecer']).strip() == ""):
                                    df_valid_edit.loc[idx_editar_mat, 'data_parecer'] = datetime.now().strftime("%Y-%m-%d %H:%M")

                                df_valid_edit.to_csv(MAT_AVULSA_CSV, index=False)
                                st.success("Solicitação atualizada com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao salvar alterações: {e}")

                with tab_excluir_m:
                    st.warning(
                        f"⚠️ Tem certeza que deseja **excluir** a solicitação de "
                        f"**{sol_editar_mat['estudante']}** para a disciplina "
                        f"**{sol_editar_mat['disciplina_solicitada']}**?"
                    )
                    st.caption("Esta ação não poderá ser desfeita.")

                    if st.button("🗑️ Confirmar Exclusão", type="primary", key="btn_excluir_mat"):
                        df_valid_edit = df_valid_edit.drop(index=idx_editar_mat).reset_index(drop=True)
                        df_valid_edit.to_csv(MAT_AVULSA_CSV, index=False)
                        st.success("Solicitação excluída com sucesso!")
                        st.rerun()


    # ==================== BOTÕES DE AÇÃO ====================
    col_act_m1, col_act_m2 = st.columns(2)
    with col_act_m1:
        if st.button("✍️ Registrar Nova Solicitação", use_container_width=True):
            _dialog_registrar_matricula()
    with col_act_m2:
        if st.button("🔧 Editar / Excluir Solicitação", use_container_width=True):
            _dialog_editar_matricula()

    # ==================== SEÇÃO 4: CONSULTA E RELATÓRIO ====================
    df_mat_avulsa = carregar_matriculas_avulsas()

    st.header("🗂️ Consulta e Relatório das Solicitações de Matrícula Avulsa")

    if df_mat_avulsa.empty:
        st.info("Nenhuma solicitação de matrícula avulsa registrada até o momento.")
    else:
        # Filtros
        semestres_disp_mat = [str(s) for s in df_mat_avulsa['semestre'].dropna().unique() if str(s).strip() != '']
        semestres_disp_mat = sorted(semestres_disp_mat, reverse=True)

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            semestre_sel_mat = st.selectbox("Semestre", options=["Todos"] + semestres_disp_mat, key="filtro_sem_mat")
        with col_f2:
            STATUS_OPCOES_MAT = ["Pendente", "Deferido", "Indeferido"]
            status_filter_mat = st.multiselect("Status", options=STATUS_OPCOES_MAT, default=["Deferido"], key="filtro_status_mat")
        with col_f3:
            estudantes_opcoes_mat = sorted(df_mat_avulsa['estudante'].dropna().unique())
            aluno_filter_mat = st.multiselect("Estudante", options=estudantes_opcoes_mat, key="filtro_aluno_mat")

        df_filtrado_mat = df_mat_avulsa.copy()
        if semestre_sel_mat != "Todos":
            df_filtrado_mat = df_filtrado_mat[df_filtrado_mat['semestre'] == semestre_sel_mat]
        if status_filter_mat:
            df_filtrado_mat = df_filtrado_mat[df_filtrado_mat['status'].isin(status_filter_mat)]
        if aluno_filter_mat:
            df_filtrado_mat = df_filtrado_mat[df_filtrado_mat['estudante'].isin(aluno_filter_mat)]

        COLUNAS_EXIB_MAT = {
            "data_solicitacao": "Data Solicitação",
            "matricula": "Matrícula",
            "estudante": "Estudante",
            "disciplina_solicitada": "Disciplina Solicitada",
            "descricao": "Descrição",
            "professor_responsavel": "Professor Responsável",
            "semestre": "Semestre",
            "parecer_coordenacao": "Parecer da Coordenação",
            "status": "Status",
            "data_parecer": "Data do Parecer",
        }

        st.write(f"Exibindo **{len(df_filtrado_mat)}** de **{len(df_mat_avulsa)}** solicitações.")

        cols_exibir_mat = [c for c in COLUNAS_EXIB_MAT.keys() if c in df_filtrado_mat.columns]
        df_exibir_mat = df_filtrado_mat[cols_exibir_mat].rename(columns=COLUNAS_EXIB_MAT)
        st.dataframe(df_exibir_mat.sort_values("Data Solicitação", ascending=False), use_container_width=True)

        def gerar_relatorio_mat(df_rel):
            report_lines = []
            report_lines.append("RELATÓRIO DE SOLICITAÇÕES DE MATRÍCULA AVULSA")
            report_lines.append(f"Semestre: {semestre_sel_mat}")
            report_lines.append(f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            report_lines.append(f"Total de solicitações: {len(df_rel)}")
            report_lines.append("=" * 60)
            report_lines.append("")
            for _, row in df_rel.iterrows():
                report_lines.append("-" * 60)
                report_lines.append(f"ESTUDANTE: {row.get('estudante', 'N/A')}")
                report_lines.append(f"Matrícula: {row.get('matricula', 'N/A')}")
                report_lines.append(f"Disciplina Solicitada: {row.get('disciplina_solicitada', 'N/A')}")
                descr = row.get('descricao', '')
                report_lines.append(f"Descrição: {descr if descr and str(descr) != 'nan' else 'N/A'}")
                prof = row.get('professor_responsavel', '')
                report_lines.append(f"Professor Responsável: {prof if prof and str(prof) != 'nan' else 'N/A'}")
                report_lines.append(f"Status: {row.get('status', 'N/A')}")
                report_lines.append(f"Data da Solicitação: {row.get('data_solicitacao', 'N/A')}")
                parecer = row.get('parecer_coordenacao', '')
                report_lines.append(f"Parecer: {parecer if parecer else 'N/A'}")
                data_p = row.get('data_parecer', '')
                report_lines.append(f"Data do Parecer: {data_p if data_p else 'N/A'}")
                report_lines.append("")
            return "\n".join(report_lines)

        if not df_filtrado_mat.empty:
            nome_arquivo_mat = f"relatorio_matricula_avulsa_{semestre_sel_mat.replace('.', '_') if semestre_sel_mat != 'Todos' else 'todos'}.txt"
            st.download_button(
                label="📥 Gerar Relatório em .txt",
                data=gerar_relatorio_mat(df_filtrado_mat),
                file_name=nome_arquivo_mat,
                mime="text/plain"
            )

    # ==================== SEÇÃO 3: CASOS DEFERIDOS — PENDENTES DE MEMORANDO ====================
    st.markdown("---")
    st.subheader("⏳ Casos Deferidos — Pendentes de Memorando")

    def _is_vazio_mat(val):
        if pd.isna(val):
            return True
        return str(val).strip() == ""

    df_deferidos_mat = df_mat_avulsa[df_mat_avulsa['status'] == 'Deferido'].copy() if not df_mat_avulsa.empty else pd.DataFrame()

    if not df_deferidos_mat.empty:
        _mask_pend = df_deferidos_mat['memorando_enviado'].apply(_is_vazio_mat)
        df_pendentes_mat = df_deferidos_mat[_mask_pend].copy()
        df_enviados_mat = df_deferidos_mat[~_mask_pend].copy()
    else:
        df_pendentes_mat = pd.DataFrame()
        df_enviados_mat = pd.DataFrame()

    if df_pendentes_mat.empty:
        st.success("Todos os casos deferidos já tiveram memorando enviado!")
    else:
        st.write(f"**{len(df_pendentes_mat)}** caso(s) deferido(s) aguardando emissão de memorando.")

        if 'mat_avulsa_memo_sel' not in st.session_state:
            st.session_state.mat_avulsa_memo_sel = {}

        indices_sel_mat = []
        for idx, row in df_pendentes_mat.iterrows():
            label = (
                f"📨 {row['estudante']} — "
                f"{row['disciplina_solicitada']} "
                f"({row['semestre']})"
            )
            default_val = st.session_state.mat_avulsa_memo_sel.get(idx, False)
            sel = st.checkbox(label, value=default_val, key=f"mat_memo_cb_{idx}")
            st.session_state.mat_avulsa_memo_sel[idx] = sel
            if sel:
                indices_sel_mat.append(idx)

        df_sel_mat = df_pendentes_mat.loc[df_pendentes_mat.index.isin(indices_sel_mat)]

        st.markdown("---")

        if not df_sel_mat.empty:
            def gerar_memorando_matricula(df_sel):
                lines = []
                lines.append("Matrícula Avulsa")
                lines.append("")
                lines.append(
                    "Solicita-se a efetivação da matrícula nas disciplinas "
                    "correspondentes para os estudantes abaixo listados:"
                )
                lines.append("")

                agr = df_sel.groupby(['matricula', 'estudante']).apply(
                    lambda g: list(zip(
                        g['disciplina_solicitada'],
                        g['descricao'].fillna(''),
                    ))
                ).reset_index(name='disciplinas')
                agr = agr.sort_values('estudante')

                for i, (_, row) in enumerate(agr.iterrows()):
                    if i > 0:
                        lines.append("")
                    lines.append(f"{row['matricula']} - {row['estudante']}")
                    for disc, descr in row['disciplinas']:
                        lines.append(f"  {disc}")
                        if descr and 'TC2' in str(descr):
                            lines.append(f"    {descr}")

                lines.append("")
                lines.append("Atenciosamente,")
                lines.append("Luiz Alberto Radavelli")
                lines.append("Coordenador do Curso de Bacharelado em Engenharia Elétrica")
                return "\n".join(lines)

            memorando_txt_mat = gerar_memorando_matricula(df_sel_mat)

            with st.expander("👁️ Pré-visualização do Memorando", expanded=False):
                st.code(memorando_txt_mat, language=None)

            if st.button("✅ Marcar Selecionados como Memorando Enviado", type="primary", key="btn_enviar_memo_mat"):
                agora = datetime.now().strftime("%Y-%m-%d %H:%M")
                for idx in indices_sel_mat:
                    df_mat_avulsa.loc[idx, 'memorando_enviado'] = agora
                salvar_matriculas_avulsas(df_mat_avulsa)
                st.success(f"✅ {len(indices_sel_mat)} caso(s) marcado(s) como memorando enviado!")
                st.session_state.mat_avulsa_memo_sel = {}
                st.rerun()
        else:
            st.info("Selecione ao menos um caso para gerar o memorando.")

    # --- Já enviados ---
    st.markdown("---")
    st.subheader("✅ Casos Deferidos — Memorando Já Enviado")

    if df_enviados_mat.empty:
        st.info("Nenhum memorando enviado até o momento.")
    else:
        st.write(f"**{len(df_enviados_mat)}** caso(s) com memorando já enviado.")

        COLUNAS_ENV_MAT = {
            "matricula": "Matrícula",
            "estudante": "Estudante",
            "disciplina_solicitada": "Disciplina",
            "descricao": "Descrição",
            "semestre": "Semestre",
            "data_parecer": "Data Parecer",
            "memorando_enviado": "Memorando Enviado em",
        }
        cols_d_m = [c for c in COLUNAS_ENV_MAT.keys() if c in df_enviados_mat.columns]
        st.dataframe(
            df_enviados_mat[cols_d_m].rename(columns=COLUNAS_ENV_MAT).sort_values("Memorando Enviado em", ascending=False),
            use_container_width=True
        )

        with st.expander("🔄 Desfazer Envio de Memorando"):
            opcoes_desf_mat = {
                f"{row['estudante']} — {row['disciplina_solicitada']} ({row['memorando_enviado']})": idx
                for idx, row in df_enviados_mat.iterrows()
            }
            sel_desf_mat = st.selectbox(
                "Selecione o caso para desfazer",
                options=opcoes_desf_mat.keys(),
                index=None,
                placeholder="Selecione...",
                key="sel_desfazer_mat"
            )
            if sel_desf_mat:
                if st.button("🔄 Confirmar: remover marcação", key="btn_desfazer_mat"):
                    idx_d_m = opcoes_desf_mat[sel_desf_mat]
                    df_mat_avulsa.loc[idx_d_m, 'memorando_enviado'] = ""
                    salvar_matriculas_avulsas(df_mat_avulsa)
                    st.success("Marcação de memorando removida com sucesso!")
                    st.rerun()

else:
    st.info("Não foi possível carregar a lista de estudantes para matrícula avulsa.")
