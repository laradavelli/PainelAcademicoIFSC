import streamlit as st
import os

# ── Sidebar com logos ────────────────────────────────────────────────────
from utils import setup_sidebar_header
setup_sidebar_header()

st.markdown("# 🛠️ Desenvolvedor")
st.caption("Referência técnica interna — Painel Acadêmico")

st.info(
    "Esta página documenta a **arquitetura, fluxo de dados e decisões técnicas** "
    "do projeto para facilitar manutenção e evolução futura."
)

# ══════════════════════════════════════════════════════════════════════════
# 1. ARQUITETURA GERAL
# ══════════════════════════════════════════════════════════════════════════
st.header("1. Arquitetura Geral")
st.markdown(
    """
    O Painel Acadêmico é uma aplicação **Streamlit multipage** orquestrada por um
    único entrypoint (`app.py`) que usa `st.navigation` para registrar todas as
    páginas e seções do sidebar.

    ```
    app.py (entrypoint)
    ├── Configura st.set_page_config — UMA ÚNICA VEZ
    ├── Faz monkey-patch de set_page_config para impedir chamadas duplicadas
    ├── Substitui setup_sidebar_header por _sidebar_logos (apenas imagens)
    └── Registra st.navigation com todas as páginas organizadas em seções
    ```

    **Decisão de design:** cada página individualmente chama `st.set_page_config`
    (para funcionar standalone), mas `app.py` intercepta essa chamada com
    `st.set_page_config = lambda *a, **kw: None` para evitar conflitos no modo
    multipage.
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 2. FLUXO DE DADOS PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════
st.header("2. Fluxo de Dados Principal")

st.subheader("2.1 Upload e Ingestão (Home)")
st.markdown(
    """
    1. O usuário faz upload de um CSV exportado do **SIGAA → Mapa de Conceito**
    2. O sistema tenta decodificar com `utf-8 → latin1 → cp1252`
    3. As **4 primeiras linhas** (cabeçalho institucional SIGAA) são extraídas e
       armazenadas em `st.session_state.sigaa_header`
    4. O CSV é parseado com `pd.read_csv(sep=';', skiprows=4)`
    5. Colunas são **renomeadas** do padrão SIGAA para nomes internos:

    | SIGAA (original)                       | Interno           |
    |----------------------------------------|-------------------|
    | `Período`                              | `Fase`            |
    | `Matrícula`                            | `Matricula`       |
    | `Nome discente`                        | `Aluno`           |
    | `Situação`                             | `Situacao`        |
    | `Código`                               | `Codigo`          |
    | `Nome`                                 | `Disciplina`      |
    | `Nota`                                 | `Nota`            |
    | `Frequência Consolidada`               | `Frequencia`      |
    | `Percentual de Infrequência (parcial)` | `Infrequencia`    |
    | `ANP - Não participação`               | `ANP`             |

    6. Linhas sem `Matricula` ou `Disciplina` são descartadas
    7. O DataFrame é armazenado em `st.session_state.df`

    **Importante:** neste momento **nada é salvo em disco**. O arquivo existe
    apenas em memória (session state).
    """
)

st.subheader("2.2 Persistência em Disco")
st.markdown(
    """
    A gravação em disco ocorre **somente** quando o usuário clica em
    "💾 Salvar Tudo" nas páginas de **Conselho Final** ou **Pedagógico**. Nesse momento:

    | Arquivo                                         | Descrição                          |
    |-------------------------------------------------|------------------------------------|
    | `dados/notas_discentes.csv`                     | Arquivo principal (sobrescrito)    |
    | `dados/backups/notas_discentes_YYYYMMDD_HHMMSS.csv` | Backup com timestamp           |
    | `dados/audit_edits.csv`                         | Log de auditoria (append)          |

    A função `salvar_dados_sigaa()` em `utils.py` reconstrói o formato SIGAA
    original: 4 linhas de cabeçalho + nomes de coluna originais + colunas de
    observação adicionais (`Obs_Professor`, `Caracteristicas_Prof`, `Obs_Pedagogico`).

    As páginas de tarefas (Matrículas, Validações, Pré-Requisito, Protocolo SIPAC)
    gravam seus próprios CSVs independentes na pasta `dados/`.
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 3. SESSION STATE — CHAVES GLOBAIS
# ══════════════════════════════════════════════════════════════════════════
st.header("3. Session State — Chaves Globais")
st.markdown(
    """
    Todas as páginas compartilham o `st.session_state`. As chaves principais criadas
    pelo `home.py` no momento do upload são:

    | Chave                  | Tipo          | Descrição                                              |
    |------------------------|---------------|---------------------------------------------------------|
    | `arquivo_carregado`    | `bool`        | **Gate principal** — todas as páginas verificam isso     |
    | `df`                   | `DataFrame`   | Dataset ativo (mutável, editado pelas páginas)           |
    | `df_original`          | `DataFrame`   | Cópia intacta para permitir undo                         |
    | `sigaa_header`         | `list[str]`   | 4 linhas do cabeçalho institucional SIGAA                |
    | `file_encoding`        | `str`         | Encoding detectado (`utf-8`, `latin1` ou `cp1252`)       |
    | `session_id`           | `str` (UUID)  | Identificador da sessão para trilha de auditoria         |
    | `curso_selecionado`    | `str`         | Curso ativo selecionado na Home (propaga para Ajustes e Relatório Geral) |

    **Padrão de guarda:** toda página (exceto Home) verifica
    `st.session_state.arquivo_carregado` e chama `st.stop()` se `False`.
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 4. MÓDULOS E CAMADAS
# ══════════════════════════════════════════════════════════════════════════
st.header("4. Módulos e Camadas")

st.subheader("4.1 Camada de Dados (`data/`)")
st.markdown(
    """
    - **`disciplinas.py`** — Catálogo de disciplinas de Engenharia Elétrica:
      - `NOMES`: código 3 letras → nome completo (86 disciplinas)
      - `NOMES_ABREVIADOS`: código → nome abreviado (para cards compactos)
      - `SIGAA_EXTRA`: códigos alternativos SIGAA → código canônico do currículo
        (ex: `"ACX" → "ACI"`, `"COE" → "COM"`) — 15 mapeamentos
      - Funções: `sigla_curriculo()`, `cod_nome()`, `cod_nome_abreviado()`, `nome_para_codigo()`

    - **`matriz.json`** — Matriz curricular completa (345 linhas):
      ```json
      {
        "<semestre>": {
          "<código>": {
            "pre": ["<pré-requisitos>"],
            "co": ["<co-requisitos>"],
            "creditos": <int>,
            "semestre_fim": <int>   // opcional, para disciplinas multi-semestre
          }
        }
      }
      ```
      Semestres `"1"` a `"10"` + `"optativas"` (catálogo de eletivas).
    """
)

st.subheader("4.2 Camada de Modelo (`model/`)")
st.markdown(
    """
    - **`grafo.py`** — Modela o currículo como um **grafo dirigido acíclico (DAG)**
      usando NetworkX:

    | Função | Descrição |
    |--------|-----------|
    | `aplicar_optativas(curriculo, optativas, selecoes)` | Injeta eletivas nos slots OP1–OP4, remapeia pré-requisitos cruzados |
    | `construir_grafo(curriculo)` | Constrói `nx.DiGraph` — nós = disciplinas, arestas = pré/co-requisitos |
    | `obter_info_disciplina(G, disc)` | Retorna semestre, pré-requisitos diretos, co-requisitos |

    **Arestas** possuem atributo `tipo`:
    - `"pre"` → pré-requisito (obrigatório antes)
    - `"co"` → co-requisito (obrigatório simultâneo)
    """
)

st.subheader("4.3 Camada de Serviço (`service/`)")
st.markdown(
    """
    - **`planejamento.py`** — Classifica disciplinas no grafo:

    | Função | Descrição |
    |--------|-----------|
    | `classificar(G, aprovadas)` | Retorna dict: disciplina → `"aprovada"` / `"liberada"` / `"bloqueada"` |
    | `dependencias(G, disc)` | Cadeia completa de ancestrais (pré-req) e descendentes |
    | `pre_requisitos_diretos(G, disc)` | Pré-requisitos de 1 hop |
    | `dependentes_diretos(G, disc)` | Dependentes de 1 hop |
    | `co_requisitos(G, disc)` | Co-requisitos da disciplina |

    - **`estrategia.py`** — 5 algoritmos de recomendação de matrícula:

    | Estratégia | Chave | Fórmula de Pontuação |
    |------------|-------|----------------------|
    | **A — Menor Tempo** | `estrategia_menor_tempo` | `profundidade × 3 + impacto` |
    | **B — Desbloquear** | `estrategia_desbloquear` | `desbloqueios_imediatos × 5 + impacto` |
    | **C — Gargalos** | `estrategia_gargalos` | `impacto × 3 + profundidade` |
    | **D — Balanceamento** | `estrategia_balanceamento` | `(11 - semestre) × 2 + impacto × 0.5 + profundidade × 0.3` |
    | **Ótima** | `estrategia_otima` | `α × impacto_norm + β × profundidade_norm` (α=0.6, β=0.4) |

    Onde:
    - **impacto** = nº total de descendentes no subgrafo de pré-requisitos
    - **profundidade** = comprimento do caminho mais longo a partir da disciplina no DAG
    - **desbloqueios_imediatos** = simulação: se aprovada, quantas novas disciplinas são liberadas

    Seleção final usa **knapsack guloso** com limite de créditos, incluindo
    co-requisitos automaticamente.
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 5. UTILITÁRIOS COMPARTILHADOS (utils.py)
# ══════════════════════════════════════════════════════════════════════════
st.header("5. Utilitários Compartilhados (`utils.py`)")
st.markdown(
    """
    | Função | Finalidade |
    |--------|-----------|
    | `setup_sidebar_header()` | Sidebar com navegação via `streamlit_option_menu` + logos |
    | `aplicar_css_padding()` | Injeta CSS para reduzir padding padrão do Streamlit |
    | `normalizar_dados(df)` | Adiciona `Nota_num` e `Infrequencia_num` (trata vírgula decimal, `%`) |
    | `create_plotly_chart(df)` | Gráfico de barras sobrepostas (notas × infrequência) |
    | `preparar_dados_radar(df)` | Transforma dados para gráfico radar |
    | `get_foto_path(matricula)` | Busca foto do aluno em `fotos/` (png/jpg/jpeg) |
    | `salvar_dados_sigaa(df, path, header, enc)` | Salva no formato SIGAA (4 linhas cabeçalho + colunas originais) |
    | `carregar_dados_sigaa(path, enc)` | Carrega arquivo SIGAA, renomeia colunas para interno |
    | `construir_disciplinas_cod_nome(df)` | Constrói lista padronizada `"COD - Nome"` |
    | `renderizar_matriz_curricular(df, mat, prefix)` | Grid HTML/CSS da matriz curricular com cores de status |

    **Constantes:**
    - `CORES_GRAFICO` — paleta de cores para gráficos Plotly
    - `GRAFICO_CONFIG` — altura e cor de fundo dos gráficos
    - `CSS_PADDING` — snippet CSS compartilhado
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 6. ARQUIVOS DE DADOS (pasta dados/)
# ══════════════════════════════════════════════════════════════════════════
st.header("6. Arquivos de Dados (`dados/`)")
st.markdown(
    """
    | Arquivo | Origem | Descrição |
    |---------|--------|-----------|
    | `notas_discentes.csv` | Upload + edição | Arquivo principal — notas, frequência, observações |
    | `Coordenadores.csv` | Página Docentes | Coordenadores por curso (CRUD na interface) |
    | `Docentes.csv` | Página Docentes | Corpo docente (CRUD na interface) |
    | `pre_requisitos.csv` | Manual | Tabela de pré-requisitos |
    | `solicitacoes_validacoes.csv` | Página Validações | Solicitações de validação/aproveitamento |
    | `solicitacoes_matricula_avulsa.csv` | Página Matrículas | Solicitações de matrícula avulsa |
    | `solicitacoes_prerequisito.csv` | Página Pré-Requisito | Dispensas de pré-requisito |
    | `protocolos_sipac.csv` | Página Protocolo SIPAC | Protocolos institucionais |
    | `google_credentials.json` | Upload via sidebar (Ajustes) | Credenciais Google (conta de serviço) — opcional |
    | `audit_edits.csv` | Automático | Log de auditoria de todas as edições |
    | `backups/` | Automático | Backups com timestamp a cada salvamento |
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 7. PÁGINAS — RESUMO TÉCNICO
# ══════════════════════════════════════════════════════════════════════════
st.header("7. Páginas — Resumo Técnico")

st.markdown(
    """
    | Página | Arquivo | Funcionalidade principal |
    |--------|---------|--------------------------|
    | **Home** | `pages/home.py` | Upload CSV, bootstrap da sessão |
    | **Documentação** | `pages/documentacao.py` | Documentação funcional em Markdown |
    | **Relatório Geral** | `pages/relatorio_geral.py` | Dados agregados da coordenação |
    | **Conselho Intermediário** | `pages/coordenacao_tarefas/conselho_intermediario.py` | Análise por aluno com gráficos radar e matriz curricular |
    | **Pré-Requisito** | `pages/coordenacao_tarefas/pre_requisito.py` | CRUD de dispensas → `solicitacoes_prerequisito.csv` |
    | **Validação** | `pages/coordenacao_tarefas/validacoes.py` | CRUD de validações → `solicitacoes_validacoes.csv` |
    | **Matrículas** | `pages/coordenacao_tarefas/matriculas.py` | Memorandos de matrícula avulsa → `solicitacoes_matricula_avulsa.csv` |
    | **Protocolo SIPAC** | `pages/coordenacao_tarefas/protocolo_sipac.py` | CRUD de protocolos → `protocolos_sipac.csv` |
    | **Ajustes** | `pages/coordenacao_tarefas/ajustes.py` | Integração Google Sheets → leitura pública + escrita via gspread |
    | **Conselho Final** | `pages/coordenacao/conselho_final.py` | Notas/faltas por aluno, edição SIGAA, salvamento com backup |
    | **Docentes** | `pages/coordenacao/docentes.py` | CRUD de docentes + seleção de coordenadores por curso |
    | **Discentes** | `pages/coordenacao/discentes.py` | Listagem e filtros de alunos |
    | **Pedagógico** | `pages/coordenacao/pedagogico.py` | Análise pedagógica com edição de observações |
    | **Painel Acadêmico** | `pages/planejamento/painel.py` | Visualização interativa do grafo curricular |
    | **Estratégias** | `pages/planejamento/estrategias.py` | Comparativo de 5 algoritmos de matrícula |
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 8. PADRÕES E CONVENÇÕES
# ══════════════════════════════════════════════════════════════════════════
st.header("8. Padrões e Convenções")
st.markdown(
    """
    - **Guard pattern:** toda página (exceto Home) verifica `st.session_state.arquivo_carregado`
      e exibe erro + `st.stop()` se o arquivo não foi carregado.

    - **DataFrame mutável compartilhado:** `st.session_state.df` é o dataset ativo.
      Edições feitas em qualquer página são refletidas globalmente.

    - **Fidelidade SIGAA:** as funções `salvar_dados_sigaa()` e `carregar_dados_sigaa()`
      preservam o cabeçalho institucional de 4 linhas e os nomes originais das colunas,
      permitindo que o arquivo salvo seja reimportado no SIGAA.

    - **Backup automático:** cada operação de salvamento cria um backup com timestamp
      em `dados/backups/`, permitindo recuperação de versões anteriores.

    - **Auditoria:** edições são registradas em `dados/audit_edits.csv` com:
      `timestamp`, `página`, `matrícula`, `campo`, `valor_antigo`, `valor_novo`, `session_id`.

    - **Navegação por slider + botões:** as páginas de conselho usam um padrão de
      navegação por `st.slider` sincronizado com botões Anterior/Próximo via session state.
      O valor do slider é controlado **exclusivamente** pelo session state (`key=`) — nunca
      usar `value=` junto com atribuição ao session state, para evitar conflito do Streamlit.

    - **Grafo DAG:** o currículo é modelado como grafo dirigido acíclico (NetworkX), com
      arestas tipadas (`pre`/`co`). Isso permite análise algorítmica de caminhos,
      dependências e estratégias de matrícula.
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 9. TECNOLOGIAS E DEPENDÊNCIAS
# ══════════════════════════════════════════════════════════════════════════
st.header("9. Tecnologias e Dependências")
st.markdown(
    """
    | Pacote | Versão | Uso |
    |--------|--------|-----|
    | `streamlit` | 1.51.0 | Framework web (frontend + backend) |
    | `streamlit-option-menu` | ≥0.3 | Menu de navegação customizado no sidebar |
    | `streamlit-elements` | 0.1.0 | Componentes MUI (Material UI) |
    | `pandas` | ≥2.0 | Manipulação de DataFrames |
    | `plotly` | ≥5.0 | Gráficos interativos (barras, radar) |
    | `networkx` | ≥3.0 | Grafo de pré-requisitos (DAG) |
    | `gspread` | ≥6.0.0 | Acesso à API Google Sheets (leitura/escrita) |
    | `google-auth` | ≥2.0.0 | Autenticação via conta de serviço Google |
    | `numpy` | ≥1.24 | Operações numéricas |
    | `openpyxl` | ≥3.1 | Suporte a Excel (futuro) |
    | `pillow` | ≥9.0 | Manipulação de imagens (fotos dos alunos) |
    | `pyvis` | ≥0.3 | Visualização de grafos (exploratória) |

    **Python:** 3.10+ (local) / 3.12 (Docker)

    **Distribuição:** Docker (multiplataforma) — ver `Dockerfile` e `docker-compose.yml`.
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 10. COMO CONTRIBUIR / MANTER
# ══════════════════════════════════════════════════════════════════════════
st.header("10. Dicas para Manutenção")
st.markdown(
    """
    - **Adicionar nova disciplina:** edite `data/disciplinas.py` (NOMES + NOMES_ABREVIADOS)
      e `data/matriz.json` (semestre, pré/co-requisitos, créditos).

    - **Adicionar nova página:** crie o arquivo em `pages/`, registre em `app.py`
      (variável + seção do `st.navigation`).

    - **Nova coluna de dados:** adicione o mapeamento em `home.py` (mapeamento_colunas)
      e em `utils.py` (`salvar_dados_sigaa` / `carregar_dados_sigaa`).

    - **Nova estratégia de matrícula:** crie a função em `service/estrategia.py`,
      adicione a `ESTRATEGIAS` e `DESCRICOES`.

    - **Depuração de slider:** nunca combine `value=` + `key=` + atribuição direta
      ao session state. Use apenas `key=` e sincronize antes da renderização.

    - **Testar localmente:** `streamlit run app.py` (com `.venv` ativado).
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 11. INTEGRAÇÃO GOOGLE SHEETS (PÁGINA AJUSTES)
# ══════════════════════════════════════════════════════════════════════════
st.header("11. Integração Google Sheets (Página Ajustes)")
st.markdown(
    """
    A página **Ajustes** (`pages/coordenacao_tarefas/ajustes.py`) é a única página
    do sistema que **não usa CSVs locais** para armazenamento. Em vez disso, lê
    (e opcionalmente escreve) diretamente em uma **planilha Google Sheets**
    vinculada a um formulário Google Forms.

    #### Arquitetura de Acesso

    ```
    Google Forms (alunos submetem ajustes)
         │
         ▼
    Google Sheets (planilha de respostas)
         │
         ├── Modo 1: Planilha publicada na web (CSV público)
         │     └── fetch_sheet_public() → pd.read_csv(URL)
         │         └── Somente leitura, sem credenciais
         │
         └── Modo 2: API Google Sheets (gspread + service account)
               └── fetch_sheet_gspread(client) → sheet.get_all_values()
                   └── Leitura + escrita (colunas Q e R)
    ```

    #### Constantes Críticas

    | Constante | Valor | Uso |
    |-----------|-------|-----|
    | `SPREADSHEET_ID` | `15KawxJNSE5Im_...` | ID da planilha (para API autenticada) |
    | `PUBLISHED_ID` | `2PACX-1vQv7...` | ID do documento publicado (para URL pública) |
    | `HEADER_ROWS` | `2` | Número de linhas de cabeçalho na planilha |
    | `COL_Q_IDX` | `16` | Índice 0-based da coluna "Parecer" |
    | `COL_R_IDX` | `17` | Índice 0-based da coluna "Observação" |

    #### Fluxo de Autenticação

    A função `get_gspread_client()` tenta obter credenciais em 3 níveis de prioridade:

    1. **Arquivo local** (`dados/google_credentials.json`) — persiste entre sessões
    2. **Upload via sidebar** (`st.session_state["google_creds_json"]`) — volátil
    3. **Streamlit Secrets** (`st.secrets["gcp_service_account"]`) — deploy em nuvem

    Se nenhuma credencial for encontrada, retorna `None` e o sistema opera em
    modo somente leitura (fallback para URL pública).

    #### Cache

    Ambas as funções de leitura usam `@st.cache_data(ttl=300)` (5 minutos).
    O botão "🔄 Atualizar dados" limpa o cache e força recarregamento.

    #### Propagação do Curso Selecionado

    A página **Home** define `st.session_state.curso_selecionado` com o curso
    escolhido pelo usuário. Esse valor é usado como **filtro padrão** em:
    - Página Ajustes (selectbox de curso)
    - Relatório Geral (filtragem de dados de ajustes antes da contagem)
    """
)
