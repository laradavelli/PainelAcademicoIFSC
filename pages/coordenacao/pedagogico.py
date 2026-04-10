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
st.set_page_config(page_title="Pedagógico", layout="wide")

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

# Garante a coluna de observações pedagógicas
if 'Obs_Pedagogico' not in df.columns:
    df['Obs_Pedagogico'] = ''
    st.session_state.df = df

# Garante a coluna de características do professor
if 'Caracteristicas_Prof' not in df.columns:
    df['Caracteristicas_Prof'] = ''
    st.session_state.df = df

# Garante a coluna de observações do professor
if 'Obs_Professor' not in df.columns:
    df['Obs_Professor'] = ''
    st.session_state.df = df

# Configuração do padding
st.markdown("""
    <style>
        .block-container {
            padding-top: 2.8rem;
            padding-bottom: 0rem;
        }
    </style>
    """, unsafe_allow_html=True)

# Controle do índice do estudante atual
if "indice_pedagogico" not in st.session_state:
    st.session_state.indice_pedagogico = 0

# Funções de navegação
def proximo_estudante():
    st.session_state.indice_pedagogico += 1
    if "slider_estudante_pedagogico" in st.session_state:
        st.session_state.slider_estudante_pedagogico = st.session_state.indice_pedagogico + 1

def anterior_estudante():
    if st.session_state.indice_pedagogico > 0:
        st.session_state.indice_pedagogico -= 1
        if "slider_estudante_pedagogico" in st.session_state:
            st.session_state.slider_estudante_pedagogico = st.session_state.indice_pedagogico + 1

# Função para calcular o score de risco de um estudante (recorrência: 2+ professores)
def calcular_score_risco(df_aluno):
    caracteristicas_aluno = df_aluno['Caracteristicas_Prof'].dropna().values
    if len(caracteristicas_aluno) == 0:
        return 0

    contador_caracteristicas = {}
    for caract_str in caracteristicas_aluno:
        if caract_str and str(caract_str).strip():
            caracteristicas_prof = [c.strip() for c in str(caract_str).split(',') if c.strip()]
            for caract in caracteristicas_prof:
                contador_caracteristicas[caract] = contador_caracteristicas.get(caract, 0) + 1
    
    todas_caract = [caract for caract, count in contador_caracteristicas.items() if count >= 2]
    todas_caract = list(set(todas_caract))
    
    if not todas_caract:
        return 0
        
    caract_negativas = [c for c in todas_caract if c.startswith('NEG_')]
    caract_criticas = [c for c in caract_negativas if int(c.split('_')[1]) >= 11]
    caract_altas = [c for c in caract_negativas if 6 <= int(c.split('_')[1]) <= 10]
    caract_moderadas = [c for c in caract_negativas if 1 <= int(c.split('_')[1]) <= 5]
    
    score = len(caract_criticas) * 3 + len(caract_altas) * 2 + len(caract_moderadas) * 1
    return score

# Função de score para ordenação: inclui "Alerta Disciplinar" (1 professor) como 0.5
# Garante que alunos com alerta apareçam antes de alunos com score zero real
def calcular_score_ordenacao(df_aluno):
    score_recorrente = calcular_score_risco(df_aluno)
    if score_recorrente > 0:
        return float(score_recorrente)
    
    # Verifica se há características negativas isoladas (alerta disciplinar)
    caracteristicas_aluno = df_aluno['Caracteristicas_Prof'].dropna().values
    contador = {}
    for caract_str in caracteristicas_aluno:
        if caract_str and str(caract_str).strip():
            for c in str(caract_str).split(','):
                c = c.strip()
                if c:
                    contador[c] = contador.get(c, 0) + 1
    
    tem_alerta = any(
        count == 1 and caract.startswith('NEG_')
        for caract, count in contador.items()
    )
    return 0.5 if tem_alerta else 0.0

# Sistema de seleção por Fase, Disciplina ou Discente
col_modo, col_filtro = st.columns([1, 3])

with col_modo:
    st.markdown("### 🔎 Filtrar por:")
    modo_filtro = st.radio("", ["Fase", "Disciplina", "Discente", "Score"], key="modo_filtro", label_visibility="collapsed", horizontal=True)

with col_filtro:
    if modo_filtro == "Fase":
        st.markdown("### 📚 Selecione a(s) fase(s)")
        filtro_selecionado = st.multiselect("", sorted(df["Fase"].unique()), key="fase_selector", label_visibility="collapsed")
        coluna_filtro = "Fase"
    elif modo_filtro == "Disciplina":
        st.markdown("### 📖 Selecione a(s) disciplina(s)")
        filtro_selecionado = st.multiselect("", sorted(df["Disciplina"].unique()), key="disciplina_selector", label_visibility="collapsed")
        coluna_filtro = "Disciplina"
    elif modo_filtro == "Discente":
        st.markdown("### 👤 Selecione o discente")
        alunos_unicos = df.drop_duplicates(subset=["Matricula", "Aluno"]).sort_values("Aluno")
        opcoes_matriculas = [None] + alunos_unicos["Matricula"].tolist()
        mapa_nomes = {row["Matricula"]: f"{row['Aluno']} ({row['Matricula']})" for _, row in alunos_unicos.iterrows()}
        mapa_nomes[None] = "Selecione um estudante..."
        discente_selecionado = st.selectbox("", opcoes_matriculas, format_func=lambda x: mapa_nomes[x], key="discente_selector", label_visibility="collapsed")
    else: # Score
        st.markdown("### 🏆 Estudantes por Score de Risco")
        st.info("Navegue pelos estudantes ordenados do maior para o menor score de risco.")
        filtro_selecionado = None # Não há seleção aqui
        coluna_filtro = None

if modo_filtro == "Discente":
    if discente_selecionado is None:
        st.warning("Por favor, selecione um estudante.")
        st.stop()
    dados_fase = df[df["Matricula"] == discente_selecionado]
    estudantes = dados_fase.drop_duplicates(subset=["Matricula", "Aluno"])[["Matricula", "Aluno"]].values.tolist()
elif modo_filtro == "Score":
    # Pega todos os estudantes únicos do dataframe
    estudantes_unicos = df.drop_duplicates(subset=["Matricula", "Aluno"])[["Matricula", "Aluno"]].values.tolist()
    
    # Calcula o score de ordenação para cada estudante (inclui alerta disciplinar como 0.5)
    estudantes_com_score = []
    for matricula, nome in estudantes_unicos:
        df_aluno = df[df['Matricula'] == matricula]
        score = calcular_score_ordenacao(df_aluno)
        estudantes_com_score.append((matricula, nome, score))
        
    # Ordena pelo score, do maior para o menor
    estudantes_com_score.sort(key=lambda x: x[2], reverse=True)
    
    # Recria a lista de estudantes ordenada
    estudantes = [(matricula, nome) for matricula, nome, score in estudantes_com_score]
    dados_fase = df # Para o restante da página, usa o df completo
else:
    if not filtro_selecionado:
        st.warning(f"Por favor, selecione pelo menos {'uma fase' if modo_filtro == 'Fase' else 'uma disciplina'}.")
        st.stop()
    dados_fase = df[df[coluna_filtro].isin(filtro_selecionado)]
    estudantes = dados_fase.drop_duplicates(subset=["Matricula", "Aluno"])[["Matricula", "Aluno"]].values.tolist()

if not estudantes:
    st.warning("Nenhum estudante encontrado para a seleção.")
    st.stop()

# Garante que o índice está dentro dos limites válidos
st.session_state.indice_pedagogico = max(0, min(st.session_state.indice_pedagogico, len(estudantes) - 1))

# Reinicia índice se mudar o filtro
if modo_filtro == "Discente":
    filtro_key = f"Discente_{discente_selecionado}"
elif modo_filtro == "Score":
    filtro_key = "Score"
else:
    filtro_key = f"{modo_filtro}_{filtro_selecionado}"
if "filtro_atual_pedagogico" not in st.session_state or st.session_state.filtro_atual_pedagogico != filtro_key:
    st.session_state.filtro_atual_pedagogico = filtro_key
    st.session_state.indice_pedagogico = 0

# Slider e navegação só aparecem quando há mais de 1 estudante
if len(estudantes) > 1:
    # Barra de seleção de estudante com slider (1-based para exibição)
    st.markdown("**Selecione o estudante:**")
    indice_selecionado = st.slider(
        "",
        min_value=1,
        max_value=len(estudantes),
        value=st.session_state.indice_pedagogico + 1,
        format="Estudante %d de " + str(len(estudantes)),
        label_visibility="collapsed",
        key="slider_estudante_pedagogico"
    )

    # Converte de volta para 0-based
    st.session_state.indice_pedagogico = indice_selecionado - 1

# Estudante atual
matricula, aluno = estudantes[st.session_state.indice_pedagogico]

# Botões de navegação só quando há mais de 1 estudante
if len(estudantes) > 1:
    col_anterior, col_proximo = st.columns([1, 1])

    with col_anterior:
        if st.session_state.indice_pedagogico > 0:
            st.button("⬅️ Anterior", on_click=anterior_estudante, use_container_width=True, type="secondary")

    with col_proximo:
        if st.session_state.indice_pedagogico < len(estudantes) - 1:
            st.button("Próximo ➡️", on_click=proximo_estudante, use_container_width=True, type="secondary")

# === ANÁLISE DE RISCO PEDAGÓGICO ===

# Inicializa variáveis de score
score_risco = 0
nivel_risco = "BAIXO"
cor_risco = "#32CD32"
emoji_risco = "✅"
recomendacao = "Nenhuma característica avaliada ainda pelos professores."

# Dicionário de características
dict_caract = {
    "POS_01": "Dedicado(a)", "POS_02": "Responsável", "POS_03": "Curioso(a)",
    "POS_04": "Proativo(a)", "POS_05": "Disciplinado(a)", "POS_06": "Criativo(a)",
    "POS_07": "Organizado(a)", "POS_08": "Colaborativo(a)", "POS_09": "Resiliente",
    "POS_10": "Comunicativo(a)", "POS_11": "Autônomo(a)", "POS_12": "Persistente",
    "POS_13": "Reflexivo(a)", "POS_14": "Analítico(a)", "POS_15": "Adaptável",
    "NEG_01": "Indisciplinado(a)", "NEG_02": "Desorganizado(a)", "NEG_03": "Impontual",
    "NEG_04": "Desatento(a)", "NEG_05": "Passivo(a)", "NEG_06": "Apático(a)",
    "NEG_07": "Procrastinador(a)", "NEG_08": "Desinteressado(a)", "NEG_09": "Inconstante",
    "NEG_10": "Irresponsável", "NEG_11": "Superficial", "NEG_12": "Rígido(a)",
    "NEG_13": "Dependente", "NEG_14": "Autossabotador(a)", "NEG_15": "Desmotivado(a)"
}

# Recupera características marcadas pelos professores
caracteristicas_aluno = df[df['Matricula'] == matricula]['Caracteristicas_Prof'].dropna().values

caract_positivas = []
caract_negativas = []
caract_criticas = []
caract_altas = []
caract_moderadas = []
padroes_evasao = []

# Variáveis para alertas de disciplinas isoladas
tem_alerta_disciplina = False
num_disciplinas_alerta = 0
disciplinas_com_alerta = []

# Processa se houver características
if len(caracteristicas_aluno) > 0:
    # Conta quantos professores marcaram cada característica
    contador_caracteristicas = {}
    num_professores_avaliaram = 0
    
    for caract_str in caracteristicas_aluno:
        if caract_str and str(caract_str).strip():
            num_professores_avaliaram += 1
            caracteristicas_prof = [c.strip() for c in str(caract_str).split(',') if c.strip()]
            for caract in caracteristicas_prof:
                contador_caracteristicas[caract] = contador_caracteristicas.get(caract, 0) + 1
    
    # Identifica características isoladas (apenas 1 professor) - ALERTA AMARELO
    caract_isoladas = [caract for caract, count in contador_caracteristicas.items() 
                       if count == 1 and caract.startswith('NEG_')]
    
    if len(caract_isoladas) > 0:
        tem_alerta_disciplina = True
        # Identifica quais disciplinas têm características negativas isoladas
        for idx, caract_str in enumerate(caracteristicas_aluno):
            if caract_str and str(caract_str).strip():
                caract_prof = [c.strip() for c in str(caract_str).split(',') if c.strip()]
                # Verifica se há características isoladas nesta disciplina
                if any(c in caract_isoladas for c in caract_prof if c.startswith('NEG_')):
                    disciplina_nome = df[df['Matricula'] == matricula]['Disciplina'].iloc[idx]
                    if disciplina_nome not in disciplinas_com_alerta:
                        disciplinas_com_alerta.append(disciplina_nome)
        num_disciplinas_alerta = len(disciplinas_com_alerta)
    
    # Filtra características que aparecem em pelo menos 2 professores (recorrência)
    # TODAS as características, incluindo críticas, precisam de recorrência
    todas_caract = []
    for caract, count in contador_caracteristicas.items():
        # Todas as características precisam ter recorrência (2+ professores)
        if count >= 2:
            todas_caract.append(caract)
    
    # Remove duplicatas
    todas_caract = list(set(todas_caract))
    
    # Se realmente tem características após o processamento
    if len(todas_caract) > 0:
        # Separa por tipo
        caract_positivas = [c for c in todas_caract if c.startswith('POS_')]
        caract_negativas = [c for c in todas_caract if c.startswith('NEG_')]
        
        # Análise de risco com base em características recorrentes
        # Moderado: NEG_01 a NEG_05
        # Alto: NEG_06 a NEG_10
        # Crítico: NEG_11 a NEG_15
        caract_criticas = [c for c in caract_negativas if int(c.split('_')[1]) >= 11]
        caract_altas = [c for c in caract_negativas if 6 <= int(c.split('_')[1]) <= 10]
        caract_moderadas = [c for c in caract_negativas if 1 <= int(c.split('_')[1]) <= 5]
        
        # Cálculo do nível de risco
        score_risco = len(caract_criticas) * 3 + len(caract_altas) * 2 + len(caract_moderadas) * 1
        
        # Define nível de risco
        if score_risco >= 8 or len(caract_criticas) >= 3:
            nivel_risco = "CRÍTICO"
            cor_risco = "#8B0000"
            emoji_risco = "🚨"
            recomendacao = "Intervenção urgente necessária. Múltiplos professores reportam problemas graves."
        elif score_risco >= 5 or len(caract_criticas) >= 1:
            nivel_risco = "ALTO"
            cor_risco = "#FF4500"
            emoji_risco = "🔴"
            recomendacao = "Acompanhamento intensivo recomendado. Problemas reportados por diferentes professores."
        elif score_risco >= 2:
            nivel_risco = "MODERADO"
            cor_risco = "#FFA500"
            emoji_risco = "⚠️"
            recomendacao = "Monitoramento regular necessário. Padrão consistente de dificuldades."
        else:
            nivel_risco = "BAIXO"
            cor_risco = "#32CD32"
            emoji_risco = "✅"
            recomendacao = "Estudante apresenta perfil adequado."
        
        # Análise de padrões específicos (também com recorrência)
        if 'NEG_06' in caract_negativas and 'NEG_08' in caract_negativas:
            padroes_evasao.append("Apatia + Desinteresse (padrão recorrente)")
        if 'NEG_14' in caract_negativas or 'NEG_15' in caract_negativas:
            padroes_evasao.append("Desmotivação severa")
        if 'NEG_10' in caract_negativas and 'NEG_01' in caract_negativas:
            padroes_evasao.append("Irresponsabilidade + Indisciplina (padrão recorrente)")

# Controle de abertura automática do modal via session_state
if 'ultima_matricula_pedagogico' not in st.session_state:
    st.session_state.ultima_matricula_pedagogico = None
if 'mostrar_modal_risco' not in st.session_state:
    st.session_state.mostrar_modal_risco = False

# Detecta mudança de estudante para abrir modal automaticamente
estudante_mudou = st.session_state.ultima_matricula_pedagogico != matricula
if estudante_mudou:
    st.session_state.ultima_matricula_pedagogico = matricula
    # Marca para abrir modal se houver risco
    if score_risco >= 2:
        st.session_state.mostrar_modal_risco = True

# === EXIBIÇÃO DE BADGES E ALERTAS ===

# Caso 1: TEM RISCO SISTÊMICO (recorrência) - Exibe nome + badge clicável
if score_risco >= 2:
    # Modal de análise detalhada (define a função primeiro)
    @st.dialog("Análise de Risco")
    def mostrar_analise_risco():
        # Nome do estudante
        st.markdown(f"### 👤 {aluno}")
        
        # Recomendações logo no início
        st.markdown("### 💡 Recomendações")
        
        # Recomendação principal em largura total
        st.info(recomendacao)
        
        # Padrões identificados
        if padroes_evasao:
            st.error(f"**🔍 Padrões identificados:**")
            for padrao in padroes_evasao:
                st.markdown(f"• {padrao}")
        
        # Alertas específicos
        if len(caract_criticas) >= 2:
            st.error("⚠️ **ALERTA:** Múltiplos indicadores críticos detectados!")
        
        # Características em formato de tabela
        st.markdown("### 📋 Características Identificadas")
        
        if len(caract_negativas) > 0 or len(caract_positivas) > 0:
            # Características negativas (pontos de atenção)
            if len(caract_negativas) > 0:
                # Prepara dados para tabela
                max_rows = max(len(caract_moderadas), len(caract_altas), len(caract_criticas))
                
                tabela_html = """
                <table style='width: 100%; border-collapse: collapse; margin-bottom: 1rem;'>
                    <thead>
                        <tr style='background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;'>
                            <th style='padding: 0.75rem; text-align: left; border: 1px solid #dee2e6;'>⚠️ Moderados</th>
                            <th style='padding: 0.75rem; text-align: left; border: 1px solid #dee2e6;'>🔴 Altos</th>
                            <th style='padding: 0.75rem; text-align: left; border: 1px solid #dee2e6;'>🚨 Críticos</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                
                for i in range(max_rows):
                    tabela_html += "<tr>"
                    
                    # Coluna Moderados
                    if i < len(caract_moderadas):
                        tabela_html += f"<td style='padding: 0.5rem; border: 1px solid #dee2e6;'>{dict_caract.get(sorted(caract_moderadas)[i], sorted(caract_moderadas)[i])}</td>"
                    else:
                        tabela_html += "<td style='padding: 0.5rem; border: 1px solid #dee2e6;'>-</td>"
                    
                    # Coluna Altos
                    if i < len(caract_altas):
                        tabela_html += f"<td style='padding: 0.5rem; border: 1px solid #dee2e6; background-color: #fff3cd;'>{dict_caract.get(sorted(caract_altas)[i], sorted(caract_altas)[i])}</td>"
                    else:
                        tabela_html += "<td style='padding: 0.5rem; border: 1px solid #dee2e6;'>-</td>"
                    
                    # Coluna Críticos
                    if i < len(caract_criticas):
                        tabela_html += f"<td style='padding: 0.5rem; border: 1px solid #dee2e6; background-color: #f8d7da;'>{dict_caract.get(sorted(caract_criticas)[i], sorted(caract_criticas)[i])}</td>"
                    else:
                        tabela_html += "<td style='padding: 0.5rem; border: 1px solid #dee2e6;'>-</td>"
                    
                    tabela_html += "</tr>"
                
                tabela_html += "</tbody></table>"
                st.markdown(tabela_html, unsafe_allow_html=True)
            else:
                st.info("✓ Nenhum ponto de atenção identificado")
            
            # Características positivas
            if caract_positivas:
                st.markdown("---")
                st.success(f"**✅ Características Positivas ({len(caract_positivas)})**")
                col_pos1, col_pos2, col_pos3 = st.columns(3)
                caract_pos_list = sorted(caract_positivas)
                terceira_parte = len(caract_pos_list) // 3 + 1
                
                with col_pos1:
                    for c in caract_pos_list[:terceira_parte]:
                        st.markdown(f"• {dict_caract.get(c, c)}")
                with col_pos2:
                    for c in caract_pos_list[terceira_parte:terceira_parte*2]:
                        st.markdown(f"• {dict_caract.get(c, c)}")
                with col_pos3:
                    for c in caract_pos_list[terceira_parte*2:]:
                        st.markdown(f"• {dict_caract.get(c, c)}")
        else:
            st.info("ℹ️ Nenhuma característica registrada ainda pelos professores.")
        
        # Informação sobre onde encontrar detalhes completos
        st.warning("💡 As informações detalhadas estão na tabela **'Observações dos Professores sobre o Aluno'**.")
        
        st.markdown("---")
        st.caption("📊 Esta análise considera apenas características **recorrentes** (marcadas por 2+ professores diferentes), evidenciando padrões de dificuldade do estudante em diferentes disciplinas.")
    
    # Layout: nome à esquerda, badge + botão à direita
    col_nome, col_direita = st.columns([1, 1])
    
    with col_nome:
        st.subheader(aluno)
    
    with col_direita:
        # Subcolunas para badge e botão
        col_badge, col_botao = st.columns([5, 2])
        
        with col_badge:
            st.markdown(f"""
            <div style='padding: inline-block; padding: 0.5rem 1rem; background-color: {cor_risco}20; border-left: 4px solid {cor_risco}; border-radius: 4px;'>
                <div style='font-weight: bold; color: {cor_risco}; font-size: 1.1rem;'>{emoji_risco} Risco {nivel_risco}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_botao:
            if st.button("🔍", use_container_width=True, type="secondary", key=f"btn_risco_{matricula}"):
                st.session_state.mostrar_modal_risco = True
                st.rerun()
    
    # Abre modal via session_state (funciona com reruns do wordcloud)
    if st.session_state.mostrar_modal_risco:
        st.session_state.mostrar_modal_risco = False  # Reset para próxima vez
        mostrar_analise_risco()

# Caso 2: TEM ALERTA EM DISCIPLINA(S) ISOLADA(S) - Nome + Badge amarelo
elif tem_alerta_disciplina:
    col_nome, col_badge = st.columns([1, 1])
    
    with col_nome:
        st.subheader(aluno)
    
    with col_badge:
        # Monta o texto das disciplinas de forma inteligente
        if num_disciplinas_alerta == 1:
            texto_disciplinas = disciplinas_com_alerta[0]
        elif num_disciplinas_alerta == 2:
            texto_disciplinas = f"{disciplinas_com_alerta[0]} e {disciplinas_com_alerta[1]}"
        else:
            texto_disciplinas = f"{', '.join(disciplinas_com_alerta[:2])} e mais {num_disciplinas_alerta - 2}"
        
        st.markdown(f"""
        <div style='padding: 0.5rem 1rem; background-color: #FFF3CD; border-left: 4px solid #FFC107; border-radius: 4px; margin-top: 0.5rem;'>
            <div style='font-weight: bold; color: #856404; font-size: 1.1rem;'>⚠️ Alerta Disciplinar</div>
            <div style='color: #666; font-size: 0.9rem; margin-top: 0.2rem;'>{texto_disciplinas}</div>
        </div>
        """, unsafe_allow_html=True)

# Caso 3: SEM ALERTAS - Nome + Badge verde
else:
    col_nome, col_badge = st.columns([1, 1])
    
    with col_nome:
        st.subheader(aluno)
    
    with col_badge:
        st.markdown(f"""
        <div style='padding: 0.5rem 1rem; background-color: {cor_risco}20; border-left: 4px solid {cor_risco}; border-radius: 4px; margin-top: 0.5rem;'>
            <span style='font-weight: bold; color: {cor_risco}; font-size: 1.1rem;'>{emoji_risco} Risco {nivel_risco}</span>
            <span style='color: #666; font-size: 0.9rem; margin-left: 0.5rem;'>| Score: {score_risco} pts</span>
        </div>
        """, unsafe_allow_html=True)

# Preparação dos dados
disciplinas = dados_fase[dados_fase["Matricula"] == matricula].copy()
disciplinas = normalizar_dados(disciplinas)

# Caminho da foto
foto_path = get_foto_path(matricula)

# Layout em 2 colunas principais: Esquerda (Foto + Gráfico) | Direita (Observações)
col_esquerda, col_direita = st.columns([3, 3])

with col_esquerda:
    # Linha 1: Foto e Gráfico lado a lado
    col_foto, col_grafico = st.columns([1, 2])
    
    with col_foto:
        # Foto
        st.markdown("")  # Espaçamento
        if foto_path:
            try:
                st.image(foto_path, width=150)
            except Exception:
                st.markdown("👤")
        else:
            st.markdown("👤")
        
        # Matrícula abaixo da foto
        st.caption(f"**Matrícula:** {matricula}")
    
    with col_grafico:    
        if not disciplinas.empty:
            fig = create_plotly_chart(disciplinas)
            fig.update_layout(height=300, width=200)
            st.plotly_chart(fig, use_container_width=False)
        else:
            st.info("Nenhuma nota lançada")

# Coluna direita: Wordcloud
with col_direita:
    # === WORDCLOUD DE CARACTERÍSTICAS ===
    # Busca características do estudante selecionado para o wordcloud
    caract_wordcloud = df[df['Matricula'] == matricula]['Caracteristicas_Prof'].dropna().values

    # Conta frequência de cada característica
    contador_wordcloud = {}
    for caract_str in caract_wordcloud:
        if caract_str and str(caract_str).strip():
            caracteristicas_prof = [c.strip() for c in str(caract_str).split(',') if c.strip()]
            for caract in caracteristicas_prof:
                contador_wordcloud[caract] = contador_wordcloud.get(caract, 0) + 1

    if contador_wordcloud:
        import streamlit_wordcloud as wordcloud_component
        
        # Dicionário para traduzir IDs para nomes legíveis (sem emojis para o wordcloud)
        dict_caract_wordcloud = {
            "POS_01": "Dedicado(a)", "POS_02": "Responsável", "POS_03": "Curioso(a)",
            "POS_04": "Proativo(a)", "POS_05": "Disciplinado(a)", "POS_06": "Criativo(a)",
            "POS_07": "Organizado(a)", "POS_08": "Colaborativo(a)", "POS_09": "Resiliente",
            "POS_10": "Comunicativo(a)", "POS_11": "Autônomo(a)", "POS_12": "Persistente",
            "POS_13": "Reflexivo(a)", "POS_14": "Analítico(a)", "POS_15": "Adaptável",
            "NEG_01": "Indisciplinado(a)", "NEG_02": "Desorganizado(a)", "NEG_03": "Impontual",
            "NEG_04": "Desatento(a)", "NEG_05": "Passivo(a)", "NEG_06": "Apático(a)",
            "NEG_07": "Procrastinador(a)", "NEG_08": "Desinteressado(a)", "NEG_09": "Inconstante",
            "NEG_10": "Irresponsável", "NEG_11": "Superficial", "NEG_12": "Rígido(a)",
            "NEG_13": "Dependente", "NEG_14": "Autossabotador(a)", "NEG_15": "Desmotivado(a)"
        }
        
        # Prepara lista de palavras para o wordcloud
        words = []
        for caract_id, count in contador_wordcloud.items():
            nome = dict_caract_wordcloud.get(caract_id, caract_id)
            
            # Define cor baseada no tipo (positiva=verde, negativa=vermelho/laranja)
            if caract_id.startswith('POS_'):
                color = "#28a745"  # Verde
                tipo = "Positiva"
            elif caract_id.startswith('NEG_') and int(caract_id.split('_')[1]) <= 5:
                color = "#ffc107"  # Amarelo (alertas leves)
                tipo = "Alerta Leve"
            elif caract_id.startswith('NEG_') and int(caract_id.split('_')[1]) <= 10:
                color = "#fd7e14"  # Laranja (alertas moderados)
                tipo = "Alerta Moderado"
            else:
                color = "#dc3545"  # Vermelho (alertas críticos)
                tipo = "Alerta Crítico"
            
            # Usa contagem direta como valor - os parâmetros font_min/font_max controlam o tamanho visual
            # O componente escala automaticamente os valores para o range de fontes definido
            value = count
            
            words.append(dict(
                text=nome,
                value=int(value),
                color=color,
                tipo=tipo,
                professores=f"{count} professor(es)"
            ))
        
        # Renderiza o wordcloud em um fragment para não causar rerun da página inteira
        @st.fragment
        def render_wordcloud():
            wordcloud_component.visualize(
                words,
                tooltip_data_fields={'text': 'Característica', 'professores': 'Avaliações', 'tipo': 'Tipo'},
                per_word_coloring=True,
                height=250,
                font_min=14,
                font_max=60,
                font_scale=15
            )
        
        render_wordcloud()
    else:
        st.info("Nenhuma observação ou característica de professor registrada ainda para este aluno")

# === MURAL DE COMENTÁRIOS DOS DOCENTES ===
import html as _html

# Dicionário para traduzir IDs de características nos cards
_dict_caract_cards = {
    "POS_01": ("Dedicado(a)", "#28a745"), "POS_02": ("Responsável", "#28a745"), "POS_03": ("Curioso(a)", "#28a745"),
    "POS_04": ("Proativo(a)", "#28a745"), "POS_05": ("Disciplinado(a)", "#28a745"), "POS_06": ("Criativo(a)", "#28a745"),
    "POS_07": ("Organizado(a)", "#28a745"), "POS_08": ("Colaborativo(a)", "#28a745"), "POS_09": ("Resiliente", "#28a745"),
    "POS_10": ("Comunicativo(a)", "#28a745"), "POS_11": ("Autônomo(a)", "#28a745"), "POS_12": ("Persistente", "#28a745"),
    "POS_13": ("Reflexivo(a)", "#28a745"), "POS_14": ("Analítico(a)", "#28a745"), "POS_15": ("Adaptável", "#28a745"),
    "NEG_01": ("Indisciplinado(a)", "#ffc107"), "NEG_02": ("Desorganizado(a)", "#ffc107"), "NEG_03": ("Impontual", "#ffc107"),
    "NEG_04": ("Desatento(a)", "#ffc107"), "NEG_05": ("Passivo(a)", "#ffc107"), "NEG_06": ("Apático(a)", "#fd7e14"),
    "NEG_07": ("Procrastinador(a)", "#fd7e14"), "NEG_08": ("Desinteressado(a)", "#fd7e14"), "NEG_09": ("Inconstante", "#fd7e14"),
    "NEG_10": ("Irresponsável", "#fd7e14"), "NEG_11": ("Superficial", "#dc3545"), "NEG_12": ("Rígido(a)", "#dc3545"),
    "NEG_13": ("Dependente", "#dc3545"), "NEG_14": ("Autossabotador(a)", "#dc3545"), "NEG_15": ("Desmotivado(a)", "#dc3545")
}

obs_docentes = df[df['Matricula'] == matricula][['Disciplina', 'Obs_Professor', 'Caracteristicas_Prof']].copy()
obs_docentes = obs_docentes[
    (obs_docentes['Obs_Professor'].notna() & (obs_docentes['Obs_Professor'].astype(str).str.strip() != '')) |
    (obs_docentes['Caracteristicas_Prof'].notna() & (obs_docentes['Caracteristicas_Prof'].astype(str).str.strip() != ''))
]

if not obs_docentes.empty:
    st.markdown("**📝 Observações dos Docentes:**")

    cards_html = '<div style="max-height: 320px; overflow-y: auto; padding-right: 0.5rem;">'
    for _, row in obs_docentes.iterrows():
        disciplina = _html.escape(str(row['Disciplina']))
        obs_raw = str(row['Obs_Professor']).strip() if pd.notna(row['Obs_Professor']) else ''
        obs = _html.escape(obs_raw) if obs_raw else ''
        caract_raw = str(row['Caracteristicas_Prof']).strip() if pd.notna(row['Caracteristicas_Prof']) else ''

        # Monta badges de características
        badges_html = ''
        if caract_raw:
            ids = [c.strip() for c in caract_raw.split(',') if c.strip()]
            for cid in ids:
                nome, cor = _dict_caract_cards.get(cid, (cid, '#6c757d'))
                badges_html += (
                    f'<span style="display:inline-block; background-color:{cor}18; color:{cor}; '
                    f'border:1px solid {cor}50; border-radius:3px; padding:0.1rem 0.4rem; '
                    f'font-size:0.7rem; margin:0.15rem 0.2rem 0.15rem 0;">{_html.escape(nome)}</span>'
                )

        cards_html += (
            '<div style="background-color: #f8f9fa; border-left: 3px solid #4a90d9; '
            'border-radius: 4px; padding: 0.6rem 0.8rem; margin-bottom: 0.5rem;">'
            f'<div style="font-size: 0.75rem; color: #6c757d; font-weight: 600; '
            f'margin-bottom: 0.3rem;">📖 {disciplina}</div>'
        )
        if obs:
            cards_html += f'<div style="font-size: 0.85rem; color: #333; line-height: 1.4; margin-bottom: 0.3rem;">{obs}</div>'
        if badges_html:
            cards_html += f'<div style="line-height: 1.8;">{badges_html}</div>'
        cards_html += '</div>'
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)
    st.markdown("")

# === CAMPO DE OBSERVAÇÕES PEDAGÓGICAS (largura total) ===
st.markdown("**Observações Pedagógicas:**")

# Busca a observação atual do estudante
current_obs_val = df.loc[df['Matricula'] == matricula, 'Obs_Pedagogico'].iat[0]
current_obs = str(current_obs_val) if pd.notna(current_obs_val) else ""
novo_text = st.text_area('Observação pedagógica', value=current_obs, height=150, key=f"obs_ped_{matricula}", label_visibility="collapsed")

col_salvar, col_pdf = st.columns([1, 1])

with col_salvar:
    if st.button('💾 Salvar', type="primary", use_container_width=True):
        try:
            old_value = current_obs
            df.loc[df['Matricula'] == matricula, 'Obs_Pedagogico'] = novo_text
            st.session_state.df = df

            # Registrar no audit log
            import csv
            os.makedirs('dados', exist_ok=True)
            audit_path = 'dados/audit_edits.csv'
            with open(audit_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), 
                    'pedagogo', 
                    matricula, 
                    'Obs_Pedagogico', 
                    old_value, 
                    novo_text, 
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
            
            st.success(f"✅ Salvo!")
            
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")

with col_pdf:
    # Gera PDF inline para download direto
    try:
        from fpdf import FPDF

        # Sanitiza texto para compatibilidade com Helvetica (windows-1252)
        def _t(text):
            if not text or str(text).strip() == '':
                return '-'
            s = str(text).strip()
            _repl = {
                '\u2013': '-', '\u2014': '-', '\u2018': "'", '\u2019': "'",
                '\u201c': '"', '\u201d': '"', '\u2026': '...', '\u2022': '-',
                '\u00a0': ' ', '\u200b': '', '\ufeff': '',
            }
            for old, new in _repl.items():
                s = s.replace(old, new)
            result = []
            for ch in s:
                try:
                    ch.encode('windows-1252')
                    result.append(ch)
                except UnicodeEncodeError:
                    result.append('?')
            return ''.join(result) or '-'

        _dict_pdf = {
            "POS_01": "Dedicado(a)", "POS_02": "Responsavel", "POS_03": "Curioso(a)",
            "POS_04": "Proativo(a)", "POS_05": "Disciplinado(a)", "POS_06": "Criativo(a)",
            "POS_07": "Organizado(a)", "POS_08": "Colaborativo(a)", "POS_09": "Resiliente",
            "POS_10": "Comunicativo(a)", "POS_11": "Autonomo(a)", "POS_12": "Persistente",
            "POS_13": "Reflexivo(a)", "POS_14": "Analitico(a)", "POS_15": "Adaptavel",
            "NEG_01": "Indisciplinado(a) [Moderado]", "NEG_02": "Desorganizado(a) [Moderado]",
            "NEG_03": "Impontual [Moderado]", "NEG_04": "Desatento(a) [Moderado]",
            "NEG_05": "Passivo(a) [Moderado]", "NEG_06": "Apatico(a) [Alto]",
            "NEG_07": "Procrastinador(a) [Alto]", "NEG_08": "Desinteressado(a) [Alto]",
            "NEG_09": "Inconstante [Alto]", "NEG_10": "Irresponsavel [Alto]",
            "NEG_11": "Superficial [Critico]", "NEG_12": "Rigido(a) [Critico]",
            "NEG_13": "Dependente [Critico]", "NEG_14": "Autossabotador(a) [Critico]",
            "NEG_15": "Desmotivado(a) [Critico]"
        }

        # Imagens de cabeçalho e rodapé institucionais
        _cabecalho_img = os.path.join("assets", "cabecalho.png")
        _rodape_img = os.path.join("assets", "rodape.png")

        class _PDFRelatorio(FPDF):
            def header(self):
                if os.path.exists(_cabecalho_img):
                    self.image(_cabecalho_img, x=10, y=5, w=190)
                    self.set_y(30)

            def footer(self):
                if os.path.exists(_rodape_img):
                    self.set_y(-25)
                    self.image(_rodape_img, x=10, w=190)

        pdf = _PDFRelatorio(orientation="P", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=30)
        lm = pdf.l_margin

        # Helper: reseta X para margem esquerda e escreve com multi_cell
        def _write(txt, font="Helvetica", style="", size=10, h=6):
            pdf.set_x(lm)
            pdf.set_font(font, style, size)
            pdf.multi_cell(w=0, h=h, text=_t(txt))

        def _section(title):
            pdf.ln(4)
            pdf.set_x(lm)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(w=0, h=8, text=title, new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(70, 130, 180)
            pdf.line(lm, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(3)

        # ---- Titulo ----
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(w=0, h=10, text="RELATORIO PEDAGÓGICO DO ESTUDANTE", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(w=0, h=5, text=f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", new_x="LMARGIN", new_y="NEXT", align="C")

        # ---- Dados do Estudante ----
        _section("Dados do Estudante")
        _write(f"Nome: {aluno}")
        _write(f"Matricula: {matricula}")

        # ---- Analise de Risco ----
        _section("Analise de Risco Pedagogico")
        _write(f"Nivel de Risco: {nivel_risco} (Score: {score_risco} pts)")
        _write(f"Recomendacao: {recomendacao}")
        if padroes_evasao:
            _write(f"Padroes identificados: {'; '.join(padroes_evasao)}")

        if caract_positivas or caract_negativas:
            pdf.ln(2)
            _write("(Apenas caracteristicas marcadas por 2+ professores)", size=9, style="I", h=5)
            if caract_positivas:
                nomes_pos = [_dict_pdf.get(c, c) for c in sorted(caract_positivas)]
                _write(f"Positivas recorrentes: {', '.join(nomes_pos)}")
            if caract_negativas:
                nomes_neg = [_dict_pdf.get(c, c) for c in sorted(caract_negativas)]
                _write(f"Negativas recorrentes: {', '.join(nomes_neg)}")

        # ---- Desempenho Academico ----
        _section("Desempenho Academico")
        dados_aluno = df[df['Matricula'] == matricula][['Disciplina', 'Nota', 'Infrequencia']].copy()
        epw = pdf.w - lm - pdf.r_margin
        w_disc = epw * 0.55
        w_nota = epw * 0.20
        w_freq = epw * 0.25
        pdf.set_x(lm)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(w_disc, 6, "Disciplina", border=1)
        pdf.cell(w_nota, 6, "Nota", border=1, align="C")
        pdf.cell(w_freq, 6, "Faltas", border=1, align="C")
        pdf.ln()
        pdf.set_font("Helvetica", "", 8)
        for _, r in dados_aluno.iterrows():
            disc = _t(r['Disciplina'])
            max_w = w_disc - 2
            if pdf.get_string_width(disc) > max_w:
                while len(disc) > 3 and pdf.get_string_width(disc + '..') > max_w:
                    disc = disc[:-1]
                disc = disc + '..'
            nota = _t(r.get('Nota', '-'))
            faltas = _t(r.get('Infrequencia', '-'))
            pdf.set_x(lm)
            pdf.cell(w_disc, 6, disc, border=1)
            pdf.cell(w_nota, 6, nota, border=1, align="C")
            pdf.cell(w_freq, 6, faltas, border=1, align="C")
            pdf.ln()

        # ---- Observacoes dos Docentes ----
        _section("Observacoes dos Docentes")
        obs_pdf = df[df['Matricula'] == matricula][['Disciplina', 'Obs_Professor', 'Caracteristicas_Prof']].copy()
        obs_pdf = obs_pdf[
            (obs_pdf['Obs_Professor'].notna() & (obs_pdf['Obs_Professor'].astype(str).str.strip() != '')) |
            (obs_pdf['Caracteristicas_Prof'].notna() & (obs_pdf['Caracteristicas_Prof'].astype(str).str.strip() != ''))
        ]

        if not obs_pdf.empty:
            for _, r in obs_pdf.iterrows():
                disc = _t(r['Disciplina'])
                obs_t = _t(r['Obs_Professor']) if pd.notna(r['Obs_Professor']) and str(r['Obs_Professor']).strip() else ''
                caract_t = str(r['Caracteristicas_Prof']).strip() if pd.notna(r['Caracteristicas_Prof']) else ''

                _write(disc, style="B", size=10, h=6)

                if obs_t and obs_t != '-':
                    _write(obs_t, size=9, h=5)

                if caract_t:
                    nomes = [_dict_pdf.get(c.strip(), c.strip()) for c in caract_t.split(',') if c.strip()]
                    if nomes:
                        _write(f"Caracteristicas: {', '.join(nomes)}", style="I", size=9, h=5)
                pdf.ln(2)
        else:
            _write("Nenhuma observacao registrada pelos docentes.", style="I")

        # ---- Observacao Pedagogica ----
        _section("Observacao Pedagogica")
        obs_ped_text = novo_text.strip() if novo_text.strip() else current_obs.strip()
        if obs_ped_text:
            _write(obs_ped_text)
        else:
            _write("Nenhuma observacao pedagogica registrada.", style="I")

        # Gera PDF
        pdf_bytes = bytes(pdf.output())
        nome_arquivo = f"relatorio_pedagogico_{matricula}_{datetime.now().strftime('%Y%m%d')}.pdf"
        st.download_button(
            label="📄 Baixar PDF",
            data=pdf_bytes,
            file_name=nome_arquivo,
            mime="application/pdf",
            use_container_width=True,
            type="secondary"
        )

    except Exception as e:
        st.error(f"❌ Erro ao gerar PDF: {str(e)}")

# === RELATÓRIO ESTATÍSTICO DA TURMA ===
with st.expander("📊 Relatório Estatístico da Turma", expanded=False):
    # Analisa todas as características da fase selecionada
    todas_caracteristicas_fase = dados_fase['Caracteristicas_Prof'].dropna()

    if len(todas_caracteristicas_fase) > 0:
        # Processa todas as características
        contador_caract = {}
        alunos_com_caract = set()
        
        for idx, caract_str in todas_caracteristicas_fase.items():
            if caract_str:
                aluno_atual = dados_fase.loc[idx, 'Matricula']
                alunos_com_caract.add(aluno_atual)
                
                for caract in caract_str.split(','):
                    if caract:
                        contador_caract[caract] = contador_caract.get(caract, 0) + 1
        
        # Separa por tipo
        pos_contador = {k: v for k, v in contador_caract.items() if k.startswith('POS_')}
        neg_contador = {k: v for k, v in contador_caract.items() if k.startswith('NEG_')}
        
        # Análise de risco da turma
        total_alunos = len(estudantes)
        alunos_avaliados = len(alunos_com_caract)
        
        # Conta alunos por nível de risco
        alunos_risco_critico = 0
        alunos_risco_alto = 0
        alunos_risco_moderado = 0
        alunos_risco_baixo = 0
        
        for matricula_aluno, _ in estudantes:
            caract_aluno = dados_fase[dados_fase['Matricula'] == matricula_aluno]['Caracteristicas_Prof'].dropna().values
            if len(caract_aluno) > 0:
                # Conta quantos professores marcaram cada característica
                contador_caract_aluno = {}
                for c_str in caract_aluno:
                    if c_str:
                        caracteristicas_prof = [c.strip() for c in c_str.split(',') if c.strip()]
                        for caract in caracteristicas_prof:
                            contador_caract_aluno[caract] = contador_caract_aluno.get(caract, 0) + 1
                
                # Filtra características recorrentes (2+ professores)
                # TODAS as características precisam de recorrência
                caract_recorrentes = []
                for caract, count in contador_caract_aluno.items():
                    if count >= 2:
                        caract_recorrentes.append(caract)
                
                # Calcula score baseado em características recorrentes
                caract_neg = [c for c in caract_recorrentes if c.startswith('NEG_')]
                caract_crit = [c for c in caract_neg if int(c.split('_')[1]) >= 11]
                caract_alt = [c for c in caract_neg if 6 <= int(c.split('_')[1]) <= 10]
                caract_mod = [c for c in caract_neg if 1 <= int(c.split('_')[1]) <= 5]
                
                score = len(caract_crit) * 3 + len(caract_alt) * 2 + len(caract_mod) * 1
                
                if score >= 8 or len(caract_crit) >= 3:
                    alunos_risco_critico += 1
                elif score >= 5 or len(caract_crit) >= 1:
                    alunos_risco_alto += 1
                elif score >= 2:
                    alunos_risco_moderado += 1
                else:
                    alunos_risco_baixo += 1
        
        # Exibe métricas gerais
        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
        
        with col_m1:
            st.metric("Total de Alunos", total_alunos)
        with col_m2:
            st.metric("Avaliados", alunos_avaliados, 
                      delta=f"{(alunos_avaliados/total_alunos*100):.0f}%")
        with col_m3:
            st.metric("🚨 Risco Crítico", alunos_risco_critico,
                      delta="Urgente" if alunos_risco_critico > 0 else None,
                      delta_color="inverse")
        with col_m4:
            st.metric("🔴 Risco Alto", alunos_risco_alto)
        with col_m5:
            st.metric("⚠️ Risco Moderado", alunos_risco_moderado)
        
        # Gráficos e análises
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.markdown("<div style='background-color: #fff3cd; padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;'><strong>Top 5 Pontos de Atenção Mais Frequentes</strong></div>", unsafe_allow_html=True)
            if neg_contador:
                top_neg = sorted(neg_contador.items(), key=lambda x: x[1], reverse=True)[:5]
                
                dict_caract = {
                    "NEG_01": "Indisciplinado(a)", "NEG_02": "Desorganizado(a)", "NEG_03": "Impontual",
                    "NEG_04": "Desatento(a)", "NEG_05": "Passivo(a)", "NEG_06": "Apático(a)",
                    "NEG_07": "Procrastinador(a)", "NEG_08": "Desinteressado(a)", "NEG_09": "Inconstante",
                    "NEG_10": "Irresponsável", "NEG_11": "Superficial", "NEG_12": "Rígido(a)",
                    "NEG_13": "Dependente", "NEG_14": "Autossabotador(a)", "NEG_15": "Desmotivado(a)"
                }
                
                for caract_id, count in top_neg:
                    nivel = "🚨" if int(caract_id.split('_')[1]) >= 11 else "🔴" if int(caract_id.split('_')[1]) >= 6 else "⚠️"
                    percentual = (count / alunos_avaliados * 100) if alunos_avaliados > 0 else 0
                    st.markdown(f"{nivel} **{dict_caract.get(caract_id, caract_id)}**: {count} alunos ({percentual:.0f}%)")
            else:
                st.info("Nenhum ponto de atenção registrado")
        
        with col_graf2:
            st.markdown("<div style='background-color: #d4edda; padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;'><strong>Top 5 Características Positivas Mais Frequentes</strong></div>", unsafe_allow_html=True)
            if pos_contador:
                top_pos = sorted(pos_contador.items(), key=lambda x: x[1], reverse=True)[:5]
                
                dict_caract_pos = {
                    "POS_01": "Dedicado(a)", "POS_02": "Responsável", "POS_03": "Curioso(a)",
                    "POS_04": "Proativo(a)", "POS_05": "Disciplinado(a)", "POS_06": "Criativo(a)",
                    "POS_07": "Organizado(a)", "POS_08": "Colaborativo(a)", "POS_09": "Resiliente",
                    "POS_10": "Comunicativo(a)", "POS_11": "Autônomo(a)", "POS_12": "Persistente",
                    "POS_13": "Reflexivo(a)", "POS_14": "Analítico(a)", "POS_15": "Adaptável"
                }
                
                for caract_id, count in top_pos:
                    percentual = (count / alunos_avaliados * 100) if alunos_avaliados > 0 else 0
                    st.markdown(f"✅ **{dict_caract_pos.get(caract_id, caract_id)}**: {count} alunos ({percentual:.0f}%)")
            else:
                st.info("Nenhuma característica positiva registrada")
        
        # Alerta de intervenção
        if alunos_risco_critico > 0 or alunos_risco_alto >= 3:
            st.error(f"""
            ⚠️ **ATENÇÃO PEDAGÓGICA NECESSÁRIA:**
            - {alunos_risco_critico} aluno(s) em risco crítico de evasão
            - {alunos_risco_alto} aluno(s) em risco alto
            - Recomenda-se reunião pedagógica urgente para planejamento de intervenções
            """)
        elif alunos_risco_moderado >= 5:
            st.warning(f"""
            📋 **Monitoramento recomendado:**
            - {alunos_risco_moderado} aluno(s) apresentam pontos de atenção que requerem acompanhamento
            """)

    else:
        st.info("📊 Nenhuma característica foi registrada ainda. As análises aparecerão quando os professores preencherem as avaliações na página 'Conselho Final'.")

# CSS para fonte pequena (0.7rem)
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
        </style>
    """, unsafe_allow_html=True)

# Listas de características com descrições
caracteristicas_positivas = [
    ("Dedicado(a)", "empenha-se persistentemente nas tarefas"),
    ("Responsável", "cumpre prazos e assume compromissos"),
    ("Curioso(a)", "busca ativamente conhecimento e questionamentos"),
    ("Proativo(a)", "antecipa necessidades e inicia soluções"),
    ("Disciplinado(a)", "mantém rotina e método de estudo"),
    ("Criativo(a)", "propõe soluções originais e inovadoras"),
    ("Organizado(a)", "estrutura informações e recursos eficientemente"),
    ("Colaborativo(a)", "trabalha bem em equipe e compartilha conhecimento"),
    ("Resiliente", "recupera-se diante de falhas e contratempos"),
    ("Comunicativo(a)", "expressa ideias com clareza técnica"),
    ("Autônomo(a)", "executa tarefas com independência e critério"),
    ("Persistente", "mantém esforço frente à dificuldade técnica"),
    ("Reflexivo(a)", "avalia e ajusta seu próprio processo de aprendizagem"),
    ("Analítico(a)", "aborda problemas com raciocínio lógico e rigor"),
    ("Adaptável", "ajusta estratégias frente a novas exigências")
]

caracteristicas_negativas = [
    # Risco Moderado (NEG_01 a NEG_05)
    ("⚠️ Indisciplinado(a)", "dificuldade em seguir regras e rotinas"),
    ("⚠️ Desorganizado(a)", "estruturação pobre de tempo e materiais"),
    ("⚠️ Impontual", "não cumpre horários e prazos estabelecidos"),
    ("⚠️ Desatento(a)", "atenção fragmentada em situações de instrução"),
    ("⚠️ Passivo(a)", "espera instruções sem agir por conta própria"),
    # Risco Alto (NEG_06 a NEG_10)
    ("🔴 Apático(a)", "baixa iniciativa e envolvimento nas atividades"),
    ("🔴 Procrastinador(a)", "adia tarefas até prejudicar o desempenho"),
    ("🔴 Desinteressado(a)", "não demonstra motivação pelo conteúdo"),
    ("🔴 Inconstante", "desempenho flutuante sem padrão estabilizado"),
    ("🔴 Irresponsável", "ignora consequências de ações ou omissões"),
    # Risco Crítico (NEG_11 a NEG_15)
    ("🚨 Superficial", "trata conceitos sem aprofundamento técnico"),
    ("🚨 Rígido(a)", "resistência à mudança de método ou ideia"),
    ("🚨 Dependente", "depende excessivamente de orientação externa"),
    ("🚨 Autossabotador(a)", "comportamento que prejudica seu próprio progresso"),
    ("🚨 Desmotivado(a)", "perda persistente de interesse e empenho")
]

# Características em expander
with st.expander("📚 Características usadas como referências peles Professores", expanded=False):
    # Características em 2 colunas
    col_positivas, col_negativas = st.columns(2)
    
    with col_positivas:
        st.markdown("<div style='font-size: 0.9rem; font-weight: bold; color: #28a745;'>✅ Características Positivas</div>", unsafe_allow_html=True)
        for palavra, descricao in caracteristicas_positivas:
            st.markdown(f"<div class='caracteristica'><span class='caracteristica-titulo'>{palavra}</span> — {descricao}</div>", unsafe_allow_html=True)
    
    with col_negativas:
        st.markdown("<div style='font-size: 0.9rem; font-weight: bold; color: #dc3545;'>⚠️ Pontos de Atenção</div>", unsafe_allow_html=True)
        for palavra, descricao in caracteristicas_negativas:
            st.markdown(f"<div class='caracteristica'><span class='caracteristica-titulo'>{palavra}</span> — {descricao}</div>", unsafe_allow_html=True)

# Informação sobre as características em 3 colunas
with st.expander("📋 Dicionário de Características", expanded=False):
    col_mod, col_alt, col_crit = st.columns(3)
    
    with col_mod:
        st.info("""
        **⚠️ Risco Moderado**  
        **(1 ponto cada)**
        
        - **NEG_01:** Indisciplinado(a)
        - **NEG_02:** Desorganizado(a)
        - **NEG_03:** Impontual
        - **NEG_04:** Desatento(a)
        - **NEG_05:** Passivo(a)
        """)
    
    with col_alt:
        st.warning("""
        **🔴 Risco Alto**  
        **(2 pontos cada)**
        
        - **NEG_06:** Apático(a)
        - **NEG_07:** Procrastinador(a)
        - **NEG_08:** Desinteressado(a)
        - **NEG_09:** Inconstante
        - **NEG_10:** Irresponsável
        """)
    
    with col_crit:
        st.error("""
        **🚨 Risco Crítico**  
        **(3 pontos cada)**
        
        - **NEG_11:** Superficial
        - **NEG_12:** Rígido(a)
        - **NEG_13:** Dependente
        - **NEG_14:** Autossabotador(a)
        - **NEG_15:** Desmotivado(a)
        """)

# Explicação sobre a análise de risco em expander
with st.expander("📊 Como funciona a Análise de Risco?", expanded=False):
    st.info("""
**Metodologia de Avaliação de Risco Pedagógico:**

A análise de risco é calculada automaticamente com base nas características marcadas pelos professores na página **'Conselho Final'**. 

**IMPORTANTE:** O sistema considera apenas características **recorrentes** - ou seja, aquelas identificadas por **2 ou mais professores** diferentes.

**Critério de Recorrência:**
- **TODAS as características** (moderadas, altas e críticas): precisam ser marcadas por **pelo menos 2 professores diferentes**
- Objetivo: identificar problemas sistêmicos do curso, não dificuldades isoladas em uma disciplina específica
- Mesmo características graves só aparecem na análise se forem confirmadas por múltiplos professores

---

**Sistema de Três Níveis de Alerta:**

O sistema diferencia três cenários distintos de acompanhamento pedagógico:

**Nível 1 - 🔴 Risco Sistêmico (Badge Vermelho/Laranja com Botão de Análise)**
- Acionado quando: Score de risco ≥ 2 (características recorrentes em múltiplos professores)
- Indica: Problemas identificados por 2 ou mais professores em disciplinas diferentes
- Ação: Exibe badge de risco + botão "Ver Análise de Risco" + modal automático com análise completa
- Interpretação: Questão sistêmica que requer intervenção coordenada do curso

**Nível 2 - ⚠️ Alerta Disciplinar (Badge Amarelo, sem modal)**
- Acionado quando: Características negativas identificadas por apenas 1 professor
- Indica: Dificuldade específica em uma ou mais disciplinas isoladas
- Ação: Exibe badge amarelo com nome da(s) disciplina(s) afetada(s)
- Interpretação: Problema pontual que requer investigação de contexto (pode ser questão metodológica, de afinidade ou característica real do aluno)

**Nível 3 - ✅ Sem Alertas (Badge Verde)**
- Badge Verde: Aluno avaliado com características positivas ou sem pontos de atenção
- Ação: Apenas exibição do status, sem modal ou botões adicionais

**Fluxo de Decisão:**
1. Sistema conta quantos professores marcaram cada característica negativa
2. Se alguma característica aparece 2+ vezes → **Nível 1** (Risco Sistêmico)
3. Se todas aparecem apenas 1 vez → **Nível 2** (Alerta Disciplinar)
4. Se não há características negativas → **Nível 3** (Sem Alertas)

---

**Filtro "Score" — Navegação Global por Prioridade:**

Ao selecionar o filtro **Score**, todos os estudantes do arquivo são listados globalmente (independente de fase ou disciplina), ordenados pela prioridade de atendimento:

| Prioridade | Score de ordenação | Critério |
|------------|--------------------|---------|
| 1ª | ≥ 1 (valor real) | Risco recorrente confirmado por 2+ professores |
| 2ª | 0,5 | Alerta Disciplinar — 1 professor sinalizou algo negativo |
| 3ª | 0,0 | Sem nenhuma observação negativa |

Isso garante que estudantes com Alerta Disciplinar sempre precedam estudantes sem qualquer sinalização, mesmo que ambos tenham score formal zero. Ao clicar em "Próximo", o setor pedagógico percorre automaticamente os casos mais críticos primeiro.

---

**Pesos das Características:**

Cada característica negativa possui um peso específico de acordo com sua gravidade:

- **⚠️ Pontos Moderados** (NEG_01 a NEG_05): **1 ponto** cada
- **🔴 Pontos Altos** (NEG_06 a NEG_10): **2 pontos** cada  
- **🚨 Pontos Críticos** (NEG_11 a NEG_15): **3 pontos** cada

**Classificação de Risco:**
- **🚨 CRÍTICO** (Score ≥ 8 ou ≥ 3 características críticas): Intervenção urgente necessária com planejamento de ações imediatas.
- **🔴 ALTO** (Score ≥ 5 ou ≥ 1 característica crítica): Acompanhamento intensivo com estratégias de suporte direcionadas.
- **⚠️ MODERADO** (Score ≥ 2): Monitoramento regular e atenção preventiva.
- **✅ BAIXO** (Score = 0 sem alertas): Estudante apresenta perfil adequado.

**Padrões de Risco:**

1. **Apatia + Desinteresse** (NEG_06 + NEG_08 - ambas recorrentes)
   - Combinação de baixa iniciativa/envolvimento com falta de motivação pelo conteúdo
   - Alto risco de abandono escolar quando reportado por múltiplos professores
   - O estudante não apenas não se interessa, como também não se envolve de forma consistente

2. **Desmotivação severa** (NEG_14 ou NEG_15 - características críticas recorrentes)
   - Presença de Autossabotador (prejudica ativamente seu próprio progresso) ou Desmotivado (perda persistente de interesse)
   - Necessita intervenção imediata quando reportado por múltiplos professores
   - Indicador forte de necessidade de suporte psicopedagógico urgente

3. **Irresponsabilidade + Indisciplina** (NEG_10 + NEG_01 - ambas recorrentes)
   - Combinação de ignorar consequências com dificuldade em seguir regras e rotinas
   - Comportamento disruptivo que impacta o próprio desempenho e o ambiente de aprendizagem
   - Requer acompanhamento comportamental estruturado quando é padrão recorrente

As **recomendações** são geradas automaticamente com base no nível de risco calculado, orientando a equipe pedagógica sobre as ações prioritárias para cada estudante.
    """)

# Informação sobre onde os dados são salvos
with st.expander("💾 Informações sobre salvamento", expanded=False):
    st.info("""
    - **Observação:** As observações são salvas em todas as disciplinas do estudante.
    - **Arquivo principal:** `dados/notas_discentes.csv` (atualizado automaticamente ao salvar)
    - **Backups:** `dados/backups/notas_discentes_YYYYMMDD_HHMMSS.csv` (criado a cada salvamento)
    - **Auditoria:** `dados/audit_edits.csv` (registro de todas as alterações com data/hora)
    """)