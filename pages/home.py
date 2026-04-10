import streamlit as st
import pandas as pd
import os

# Configuração da página
st.set_page_config(page_title="Sistema Acadêmico", layout="wide")

# Configuração da sidebar (centralizada)
from utils import setup_sidebar_header, carregar_dados_sigaa
setup_sidebar_header()

# Configuração da sessão
if 'arquivo_carregado' not in st.session_state:
        st.session_state.arquivo_carregado = False
if 'df' not in st.session_state:
    st.session_state.df = None

# Título central
st.header("Base de dados")

# ── Seleção do curso ─────────────────────────────────────────────────────
CURSOS_DISPONIVEIS = [
    "Bacharelado em Engenharia Elétrica",
    "Bacharelado em Engenharia Mecânica",
    "Tecnologia de Fabricação Mecânica",
    "Técnico em Desenvolvimento de Sistemas",
    "Técnico em Eletrotécnica",
    "Técnico em Mecânica",
]

if "curso_selecionado" not in st.session_state:
    st.session_state.curso_selecionado = CURSOS_DISPONIVEIS[0]

curso_escolhido = st.selectbox(
    "Curso",
    options=["Todos"] + CURSOS_DISPONIVEIS,
    index=(["Todos"] + CURSOS_DISPONIVEIS).index(st.session_state.curso_selecionado)
        if st.session_state.curso_selecionado in (["Todos"] + CURSOS_DISPONIVEIS)
        else 1,
    help="Selecione o curso que o sistema irá analisar. Aplica-se a todas as páginas.",
)
st.session_state.curso_selecionado = curso_escolhido

# ── Upload do arquivo ────────────────────────────────────────────────────

# Área de upload do arquivo
uploaded_file = st.file_uploader("",type=['csv'])

if uploaded_file is not None:
    try:
        # Leitura do arquivo CSV com tentativa de vários encodings
        df = None
        used_encoding = None
        header_lines = None
        encodings_to_try = ['utf-8', 'latin1', 'cp1252']
        last_exc = None
        
        for enc in encodings_to_try:
            try:
                # reinicia ponteiro do arquivo (UploadedFile)
                uploaded_file.seek(0)
                
                # Primeiro, lê as 4 primeiras linhas do cabeçalho SIGAA
                header_lines = []
                for i in range(4):
                    line = uploaded_file.readline().decode(enc)
                    header_lines.append(line.strip())
                
                # Reinicia e lê o CSV completo pulando o cabeçalho
                uploaded_file.seek(0)
                
                # Mapeamento de nomes originais SIGAA para nomes internos
                # Inclui também nomes antigos (sem acento) para compatibilidade com arquivos já salvos
                mapeamento_colunas = {
                    # Nomes originais SIGAA (com acentos)
                    "Período": "Fase",
                    "Matrícula": "Matricula",
                    "Nome discente": "Aluno",
                    "Situação": "Situacao",
                    "Código": "Codigo",
                    "Nome": "Disciplina",
                    "Nota": "Nota",
                    "Frequência Consolidada": "Frequencia",
                    "Percentual de Infrequência (parcial)": "Infrequencia",
                    "ANP - Não participação": "ANP",
                    # Nomes antigos (arquivos salvos antes da atualização) - já estão corretos, não precisa mapear
                }
                
                # Lê todas as colunas disponíveis (pode ter colunas de observação)
                df = pd.read_csv(
                    uploaded_file,
                    sep=';',
                    skiprows=4,  # Pula as 4 linhas de cabeçalho SIGAA, mantém linha de nomes das colunas
                    encoding=enc,
                    index_col=False  # Evita que a primeira coluna seja usada como índice
                )
                
                # Renomeia colunas originais do SIGAA para nomes internos
                df = df.rename(columns=mapeamento_colunas)
                
                used_encoding = enc
                break
            except Exception as e:
                last_exc = e

        if df is None:
            # Não conseguimos decodificar com os encodings tentados
            raise last_exc

        # Armazena cabeçalho SIGAA na sessão para uso ao salvar
        st.session_state.sigaa_header = header_lines
        st.session_state.file_encoding = used_encoding
        
        # Informe ao usuário (se desenvolvedor) qual encoding foi utilizado (útil para depuração)
        # deixar o código abaixo apenas para desenvolvedor, não há necessidade do usuário identificar isso.
        st.info(f"Arquivo lido com encoding: {used_encoding}")
        
        # Preparação dos dados
        df = df.dropna(subset=["Matricula", "Disciplina"])
        df["Fase"] = df["Fase"].astype(str).str.strip()
        df["Matricula"] = df["Matricula"].astype(str).str.strip()
        
        # === MESCLA DE OBSERVAÇÕES DO CSV EXISTENTE ===
        # Se já existe um arquivo salvo anteriormente, recupera as observações
        # (pedagógicas e de docentes) para que não sejam perdidas com o novo upload.
        csv_existente = 'dados/notas_discentes.csv'
        if os.path.exists(csv_existente):
            try:
                # Tenta múltiplos encodings pois o CSV salvo pode ter encoding diferente
                df_anterior = None
                for enc_try in [used_encoding, 'utf-8', 'latin1', 'cp1252']:
                    try:
                        df_anterior, _ = carregar_dados_sigaa(csv_existente, encoding=enc_try)
                        break
                    except Exception:
                        continue
                
                if df_anterior is not None:
                    df_anterior['Matricula'] = df_anterior['Matricula'].astype(str).str.strip()
                    
                    # Obs_Pedagogico é por estudante (mesma obs em todas as disciplinas),
                    # então a chave é apenas a matrícula.
                    # Obs_Professor e Caracteristicas_Prof são por disciplina,
                    # então a chave é (matrícula, disciplina).
                    colunas_por_estudante = ['Obs_Pedagogico']
                    colunas_por_disciplina = ['Obs_Professor', 'Caracteristicas_Prof']
                    
                    for col in colunas_por_estudante + colunas_por_disciplina:
                        if col not in df.columns:
                            df[col] = ''
                        if col not in df_anterior.columns:
                            continue
                        
                        usa_disciplina = col in colunas_por_disciplina
                        
                        # Itera de cima para baixo; dict sobrescreve, então o valor
                        # mais ao final do CSV (mais recente) é o que prevalece.
                        obs_map = {}
                        for _, row in df_anterior.iterrows():
                            val = row.get(col, '')
                            if pd.notna(val) and str(val).strip():
                                if usa_disciplina:
                                    chave = (str(row['Matricula']).strip(), str(row.get('Disciplina', '')).strip())
                                else:
                                    chave = str(row['Matricula']).strip()
                                obs_map[chave] = str(val)
                        
                        # Aplica observações do arquivo anterior apenas onde o novo CSV não tem
                        for idx, row in df.iterrows():
                            val_atual = row.get(col, '')
                            if pd.isna(val_atual) or str(val_atual).strip() == '':
                                if usa_disciplina:
                                    chave = (str(row['Matricula']).strip(), str(row.get('Disciplina', '')).strip())
                                else:
                                    chave = str(row['Matricula']).strip()
                                if chave in obs_map:
                                    df.at[idx, col] = obs_map[chave]
            except Exception:
                pass  # Se falhar ao ler o CSV anterior, prossegue sem mescla
        
        # Salvando os dados na sessão
        st.session_state.df = df
        # guarda uma cópia original para permitir desfazer alterações
        st.session_state.df_original = df.copy()
        # cria um id de sessão para auditoria
        import uuid
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.arquivo_carregado = True

        # Sucesso no carregamento
        st.success("Arquivo carregado com sucesso! Escolha o módulo desejado no menu lateral!")
        
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {str(e)}")
        st.session_state.arquivo_carregado = False
else:
    st.info("Faça o upload do arquivo gerado em: **SIGAA \\ aluno \\ Mapa de conceito**.")
    st.warning("Ou o arquivo **dados/notas_discentes.csv**, se deseja continuar uma sessão anterior.")