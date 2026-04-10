import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils import (
    setup_sidebar_header,
    aplicar_css_padding,
    get_foto_path,
    normalizar_dados,
    create_plotly_chart,
    salvar_dados_sigaa
)

# Configuração da página
st.set_page_config(page_title="Conselho Final", layout="wide")

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

# Adiciona colunas de observações e características se não existirem
if 'Obs_Professor' not in df.columns:
    df['Obs_Professor'] = ''
if 'Caracteristicas_Prof' not in df.columns:
    df['Caracteristicas_Prof'] = ''
st.session_state.df = df

# Controle do índice do estudante atual

# Inicializa índice e slider sincronizados
if "indice_final" not in st.session_state:
    st.session_state.indice_final = 0
if "slider_estudante_final" not in st.session_state:
    st.session_state.slider_estudante_final = 0

# Funções de navegação
def proximo_estudante():
    if st.session_state.slider_estudante_final < len(estudantes) - 1:
        st.session_state.slider_estudante_final += 1

def anterior_estudante():
    if st.session_state.slider_estudante_final > 0:
        st.session_state.slider_estudante_final -= 1

# Linha 1: Seleção de disciplinas (label ao lado do campo)
col_label, col_selector = st.columns([2, 2])
with col_label:
    st.markdown("### 📚 Selecione a(s) disciplina(s)")
with col_selector:
    disciplinas_selecionadas = st.multiselect("", sorted(df["Disciplina"].unique()), key="disciplina_selector", label_visibility="collapsed")

if not disciplinas_selecionadas:
    st.warning("Por favor, selecione pelo menos uma disciplina.")
    st.stop()

# Filtra dados pelas disciplinas selecionadas
dados_disciplinas = df[df["Disciplina"].isin(disciplinas_selecionadas)]

# Lista única de estudantes que cursam essas disciplinas
estudantes = dados_disciplinas.drop_duplicates(subset=["Matricula", "Aluno"])[["Matricula", "Aluno"]].values.tolist()

if not estudantes:
    st.warning("Nenhum estudante encontrado para as disciplinas selecionadas.")
    st.stop()

# Reinicia índice se mudar as disciplinas
# Reinicia índice e slider se mudar as disciplinas
if "disciplinas_atuais" not in st.session_state or st.session_state.disciplinas_atuais != disciplinas_selecionadas:
    st.session_state.disciplinas_atuais = disciplinas_selecionadas
    st.session_state.indice_final = 0
    st.session_state.slider_estudante_final = 0
# Barra de seleção de estudante com slider
st.markdown("**Selecione o estudante:**")

slider_value = st.slider(
    "",
    min_value=0,
    max_value=len(estudantes) - 1,
    value=st.session_state.slider_estudante_final,
    format="Estudante %d de " + str(len(estudantes)),
    label_visibility="collapsed",
    key="slider_estudante_final"
)

# Sincroniza indice_final com slider
if slider_value != st.session_state.indice_final:
    st.session_state.indice_final = slider_value
    st.rerun()

# Estudante atual
matricula, aluno = estudantes[st.session_state.indice_final]

# Linha 2: Nome do estudante com botões de navegação na mesma linha
col_nome, col_anterior, col_proximo = st.columns([4, 2, 2])

with col_nome:
    st.subheader(aluno)

with col_anterior:
    if st.session_state.indice_final > 0:
        st.button("⬅️ Anterior", on_click=anterior_estudante, width="stretch", type="secondary")

with col_proximo:
    if st.session_state.indice_final < len(estudantes) - 1:
        st.button("Próximo ➡️", on_click=proximo_estudante, width="stretch", type="secondary")

# Preparação dos dados do estudante (apenas disciplinas selecionadas)
disciplinas = dados_disciplinas[dados_disciplinas["Matricula"] == matricula].copy()
disciplinas = normalizar_dados(disciplinas)
disciplinas_com_nota = disciplinas[disciplinas['Nota_num'].notna()]

# Busca a observação atual do estudante (apenas das disciplinas selecionadas)
linhas_disciplinas = df[(df['Matricula'] == matricula) & (df['Disciplina'].isin(disciplinas_selecionadas))]
if len(linhas_disciplinas) > 0:
    # Pega a primeira observação não vazia, ou vazio se todas forem vazias
    obs_valores = linhas_disciplinas['Obs_Professor'].dropna().unique()
    obs_atual = obs_valores[0] if len(obs_valores) > 0 and obs_valores[0] != '' else ''
else:
    obs_atual = ''

# Layout em 2 colunas principais: Esquerda (Foto + Gráfico) | Direita (Observações)
col_esquerda, col_direita = st.columns([3, 3])

with col_esquerda:
    # Linha 1: Foto e Gráfico lado a lado
    col_foto, col_grafico = st.columns([1, 2])
    
    with col_foto:
        # Matrícula
        st.caption(f"Matrícula: {matricula}")
        
        # Foto
        st.markdown("")  # Espaçamento
        foto_path = get_foto_path(matricula)
        if foto_path:
            try:
                st.image(foto_path, width=150)
            except Exception:
                st.markdown("👤")
        else:
            st.markdown("👤")
    
    with col_grafico:    
        if not disciplinas_com_nota.empty:
            fig = create_plotly_chart(disciplinas_com_nota)
            fig.update_layout(height=300, width=200)
            st.plotly_chart(fig, use_container_width=False)
        else:
            st.info("Nenhuma nota lançada")

# Coluna direita: Campo de observações
with col_direita:
    st.markdown("**Além das características abaixo, alguma observação?**")
    
    # Campo de texto para observações (usa valor direto do DataFrame)
    observacao = st.text_area(
        "Observações:",
        value=obs_atual,
        height=200,
        key=f"obs_{matricula}",
        label_visibility="collapsed",
        help="Digite suas observações sobre o estudante. Marque as características abaixo."
    )

# CSS para fonte pequena (0.7rem)
# CSS para fonte pequena e checkboxes
st.markdown("""
    <style>
    .caracteristica {
        font-size: 0.7rem;
        line-height: 1.4;
        margin-bottom: 0.3rem;
    }
    .caracteristica-titulo {
        font-weight: bold;
    }
    /* Ajusta tamanho do checkbox */
    .stCheckbox {
        margin-bottom: 0.2rem;
    }
    .stCheckbox > label {
        font-size: 0.85rem;
    }
    </style>
""", unsafe_allow_html=True)

# Listas de características com IDs únicos para tracking
# IDs: POS_XX para positivas, NEG_XX para negativas
# Isso facilita análise de padrões no pedagógico
caracteristicas_positivas = [
    ("POS_01", "Dedicado(a)", "empenha-se persistentemente nas tarefas"),
    ("POS_02", "Responsável", "cumpre prazos e assume compromissos"),
    ("POS_03", "Curioso(a)", "busca ativamente conhecimento e questionamentos"),
    ("POS_04", "Proativo(a)", "antecipa necessidades e inicia soluções"),
    ("POS_05", "Disciplinado(a)", "mantém rotina e método de estudo"),
    ("POS_06", "Criativo(a)", "propõe soluções originais e inovadoras"),
    ("POS_07", "Organizado(a)", "estrutura informações e recursos eficientemente"),
    ("POS_08", "Colaborativo(a)", "trabalha bem em equipe e compartilha conhecimento"),
    ("POS_09", "Resiliente", "recupera-se diante de falhas e contratempos"),
    ("POS_10", "Comunicativo(a)", "expressa ideias com clareza técnica"),
    ("POS_11", "Autônomo(a)", "executa tarefas com independência e critério"),
    ("POS_12", "Persistente", "mantém esforço frente à dificuldade técnica"),
    ("POS_13", "Reflexivo(a)", "avalia e ajusta seu próprio processo de aprendizagem"),
    ("POS_14", "Analítico(a)", "aborda problemas com raciocínio lógico e rigor"),
    ("POS_15", "Adaptável", "ajusta estratégias frente a novas exigências")
]

# IDs negativos indicam níveis de risco para análise pedagógica
# NEG_01-05, NEG_09: Risco moderado | NEG_03, NEG_06-10: Risco alto | NEG_11-15: Risco crítico
caracteristicas_negativas = [
    # Risco Moderado
    ("NEG_01", "⚠️ Indisciplinado(a)", "dificuldade em seguir regras e rotinas", "moderado"),
    ("NEG_02", "⚠️ Desorganizado(a)", "estruturação pobre de tempo e materiais", "moderado"),
    ("NEG_04", "⚠️ Impontual", "não cumpre horários e prazos estabelecidos", "moderado"),
    ("NEG_05", "⚠️ Desatento(a)", "atenção fragmentada em situações de instrução", "moderado"),
    ("NEG_09", "⚠️ Passivo(a)", "espera instruções sem agir por conta própria", "moderado"),
    # Risco Alto
    ("NEG_03", "🔴 Apático(a)", "baixa iniciativa e envolvimento nas atividades", "alto"),
    ("NEG_06", "🔴 Procrastinador(a)", "adia tarefas até prejudicar o desempenho", "alto"),
    ("NEG_07", "🔴 Desinteressado(a)", "não demonstra motivação pelo conteúdo", "alto"),
    ("NEG_08", "🔴 Inconstante", "desempenho flutuante sem padrão estabilizado", "alto"),
    ("NEG_10", "🔴 Irresponsável", "ignora consequências de ações ou omissões", "alto"),
    # Risco Crítico
    ("NEG_11", "🚨 Superficial", "trata conceitos sem aprofundamento técnico", "crítico"),
    ("NEG_12", "🚨 Rígido(a)", "resistência à mudança de método ou ideia", "crítico"),
    ("NEG_13", "🚨 Dependente", "depende excessivamente de orientação externa", "crítico"),
    ("NEG_14", "🚨 Autossabotador(a)", "comportamento que prejudica seu próprio progresso", "crítico"),
    ("NEG_15", "🚨 Desmotivado(a)", "perda persistente de interesse e empenho", "crítico")
]

# Recupera características já salvas para o aluno
caracteristicas_salvas = df.loc[
    (df['Matricula'] == matricula) & (df['Disciplina'].isin(disciplinas_selecionadas)), 
    'Caracteristicas_Prof'
].iloc[0] if len(df[(df['Matricula'] == matricula) & (df['Disciplina'].isin(disciplinas_selecionadas))]) > 0 else ""

# Converte string salva em lista de IDs (verifica se é string válida, não NaN)
caracteristicas_selecionadas = caracteristicas_salvas.split(',') if isinstance(caracteristicas_salvas, str) and caracteristicas_salvas else []

# CSS para reduzir tamanho da fonte dos checkboxes
st.markdown("""
    <style>
    /* Reduz fonte dos labels dos checkboxes */
    div[data-testid="stCheckbox"] label p {
        font-size: 0.7rem !important;
        line-height: 2.5 !important;
        margin-bottom: 0 !important;
    }
    /* Reduz espaçamento entre checkboxes */
    div[data-testid="stCheckbox"] {
        margin-bottom: -1.6rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# Características em 2 colunas
col_positivas, col_negativas = st.columns(2)

with col_positivas:
    st.markdown("<div style='background-color: #d4edda; padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;'><strong>Características Positivas</strong></div>", unsafe_allow_html=True)

    caracteristicas_pos_marcadas = []
    for car_id, palavra, descricao in caracteristicas_positivas:
        checked = st.checkbox(
            f"**{palavra}** — {descricao}",
            value=(car_id in caracteristicas_selecionadas),
            key=f"check_{car_id}_{matricula}"
        )
        if checked:
            caracteristicas_pos_marcadas.append(car_id)

with col_negativas:
    st.markdown("<div style='background-color: #f8d7da; padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;'><strong>Pontos de Atenção</strong></div>", unsafe_allow_html=True)

    caracteristicas_neg_marcadas = []
    for car_id, palavra, descricao, nivel_risco in caracteristicas_negativas:
        checked = st.checkbox(
            f"**{palavra}** — {descricao}",
            value=(car_id in caracteristicas_selecionadas),
            key=f"check_{car_id}_{matricula}"
        )
        if checked:
            caracteristicas_neg_marcadas.append(car_id)

# Combina todas as características marcadas
todas_caracteristicas_marcadas = caracteristicas_pos_marcadas + caracteristicas_neg_marcadas

# Botão de salvar (após processar checkboxes)
st.markdown("---")
col_btn_salvar, col_info_salvar = st.columns([1, 3])
with col_btn_salvar:
    salvar = st.button("💾 Salvar Tudo", type="primary", width="stretch")

with col_info_salvar:
    if len(todas_caracteristicas_marcadas) > 0:
        st.caption(f"📊 {len(todas_caracteristicas_marcadas)} características marcadas ({len(caracteristicas_pos_marcadas)} ✅ | {len(caracteristicas_neg_marcadas)} ⚠️)")
    else:
        st.caption("ℹ️ Nenhuma característica marcada")

if salvar:
    try:
        old_value_obs = obs_atual
        old_value_caract = caracteristicas_salvas
        
        # Converte lista de características em string separada por vírgulas
        caracteristicas_string = ','.join(todas_caracteristicas_marcadas)
        
        # Atualiza as observações e características no DataFrame apenas para as disciplinas selecionadas
        mascara = (df['Matricula'] == matricula) & (df['Disciplina'].isin(disciplinas_selecionadas))
        df.loc[mascara, 'Obs_Professor'] = observacao
        df.loc[mascara, 'Caracteristicas_Prof'] = caracteristicas_string
        st.session_state.df = df
        
        # Registrar no audit log
        import csv
        os.makedirs('dados', exist_ok=True)
        audit_path = 'dados/audit_edits.csv'
        with open(audit_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Registra observação
            writer.writerow([
                datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), 
                'professor', 
                matricula, 
                'Obs_Professor', 
                old_value_obs, 
                observacao, 
                st.session_state.get('session_id', '')
            ])
            # Registra características
            writer.writerow([
                datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), 
                'professor', 
                matricula, 
                'Caracteristicas_Prof', 
                old_value_caract, 
                caracteristicas_string, 
                st.session_state.get('session_id', '')
            ])
        
        # Salva em arquivo CSV com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'dados/backups/notas_discentes_{timestamp}.csv'
        
        # Cria diretório se não existir
        os.makedirs('dados/backups', exist_ok=True)
        
        # Obtém cabeçalho SIGAA da sessão (se existir)
        header_lines = st.session_state.get('sigaa_header', None)
        encoding = st.session_state.get('file_encoding', 'utf-8')
        
        # Salva backup com formato SIGAA
        salvar_dados_sigaa(df, backup_path, header_lines, encoding)
        
        # Atualiza arquivo principal com formato SIGAA
        salvar_dados_sigaa(df, 'dados/notas_discentes.csv', header_lines, encoding)
        
        # Mensagem de sucesso com resumo
        st.success(f"✅ Observações e características salvas com sucesso!")
        st.info(f"📊 Total: {len(todas_caracteristicas_marcadas)} características ({len(caracteristicas_pos_marcadas)} positivas, {len(caracteristicas_neg_marcadas)} pontos de atenção)")
        
    except Exception as e:
        st.error(f"❌ Erro ao salvar: {str(e)}")
    
# Informação sobre onde os dados são salvos
with st.expander("💾 Informações sobre salvamento", expanded=False):
    st.info("""
    - **Observação:** As observações são salvas nas disciplinas selecionadas no início da página
    - **Arquivo principal:** `dados/notas_discentes.csv` (atualizado automaticamente ao salvar)
    - **Backups:** `dados/backups/notas_discentes_YYYYMMDD_HHMMSS.csv` (criado a cada salvamento)
    - **Auditoria:** `dados/audit_edits.csv` (registro de todas as alterações com data/hora)
    """)