import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json
from streamlit_option_menu import option_menu

from data.disciplinas import (
    NOMES,
    NOMES_ABREVIADOS as NOMES_DISCIPLINAS,
    SIGAA_EXTRA,
    sigla_curriculo,
    cod_nome,
)

# ==================== CONSTANTES ====================
CORES_GRAFICO = {
    'nota': 'rgba(135, 206, 250, 0.7)',  # Azul claro com 70% opacidade
    'nota_borda': 'blue',
    'faltas': 'rgba(255, 0, 0, 0.4)',  # Vermelho com 40% opacidade
    'faltas_borda': 'red',
    'radar_nota': '#87CEFA',  # Azul claro
    'radar_faltas': '#FF6347'  # Vermelho/Tomate
}

GRAFICO_CONFIG = {
    'height': 400,
    'plot_bgcolor': 'rgba(240, 240, 240, 0.5)'
}

CSS_PADDING = """
    <style>
        .block-container {
            padding-top: 2.8rem;
            padding-bottom: 0rem;
        }
    </style>
"""

# ==================== SIDEBAR E NAVEGAÇÃO ====================

def setup_sidebar_header():
    """Configura a parte superior do sidebar (imagens e navegação) - chamada UMA ÚNICA VEZ por página"""
    # Esconde a navegação padrão do Streamlit
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {display: none !important;}
        </style>
    """, unsafe_allow_html=True)
    
    # Determina a página atual verificando o script path
    try:
        import inspect
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        current_file = caller_frame.f_globals.get('__file__', '')
    except:
        current_file = ""
    
    # Mapeia páginas para índices do menu
    page_to_index = {
        "home.py": 0,
        "conselho_intermediario.py": 1,
        "pedagogico.py": 2,
        "conselho_final.py": 3,
        "docentes.py": 4,
        "discentes.py": 5,
        "pre_requisito.py": 6,
        "validacoes.py": 7,
        "matriculas.py": 8,
    }
    
    # Detecta a página atual
    default_idx = 0
    for page_file, idx in page_to_index.items():
        if page_file in current_file:
            default_idx = idx
            break
    
    # Menu de navegação com option_menu (PRIMEIRO)
    with st.sidebar:
        selected = option_menu(
            menu_title=None,
        options=["Home", "Conselho Intermediário", "Pedagógico", "Conselho Final", "Docentes", "Discentes", "Pré-Requisito", "Validação", "Matrículas"],
        icons=["house", "calendar-check", "clipboard-check", "person-workspace", "people", "mortarboard", "diagram-3", "card-list", "envelope"],
            default_index=default_idx,
            key="main_menu",
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#f0f2f6"
                },
                "nav-link-selected": {"background-color": "#1f77b4"},
            }
        )
    
    # Imagens após o menu (ordem invertida: figConselho2 primeiro, depois figConselho)
    st.sidebar.image(os.path.join("assets", "figConselho2.png"))
    st.sidebar.image(os.path.join("assets", "figConselho.png"))
    
    # Mapeamento de seleção para página
    page_map = {
        "Home": "pages/home.py",
        "Conselho Intermediário": "pages/coordenacao_tarefas/conselho_intermediario.py",
        "Pedagógico": "pages/coordenacao/pedagogico.py",
        "Conselho Final": "pages/coordenacao/conselho_final.py",
        "Docentes": "pages/coordenacao/docentes.py",
        "Discentes": "pages/coordenacao/discentes.py",
        "Pré-Requisito": "pages/coordenacao_tarefas/pre_requisito.py",
        "Validação": "pages/coordenacao_tarefas/validacoes.py",
        "Matrículas": "pages/coordenacao_tarefas/matriculas.py",
    }
    
    # Navega apenas se a seleção for diferente da página atual
    target_page = page_map[selected]
    if target_page not in current_file:
        st.switch_page(target_page)

def show_sidebar():
    """Versão legacy - mantida para compatibilidade"""
    setup_sidebar_header()


def aplicar_css_padding():
    """Aplica CSS de padding padrão"""
    st.markdown(CSS_PADDING, unsafe_allow_html=True)


# ==================== FUNÇÕES DE NAVEGAÇÃO ====================

def criar_funcoes_navegacao(indice_key, estudantes_list):
    """
    Cria funções de navegação entre estudantes
    
    Args:
        indice_key: Nome da chave no session_state (ex: 'indice', 'indice_pedagogico')
        estudantes_list: Lista de estudantes
    
    Returns:
        tuple: (proximo_estudante, anterior_estudante)
    """
    def proximo_estudante():
        if st.session_state[indice_key] < len(estudantes_list) - 1:
            st.session_state[indice_key] += 1
    
    def anterior_estudante():
        if st.session_state[indice_key] > 0:
            st.session_state[indice_key] -= 1
    
    return proximo_estudante, anterior_estudante


# ==================== PROCESSAMENTO DE DADOS ====================

def normalizar_dados(disciplinas_df):
    """
    Normaliza e converte colunas de Nota e Infrequencia para numérico
    
    Args:
        disciplinas_df: DataFrame com colunas 'Nota' e 'Infrequencia'
    
    Returns:
        DataFrame com colunas 'Nota_num' e 'Infrequencia_num' adicionadas
    """
    df = disciplinas_df.copy()
    
    df['Nota_num'] = pd.to_numeric(
        df['Nota'].astype(str).str.replace(',', '.').str.replace('%', ''),
        errors='coerce'
    )
    df['Infrequencia_num'] = pd.to_numeric(
        df['Infrequencia'].astype(str).str.replace(',', '.').str.replace('%', ''),
        errors='coerce'
    )
    
    return df


# ==================== VISUALIZAÇÕES ====================

def create_plotly_chart(disciplinas_df):
    """
    Cria gráfico de barras sobrepostas com notas e infrequência
    Mostra todas as disciplinas, inclusive as sem nota lançada
    
    Args:
        disciplinas_df: DataFrame com colunas 'Disciplina', 'Nota_num', 'Infrequencia_num'
    
    Returns:
        plotly.graph_objects.Figure
    """
    fig = go.Figure()
    
    # Copia e preenche valores nulos com 0 para visualização
    disciplinas_plot = disciplinas_df.copy()
    disciplinas_plot['Nota_num'] = disciplinas_plot['Nota_num'].fillna(0)
    disciplinas_plot['Infrequencia_num'] = disciplinas_plot['Infrequencia_num'].fillna(0)
    
    # Normaliza infrequência para escala 0-10 (para visualização sobreposta)
    disciplinas_plot['Infrequencia_normalizado'] = disciplinas_plot['Infrequencia_num'] / 10
    
    # Identifica disciplinas sem nota (para marcação visual diferente)
    sem_nota = disciplinas_df['Nota_num'].isna()
    
    # Texto para notas - mostra "S/N" para disciplinas sem nota
    texto_notas = disciplinas_plot['Nota_num'].round(1).astype(str)
    texto_notas = texto_notas.where(~sem_nota, 'S/N')
    
    # Texto para infrequência
    texto_infreq = disciplinas_plot['Infrequencia_num'].round(1).astype(str) + '%'
    texto_infreq = texto_infreq.where(~sem_nota, '-')
    
    # Adiciona barras de infrequência (fundo, vermelho com opacidade)
    fig.add_trace(go.Bar(
        x=disciplinas_plot['Disciplina'],
        y=disciplinas_plot['Infrequencia_normalizado'],
        name='Faltas',
        marker=dict(
            color=CORES_GRAFICO['faltas'],
            line=dict(color=CORES_GRAFICO['faltas_borda'], width=1)
        ),
        text=texto_infreq,
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Faltas: %{text}<extra></extra>'
    ))
    
    # Adiciona barras de notas (frente, azul com opacidade)
    fig.add_trace(go.Bar(
        x=disciplinas_plot['Disciplina'],
        y=disciplinas_plot['Nota_num'],
        name='Nota',
        marker=dict(
            color=CORES_GRAFICO['nota'],
            line=dict(color=CORES_GRAFICO['nota_borda'], width=1)
        ),
        text=texto_notas,
        textposition='outside',
        textfont=dict(color='darkblue', size=12, family='Arial Black'),
        hovertemplate='<b>%{x}</b><br>Nota: %{text}<extra></extra>'
    ))
    
    # Layout com eixo único
    fig.update_layout(
        barmode='overlay',  # Barras sobrepostas
        yaxis=dict(
            range=[0, 10],
            tickvals=[0, 2, 4, 6, 8, 10],
            ticktext=['0', '2 / 20%', '4 / 40%', '6 / 60%', '8 / 80%', '10 / 100%']
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=GRAFICO_CONFIG['height'],
        hovermode='x unified',
        plot_bgcolor=GRAFICO_CONFIG['plot_bgcolor']
    )
    
    return fig


def preparar_dados_radar(disciplinas_df):
    """
    Prepara dados para o gráfico radar
    
    Args:
        disciplinas_df: DataFrame com dados das disciplinas
    
    Returns:
        list: Lista de dicionários com dados formatados para o radar
    """
    dados_radar = []
    for _, linha in disciplinas_df.iterrows():
        disciplina = linha['Disciplina']
        nota_raw = linha.get('Nota_num') if 'Nota_num' in linha.index else None
        freq_raw = linha.get('Infrequencia_num') if 'Infrequencia_num' in linha.index else None

        nota_scaled = 0.0
        if pd.notna(nota_raw):
            try:
                nota_scaled = float(nota_raw)
            except Exception:
                nota_scaled = 0.0

        freq_scaled = 0.0
        if pd.notna(freq_raw):
            try:
                freq_raw = float(freq_raw)
                if freq_raw <= 25:
                    freq_scaled = (freq_raw / 25) * 10
                else:
                    freq_scaled = 10
            except Exception:
                freq_scaled = 0.0

        dados_radar.append({
            "disciplina": disciplina,
            "Nota": nota_scaled,
            "Faltas": freq_scaled,
        })
    
    return dados_radar


# ==================== UTILITÁRIOS ====================

def get_foto_path(matricula, foto_dir="fotos"):
    """
    Procura por arquivo de foto com múltiplas extensões
    Suporta: .png, .jpg, .jpeg (case-insensitive)
    
    Args:
        matricula: Matrícula do estudante (sem extensão)
        foto_dir: Diretório onde as fotos estão armazenadas
    
    Returns:
        Caminho da foto se encontrada, None caso contrário
    """
    extensoes = ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']
    
    for ext in extensoes:
        foto_path = os.path.join(foto_dir, f"{matricula}{ext}")
        if os.path.exists(foto_path):
            return foto_path
    
    return None


def salvar_dados_sigaa(df, filepath, header_lines=None, encoding='utf-8'):
    """
    Salva o DataFrame no formato SIGAA, incluindo cabeçalho original e colunas de observação.
    
    Args:
        df: DataFrame com os dados dos estudantes
        filepath: Caminho do arquivo de destino
        header_lines: Lista com as 4 linhas de cabeçalho do SIGAA (opcional)
        encoding: Encoding para o arquivo (default: utf-8)
    
    O arquivo salvo terá:
    - 4 linhas de cabeçalho SIGAA (se fornecidas)
    - Linha de cabeçalho das colunas (com nomes originais do SIGAA)
    - Dados do DataFrame
    - Colunas de observação no final (Obs_Professor, Caracteristicas_Prof, Obs_Pedagogico)
    """
    # Mapeamento de nomes internos para nomes originais do SIGAA
    mapeamento_colunas = {
        "Fase": "Período",
        "Matricula": "Matrícula",
        "Aluno": "Nome discente",
        "Situacao": "Situação",
        "Codigo": "Código",
        "Disciplina": "Nome",
        "Nota": "Nota",
        "Frequencia": "Frequência Consolidada",
        "Infrequencia": "Percentual de Infrequência (parcial)",
        "ANP": "ANP - Não participação"
    }
    
    # Define as colunas na ordem esperada pelo SIGAA (todas) + colunas de observação
    colunas_internas = ["Fase", "Matricula", "Aluno", "Situacao", "Codigo", "Disciplina", "Nota", "Frequencia", "Infrequencia", "ANP"]
    colunas_obs = ["Obs_Professor", "Caracteristicas_Prof", "Obs_Pedagogico"]
    
    # Garante que todas as colunas existam no DataFrame
    for col in colunas_internas + colunas_obs:
        if col not in df.columns:
            df[col] = ""
    
    # Reorganiza colunas na ordem correta
    colunas_final = colunas_internas + colunas_obs
    df_save = df[colunas_final].copy()
    
    # Renomeia colunas para nomes originais do SIGAA
    df_save = df_save.rename(columns=mapeamento_colunas)
    
    # Cria diretório se não existir
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    
    # Salva o arquivo
    with open(filepath, 'w', encoding=encoding) as f:
        # Escreve cabeçalho SIGAA se fornecido
        if header_lines:
            for line in header_lines:
                f.write(line + '\n')
            # Linha em branco após cabeçalho
            f.write('\n')
        
        # Salva o DataFrame sem index
        df_save.to_csv(f, sep=';', index=False, encoding=encoding, lineterminator='\n')
    
    return filepath


def carregar_dados_sigaa(filepath, encoding='utf-8'):
    """
    Carrega um arquivo CSV no formato SIGAA, incluindo cabeçalho e colunas de observação.
    
    Args:
        filepath: Caminho do arquivo
        encoding: Encoding do arquivo (default: utf-8)
    
    Returns:
        tuple: (DataFrame com dados, lista de linhas do cabeçalho SIGAA)
    """
    header_lines = []
    
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
    
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            # Tenta detectar se há cabeçalho SIGAA (começa com CURSO;)
            first_line = f.readline().strip()
            f.seek(0)
            
            if first_line.startswith('CURSO;'):
                # Lê as 4 linhas do cabeçalho
                for i in range(4):
                    header_lines.append(f.readline().strip())
                # Pula linha em branco
                f.readline()
                # Lê o resto como DataFrame
                df = pd.read_csv(f, sep=';', encoding=encoding, index_col=False)
            else:
                # Arquivo sem cabeçalho SIGAA, lê diretamente
                df = pd.read_csv(filepath, sep=';', encoding=encoding, index_col=False)
        
        # Renomeia colunas originais do SIGAA para nomes internos
        df = df.rename(columns=mapeamento_colunas)
        
        return df, header_lines
    
    except Exception as e:
        # Em caso de erro, tenta carregar sem cabeçalho
        df = pd.read_csv(filepath, sep=';', encoding=encoding, index_col=False)
        df = df.rename(columns=mapeamento_colunas)
        return df, []


# ==================== MATRIZ CURRICULAR DO ESTUDANTE ====================

# NOMES_DISCIPLINAS e SIGAA_EXTRA importados de data.disciplinas (via import no topo)


def construir_disciplinas_cod_nome(df):
    """
    Constrói a lista padronizada de disciplinas no formato 'COD - Nome'
    a partir do DataFrame de notas carregado via upload.

    Retorna:
        disciplinas_list: lista de nomes brutos (SIGAA) ordenada
        disciplinas_cod_nome: lista formatada ["COD - Nome", ...]
        mapa_sigaa_nome: dict { nome_SIGAA: "COD - Nome" }
        mapa_cod_nome_para_parts: dict { "COD - Nome": (codigo, nome_exibicao) }
    """
    mapa_codigo = (
        df[['Disciplina', 'Codigo']]
        .drop_duplicates()
        .set_index('Disciplina')['Codigo']
        .to_dict()
    )
    disciplinas_list = sorted(df['Disciplina'].unique())

    disciplinas_cod_nome = []
    mapa_sigaa_nome = {}
    mapa_cod_nome_para_parts = {}
    _cod_nome_vistos = set()

    for d in disciplinas_list:
        sigaa_code = str(mapa_codigo.get(d, ''))
        cod = sigla_curriculo(sigaa_code[:3]) if sigaa_code else ''
        nome_exibicao = NOMES.get(cod, d)
        item = f"{cod} - {nome_exibicao}" if cod else d
        mapa_sigaa_nome[d] = item
        mapa_cod_nome_para_parts[item] = (cod, nome_exibicao)
        if item not in _cod_nome_vistos:
            disciplinas_cod_nome.append(item)
            _cod_nome_vistos.add(item)

    return disciplinas_list, disciplinas_cod_nome, mapa_sigaa_nome, mapa_cod_nome_para_parts


def _carregar_curriculo():
    """Carrega e retorna os dados do currículo a partir do arquivo matriz.json."""
    json_path = os.path.join("data", "matriz.json")
    if not os.path.exists(json_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(script_dir, "..", "data", "matriz.json")

    with open(json_path, encoding="utf-8") as f:
        dados_json = json.load(f)

    return {k: v for k, v in dados_json.items() if k != "optativas"}


def _calcular_status_disciplinas(df, matricula, curriculo, apenas_matriculadas=False):
    """Calcula os conjuntos de disciplinas cursando e aprovadas para um estudante.

    Args:
        df: DataFrame com os dados.
        matricula: Matrícula do estudante.
        curriculo: Dicionário do currículo.
        apenas_matriculadas: Se True, não infere aprovadas (sem histórico).

    Returns:
        tuple: (cursando, aprovadas, max_fase, codigos_validos)
    """
    codigos_validos = set()
    for sem, discs in curriculo.items():
        codigos_validos.update(discs.keys())

    df_est = df[df["Matricula"] == str(matricula)]

    cursando = set()
    for cod in df_est["Codigo"].dropna():
        c3 = str(cod).strip()[:3].upper()
        if c3 in codigos_validos:
            cursando.add(c3)
        elif c3 in SIGAA_EXTRA:
            cursando.add(SIGAA_EXTRA[c3])

    try:
        max_fase = int(df_est["Fase"].dropna().astype(int).max())
    except (ValueError, TypeError):
        max_fase = 1

    aprovadas = set()
    if not apenas_matriculadas:
        for sem, discs in curriculo.items():
            sem_int = int(sem)
            for disc_code, disc_data in discs.items():
                sfim = disc_data.get("semestre_fim")
                if sfim:
                    if sem_int <= max_fase and max_fase >= sfim and disc_code not in cursando:
                        aprovadas.add(disc_code)
                else:
                    if sem_int <= max_fase and disc_code not in cursando:
                        aprovadas.add(disc_code)

    return cursando, aprovadas, max_fase, codigos_validos


def renderizar_matriz_curricular(df, matricula, css_prefix="mc", apenas_matriculadas=False):
    """Renderiza a seção completa da Matriz Curricular do Estudante.

    Args:
        df: DataFrame com os dados de matrícula/disciplinas do estudante.
        matricula: Código de matrícula do estudante selecionado.
        css_prefix: Prefixo para classes CSS (evita conflitos entre páginas).
        apenas_matriculadas: Se True, mostra apenas matriculadas (sem inferir aprovadas).
    """
    curriculo = _carregar_curriculo()
    cursando, aprovadas, max_fase, codigos_validos = _calcular_status_disciplinas(
        df, matricula, curriculo, apenas_matriculadas=apenas_matriculadas
    )

    # ── CSS para cards da matriz ─────────────────────────────────────────
    st.markdown(f"""
    <style>
    .sem-header-{css_prefix} {{
        text-align: center; font-weight: 700; font-size: 0.78rem;
        color: #7f8c8d; margin-bottom: 0.3rem; letter-spacing: 1px;
    }}
    .disc-card-{css_prefix} {{
        border-radius: 6px; padding: 5px 3px; text-align: center;
        font-weight: 700; font-size: 0.72rem; line-height: 1.2;
        min-height: 48px; max-height: 48px; overflow: hidden;
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; margin-bottom: 3px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.12);
    }}
    .disc-card-{css_prefix} .sub-{css_prefix} {{
        font-weight: 400; font-size: 0.42rem; opacity: 0.85;
        display: block; margin-top: 1px; line-height: 1.1;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
        max-width: 100%;
    }}
    .disc-card-span-{css_prefix} {{
        border-radius: 5px; padding: 3px 8px; text-align: center;
        font-weight: 600; font-size: 0.65rem; line-height: 1.2;
        min-height: 26px; max-height: 26px; overflow: hidden;
        display: flex; align-items: center; justify-content: center;
        margin-bottom: 3px; box-shadow: 0 1px 2px rgba(0,0,0,0.12);
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── Funções de cor ───────────────────────────────────────────────────
    def cor(disc):
        if disc in aprovadas:
            return "#27ae60"  # verde
        if disc in cursando:
            return "#f1c40f"  # amarelo
        return "#bdc3c7"  # cinza

    def txt(disc):
        return "#2c3e50" if cor(disc) in {"#f1c40f", "#bdc3c7"} else "#ffffff"

    # ── Resumo ───────────────────────────────────────────────────────────
    total = len(codigos_validos)
    n_aprov = len(aprovadas)
    n_curs = len(cursando)
    n_pend = total - n_aprov - n_curs
    pct = round(100 * n_aprov / total) if total else 0

    if apenas_matriculadas:
        st.caption(
            f"🟡 Matriculado: **{n_curs}**  ·  "
            f"⚪ Demais: **{total - n_curs}**  ·  "
            f"Fase atual: **{max_fase}º sem**"
        )
    else:
        col_leg1, col_leg2 = st.columns([3, 1])
        with col_leg1:
            st.caption(
                f"🟢 Aprovadas: **{n_aprov}**  ·  "
                f"🟡 Cursando: **{n_curs}**  ·  "
                f"⚪ Pendentes: **{n_pend}**  ·  "
                f"Fase atual: **{max_fase}º sem**"
            )
        with col_leg2:
            st.caption(f"Progresso: **{pct}%** do currículo")

    # ── Renderizar grid ──────────────────────────────────────────────────
    num_sem = len(curriculo)
    cols = st.columns(num_sem, gap="small")

    for i, (semestre, disciplinas) in enumerate(
        sorted(curriculo.items(), key=lambda x: int(x[0]))
    ):
        with cols[i]:
            st.markdown(
                f'<div class="sem-header-{css_prefix}">{semestre}º</div>',
                unsafe_allow_html=True,
            )

            for disc, disc_data in disciplinas.items():
                sfim = disc_data.get("semestre_fim")
                if sfim and (sfim - int(semestre) + 1) >= num_sem:
                    continue  # full-width spanning — renderizado abaixo

                c = cor(disc)
                t = txt(disc)
                nome = NOMES_DISCIPLINAS.get(disc, disc)

                st.markdown(
                    f'<div class="disc-card-{css_prefix}" style="background:{c}; color:{t};" '
                    f'title="{nome}">'
                    f'{disc}<span class="sub-{css_prefix}">{nome}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── Disciplinas que abrangem toda a grade (ex: Atividades Complementares)
    for semestre, disciplinas in sorted(curriculo.items(), key=lambda x: int(x[0])):
        for disc, disc_data in disciplinas.items():
            sfim = disc_data.get("semestre_fim")
            if sfim and (sfim - int(semestre) + 1) >= num_sem:
                c = cor(disc)
                t = txt(disc)
                nome = NOMES_DISCIPLINAS.get(disc, disc)
                st.markdown(
                    f'<div class="disc-card-span-{css_prefix}" style="background:{c}; color:{t};">'
                    f'{nome}</div>',
                    unsafe_allow_html=True,
                )