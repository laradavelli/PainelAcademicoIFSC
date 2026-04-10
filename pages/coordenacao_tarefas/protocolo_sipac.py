import streamlit as st
import pandas as pd
import os
from datetime import datetime

FILE_PATH = os.path.join("dados", "protocolos_sipac.csv")
COLUMNS = [
    "data_registro",
    "semestre",
    "docente",
    "numero_protocolo",
    "despacho",
]

def carregar_protocolos():
    if os.path.exists(FILE_PATH):
        df = pd.read_csv(FILE_PATH, dtype=str)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df
    else:
        return pd.DataFrame(columns=COLUMNS)

def salvar_protocolos(df):
    df.to_csv(FILE_PATH, index=False)

def main():
    st.sidebar.image(os.path.join("assets", "figConselho2.png"))
    st.sidebar.image(os.path.join("assets", "figConselho.png"))

    st.title("📑 Protocolo (SIPAC)")
    st.write("Registre os protocolos analisados no sistema SIPAC do IFSC.")

    df_protocolos = carregar_protocolos()

    # Buscar docentes
    path_docentes = os.path.join("dados", "Docentes.csv")
    docentes_list = []
    if os.path.exists(path_docentes):
        df_docentes = pd.read_csv(path_docentes)
        df_docentes = df_docentes.dropna(subset=["Docente"])
        docentes_list = sorted(df_docentes["Docente"].unique())


    # Buscar semestres
    semestres = set()
    if not df_protocolos.empty:
        semestres.update(df_protocolos["semestre"].dropna().unique())
    # Adicionar semestres recentes
    ano_atual = datetime.now().year
    for ano in range(ano_atual - 2, ano_atual + 3):
        semestres.add(f"{ano}.1")
        semestres.add(f"{ano}.2")
    semestres = sorted(list(semestres))

    # Definir semestre atual como padrão
    mes_atual = datetime.now().month
    semestre_atual_default = f"{ano_atual}.{1 if mes_atual <= 6 else 2}"

    @st.dialog("📑 Registrar Protocolo SIPAC", width="large")
    def _dialog_registrar_protocolo():
        df_protocolos = carregar_protocolos()
        with st.form("registro_protocolo", clear_on_submit=True):
            st.subheader("Registrar Protocolo SIPAC")
            col1, col2, col3 = st.columns(3)
            with col1:
                semestre = st.selectbox(
                    "Semestre",
                    options=semestres,
                    index=semestres.index(semestre_atual_default) if semestre_atual_default in semestres else 0,
                    placeholder="Selecione o semestre..."
                )
            with col2:
                docente = st.selectbox("Docente Solicitante", options=docentes_list, index=None, placeholder="Selecione o docente...")
            with col3:
                ano_atual = datetime.now().year
                protocolo_padrao = f"23292.000000/{ano_atual}-00"
                numero_protocolo = st.text_input(
                    "Número do Protocolo SIPAC",
                    value=protocolo_padrao,
                    placeholder="23292.000000/2026-00"
                )

            despacho = st.text_area("Despacho", height=120, placeholder="Insira o despacho cadastrado no processo...")

            submit = st.form_submit_button("Registrar Protocolo")

            if submit:
                if not (semestre and docente and numero_protocolo):
                    st.warning("Todos os campos são obrigatórios!")
                else:
                    agora = datetime.now().strftime("%Y-%m-%d %H:%M")
                    nova_linha = {
                        "data_registro": agora,
                        "semestre": semestre,
                        "docente": docente,
                        "numero_protocolo": numero_protocolo,
                        "despacho": despacho,
                    }
                    df_protocolos = pd.concat([df_protocolos, pd.DataFrame([nova_linha])], ignore_index=True)
                    salvar_protocolos(df_protocolos)
                    st.success(f"Protocolo registrado com sucesso!")
                    st.rerun()


    if st.button("📑 Registrar Protocolo SIPAC", use_container_width=True):
        _dialog_registrar_protocolo()

    st.markdown("---")
    st.subheader("Protocolos Registrados")

    # Seleção para editar/excluir
    if not df_protocolos.empty:
        opcoes = [f"{row['numero_protocolo']} | {row['docente']} | {row['semestre']}" for _, row in df_protocolos.iterrows()]
        selecao = st.selectbox("Selecione um protocolo para Editar/Excluir", options=[""] + opcoes, index=0)
        if selecao:
            idx = opcoes.index(selecao)
            row = df_protocolos.iloc[idx]
            st.info(f"Editando protocolo: {row['numero_protocolo']}")
            with st.form("editar_protocolo_form", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    semestre_edit = st.selectbox(
                        "Semestre",
                        options=semestres,
                        index=semestres.index(row['semestre']) if row['semestre'] in semestres else 0,
                        placeholder="Selecione o semestre..."
                    )
                with col2:
                    docente_edit = st.selectbox(
                        "Docente Solicitante",
                        options=docentes_list,
                        index=docentes_list.index(row['docente']) if row['docente'] in docentes_list else 0,
                        placeholder="Selecione o docente..."
                    )
                with col3:
                    numero_protocolo_edit = st.text_input(
                        "Número do Protocolo SIPAC",
                        value=row['numero_protocolo'],
                        placeholder="23292.000000/2026-00"
                    )
                despacho_atual = str(row.get('despacho', '')) if pd.notna(row.get('despacho', '')) else ''
                despacho_edit = st.text_area(
                    "Despacho",
                    value=despacho_atual,
                    height=120,
                    placeholder="Insira o despacho cadastrado no processo..."
                )
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submit_edit = st.form_submit_button("Salvar Alterações")
                with col_btn2:
                    submit_delete = st.form_submit_button("Excluir Protocolo")

                if submit_edit:
                    df_protocolos.at[idx, 'semestre'] = semestre_edit
                    df_protocolos.at[idx, 'docente'] = docente_edit
                    df_protocolos.at[idx, 'numero_protocolo'] = numero_protocolo_edit
                    df_protocolos.at[idx, 'despacho'] = despacho_edit
                    salvar_protocolos(df_protocolos)
                    st.success("Protocolo atualizado com sucesso!")
                    st.rerun()
                if submit_delete:
                    df_protocolos = df_protocolos.drop(df_protocolos.index[idx]).reset_index(drop=True)
                    salvar_protocolos(df_protocolos)
                    st.success("Protocolo excluído com sucesso!")
                    st.rerun()

    st.dataframe(df_protocolos, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
