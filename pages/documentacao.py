import streamlit as st
import os

# ── Sidebar com logos ────────────────────────────────────────────────────
st.sidebar.image(os.path.join("assets", "figConselho2.png"))
st.sidebar.image(os.path.join("assets", "figConselho.png"))

st.markdown("# 📖 Documentação do Projeto")
st.caption("Painel Acadêmico — Engenharia Elétrica")

# ══════════════════════════════════════════════════════════════════════════
# 1. VISÃO GERAL
# ══════════════════════════════════════════════════════════════════════════
st.header("1. Visão Geral")
st.markdown(
    """
    O **Painel Acadêmico** é uma plataforma interativa que integra dois módulos complementares
    para o curso de **Bacharelado em Engenharia Elétrica**:

    | Módulo | Público-alvo | Finalidade |
    |--------|-------------|-----------|
    | **Planejamento Acadêmico** | Estudantes | Planejamento de matrículas, análise de dependências e estratégias de formação |
    | **Coordenação** | Coordenação / Docentes | Conselhos de Classe, análise pedagógica, solicitações de matrícula e memorandos |

    Ambos compartilham a mesma **matriz curricular** (`data/matriz.json`) com 10 semestres
    e 63+ disciplinas, e são acessados por um entrypoint unificado (`app.py`) que utiliza
    `st.navigation` para alternar entre as seções.

    O sistema permite:
    - Visualizar a **Matriz Curricular** interativa com análise de dependências
    - Recomendar disciplinas via **5 estratégias de matrícula** otimizadas
    - Importar dados do **SIGAA** (Mapa de Conceito) via upload de arquivo CSV
    - Visualizar e navegar pelos estudantes com gráficos de notas e faltas
    - Registrar observações pedagógicas e de professores com trilha de auditoria
    - Analisar riscos pedagógicos (evasão, rendimento, frequência)
    - Visualizar a **Matriz Curricular do Estudante** com progresso colorido
    - Gerenciar solicitações de **pré-requisitos**, **validações** e **matrículas avulsas**
    - Gerar **memorandos** independentes em cada página (Pré-Requisito, Validações, Matrículas)
    - Consultar a listagem de **docentes** e **coordenadores**
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 2. MÓDULO: PLANEJAMENTO ACADÊMICO
# ══════════════════════════════════════════════════════════════════════════
st.header("2. Planejamento Acadêmico")

st.subheader("2.1 Visualização da Matriz Curricular (`pages/planejamento/painel.py`)")
st.markdown(
    """
    - Grid organizado em **10 colunas** (uma por semestre)
    - Cada disciplina é um **card colorido** com sua sigla
    - Pré-requisitos diretos são exibidos como subtexto no card (`← PRE1, PRE2`)
    - Co-requisitos são exibidos como subtexto no card (`⇄ CO1`)
    - **Cards spanning**: disciplinas que atravessam múltiplos semestres são exibidas
      com largura proporcional (ex.: **EST** — Estágio Curricular Supervisionado ocupa
      as colunas do 9º e 10º semestre)
    - **Card compacto**: **ATC** — Atividades Complementares é exibida como uma barra
      horizontal na parte inferior da matriz, cobrindo do 1º ao 10º semestre
    - Seleção de **disciplinas optativas** para os slots OP1–OP4 na parte inferior da página
    - Seleção de **disciplinas aprovadas** na sidebar, incluindo EST, ATC e optativas,
      com exibição do nome completo (`CÓD — Nome`) para facilitar a identificação
    """
)

st.subheader("2.2 Classificação de Disciplinas")
st.markdown(
    """
    Com base nas disciplinas marcadas como **aprovadas** na sidebar, cada disciplina
    é classificada automaticamente:

    | Status | Cor | Significado |
    |--------|-----|-------------|
    | 🟢 Aprovada | Verde | Disciplina já cursada com aprovação |
    | 🟡 Liberada | Amarelo | Todos os pré-requisitos atendidos; pode matricular |
    | ⚪ Bloqueada | Cinza | Falta pelo menos um pré-requisito |
    """
)

st.subheader("2.3 Análise de Dependências")
st.markdown(
    """
    Ao selecionar uma disciplina para análise (botão 🔍 ou selectbox na sidebar):

    | Destaque | Cor | Significado |
    |----------|-----|-------------|
    | 🟣 Foco | Roxo | A disciplina selecionada |
    | 🔵 Pré-requisitos | Azul | Toda a cadeia de pré-requisitos (recursiva) |
    | 🔴 Dependentes | Vermelho | Todas as disciplinas futuras impactadas (recursiva) |
    | 🟠 Co-requisitos | Laranja | Disciplinas que devem ser cursadas simultaneamente |

    As disciplinas que **não fazem parte** da cadeia de dependência recebem
    **opacidade reduzida** (18%), permitindo foco visual no que importa.
    """
)

st.subheader("2.4 Painel de Detalhes")
st.markdown(
    """
    Quando uma disciplina está em foco, um painel inferior exibe:
    - **Pré-requisitos** agrupados por semestre
    - **Detalhes** da disciplina (semestre, pré-req. diretos, co-requisitos, status)
    - **Impacto Futuro** — quantas disciplinas serão impactadas com alerta visual
    """
)

st.subheader("2.5 Estratégias de Matrícula (`pages/planejamento/estrategias.py`)")
st.markdown(
    """
    O sistema oferece **5 estratégias** para recomendar a melhor matrícula
    com base nas disciplinas aprovadas e um limite de créditos por semestre:

    | Estratégia | Objetivo | Critério de priorização |
    |------------|----------|------------------------|
    | **A — Menor tempo** | Formar mais rápido | Profundidade no caminho crítico |
    | **B — Desbloquear** | Mais opções futuras | Nº de disciplinas desbloqueadas diretamente |
    | **C — Gargalos** | Evitar cascata | Nº total de descendentes (impacto) |
    | **D — Balanceamento** | Carga equilibrada | Semestre de origem + impacto |
    | **Ótima** | Melhor combinação | score = α·impacto + β·profundidade |

    **Algoritmo da Estratégia Ótima (Heurística):**
    1. Calcular disciplinas liberadas
    2. Para cada liberada, calcular: `score = α · impacto_norm + β · profundidade_norm`
    3. Ordenar por score decrescente
    4. Selecionar até atingir o limite de créditos
    5. Incluir co-requisitos obrigatórios automaticamente

    Os pesos α e β são ajustáveis pelo usuário (α + β = 1).

    A página também oferece uma **comparação entre estratégias**:
    executa todas com os mesmos parâmetros e exibe os resultados lado a lado.
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 3. MÓDULO: COORDENAÇÃO
# ══════════════════════════════════════════════════════════════════════════
st.header("3. Coordenação")
st.markdown(
    """
    O módulo de Coordenação abrange **12 páginas** organizadas para apoiar
    todas as etapas do Conselho de Classe e gestão acadêmica.
    """
)

# ---------- Home ----------
st.subheader("3.1 🏠 Home — Upload de Dados")
st.markdown(
    """
    Ponto de entrada do módulo de Coordenação. Responsável por:
    - **Upload** do arquivo CSV exportado do SIGAA (formato "Mapa de Conceito")
    - Detecção automática de encoding (`utf-8`, `latin1`, `cp1252`)
    - Parsing inteligente: ignora as 4 linhas de cabeçalho do SIGAA e renomeia as colunas
      para nomes internos padronizados (ex.: `Período` → `Fase`, `Nome discente` → `Aluno`)
    - Armazena o DataFrame em `st.session_state.df` para uso em todas as demais páginas
    - Cria um **UUID de sessão** (`session_id`) para rastreabilidade na trilha de auditoria
    """
)

# ---------- Conselho Intermediário ----------
st.subheader("3.2 📅 Conselho Intermediário")
st.markdown(
    """
    Visão **estudante-a-estudante** para o Conselho de Classe intermediário:

    - **Filtro por fase(s)** — multiselect para selecionar um ou mais semestres
    - **Navegação** — botões Anterior/Próximo e slider para percorrer os estudantes
    - **Foto do estudante** — exibe a foto da pasta `fotos/` (por matrícula)
    - **Gráficos de desempenho** — dois tipos alternáveis:
      - 📊 **Gráfico de Colunas** — barras sobrepostas de notas (azul) e faltas (vermelho)
      - 🎯 **Gráfico Radar** — visualização radar (Nivo) com notas e faltas por disciplina
    - **Matriz Curricular** — grid visual ao final da página com disciplinas coloridas:
      - 🟢 Aprovadas (verde) · 🟡 Cursando (amarelo) · ⚪ Pendentes (cinza)
      - Resumo com contagem e percentual de progresso no currículo
    """
)

# ---------- Pedagógico ----------
st.subheader("3.3 📋 Pedagógico")
st.markdown(
    """
    Módulo de **análise pedagógica** com motor de avaliação de risco:

    #### Modos de Filtro

    A página oferece 4 modos de navegação pelos estudantes:

    | Modo | Descrição |
    |------|-----------|
    | **Fase** | Multiselect de fase(s) — navega pelos estudantes das fases selecionadas |
    | **Disciplina** | Multiselect de disciplina(s) — navega pelos estudantes das disciplinas selecionadas |
    | **Discente** | Selectbox para buscar um estudante específico pelo nome |
    | **Score** | Lista **todos** os estudantes do arquivo, ordenados do maior para o menor score de risco, independentemente de fase ou disciplina |

    O modo **Score** é destinado ao setor pedagógico para priorizar o atendimento:
    ao clicar em "Próximo", o setor percorre automaticamente os casos mais críticos
    primeiro, sem precisar selecionar fases ou disciplinas.

    #### Motor de Risco Pedagógico

    O motor calcula um **score de risco** a partir das características registradas
    pelos professores no Conselho Final. Apenas características marcadas por
    **2 ou mais professores diferentes** (recorrência) geram pontuação formal:

    | Grupo | Características | Pontos por item |
    |-------|----------------|----------------|
    | Moderado | NEG_01 a NEG_05 | 1 pt |
    | Alto | NEG_06 a NEG_10 | 2 pt |
    | Crítico | NEG_11 a NEG_15 | 3 pt |

    Com base no score total, o estudante recebe um badge de risco:

    | Nível | Score / Critério | Badge |
    |-------|-----------------|-------|
    | **CRÍTICO** | score ≥ 8 ou ≥ 3 características críticas | 🚨 Vermelho escuro — intervenção urgente |
    | **ALTO** | score ≥ 5 ou ≥ 1 característica crítica | 🔴 Vermelho — acompanhamento intensivo |
    | **MODERADO** | score ≥ 2 | ⚠️ Laranja — monitoramento regular |
    | **ALERTA DISCIPLINAR** | score = 0.5 (característica negativa de apenas 1 professor) | ⚠️ Amarelo — observação isolada |
    | **BAIXO** | score = 0 e sem alertas | ✅ Verde — perfil adequado |

    **Ordenação no modo Score:**

    A ordenação considera três níveis de prioridade:
    - `score ≥ 1` — risco recorrente confirmado por 2+ professores (aparece primeiro)
    - `score = 0.5` — Alerta Disciplinar (1 professor marcou algo negativo; aparece no meio)
    - `score = 0.0` — sem nenhuma observação negativa (aparece por último)

    Isso garante que estudantes com "Alerta Disciplinar" sempre precedam estudantes
    sem qualquer sinalização, mesmo que ambos tenham score formal zero.

    - **Detecção de padrões de evasão** — ex.: Apatia + Desinteresse (recorrente)
    - **Nuvem de palavras** — visualização das características mais frequentes
    - **Observações pedagógicas** — campo de texto com salvamento e auditoria
    - **Observações dos professores** — cards consolidados (disciplina × observação × características)
    - **Relatório estatístico da turma** (expandível) — risco agregado, top-5 características positivas/negativas
    - **Geração de PDF** — relatório individual do estudante com dados, risco, observações e desempenho
    """
)

# ---------- Conselho Final ----------
st.subheader("3.4 👨‍💼 Conselho Final")
st.markdown(
    """
    Visão voltada ao **professor** para o Conselho de Classe final:

    - **Filtro por disciplina(s)** — multiselect para selecionar disciplinas do professor
    - Navegação por estudante com foto e gráfico de notas (das disciplinas filtradas)
    - **Campo de observações** — texto livre por estudante/disciplina
    - **30 checkboxes de características** — 15 positivas (POS_01–15) e 15 negativas (NEG_01–15),
      com indicação de nível de risco para cada negativa
    - Botão **"Salvar Tudo"** — persiste observações e características no CSV,
      cria backup com timestamp e registra na trilha de auditoria
    """
)

# ---------- Docentes ----------
st.subheader("3.5 👥 Docentes")
st.markdown(
    """
    Listagem de professores do curso (**não requer upload de arquivo**):

    - Carrega `dados/Docentes.csv` e `dados/Coordenadores.csv`
    - **Métricas**: total de docentes, docentes ativos, coordenadores
    - **Filtros**: por Situação (ativo/inativo) e por Área de atuação
    - **Checkboxes**: "Membro do Colegiado" e "Membro do NDE" — marcam diretamente
      no cadastro do docente, alimentando automaticamente as páginas de Reunião
    - Identificação de coordenadores por cruzamento entre as duas bases
    - **Portaria do Colegiado**: gera texto da portaria com presidente, pedagoga,
      membros docentes e representantes discentes; download em TXT e botão para
      copiar e-mails dos membros
    - **Portaria do NDE**: gera texto da portaria com presidente e membros docentes
      marcados como NDE; download em TXT e botão para copiar e-mails
    - Download da lista filtrada em CSV
    """
)

# ---------- Discentes ----------
st.subheader("3.6 🎓 Discentes")
st.markdown(
    """
    Análise consolidada dos estudantes:

    - **Métricas gerais**: total de discentes, total de disciplinas, fases ativas
    - **Filtros avançados**: fase, situação, busca por nome/matrícula, disciplina(s),
      filtros especiais de **TCC** e **Estágio** (toggles)
    - **Tabela de estudantes** com download em CSV
    - **Detalhamento por estudante**: ao selecionar um discente, exibe a lista de
      disciplinas cursadas ordenada por fase
    - **Matriz Curricular do Estudante** — grid visual com status colorido
      (🟢 Aprovadas · 🟡 Cursando · ⚪ Pendentes) e progresso percentual
    """
)

# ---------- Pré-Requisito ----------
st.subheader("3.7 🔗 Pré-Requisito")
st.markdown(
    """
    Controle de solicitações de **quebra de pré-requisito**:

    - **Seção 1 — Cadastrar**: formulário para registrar nova solicitação
      (estudante, disciplina, pré-requisitos pendentes, semestre, justificativa)
    - **Seção 2 — Avaliar**: avaliação de solicitações pendentes (Deferido/Indeferido + parecer)
    - **Seção 2B — Editar/Excluir**: manutenção de solicitações existentes (em abas)
    - **Seção 3 — Memorando**: checklist de casos deferidos, pré-visualização do memorando,
      marcação de envio e histórico de memorandos enviados (com opção de desfazer)
    - **Seção 4 — Painel de Controle**: tabela filtrável com todas as solicitações
      e download de relatório em `.txt`

    Dados persistidos em `dados/solicitacoes_prerequisito.csv`.
    Disciplinas exibidas no formato padronizado `COD - Nome` via `construir_disciplinas_cod_nome()`.
    """
)

# ---------- Validações ----------
st.subheader("3.8 📝 Validações")
st.markdown(
    """
    Controle de solicitações de **validação de disciplinas** (aproveitamento de estudos):

    - **Seção 1 — Cadastrar**: formulário para registrar solicitação de validação
      (estudante, disciplina(s), semestre, descrição)
    - **Seção 2 — Avaliar**: avaliação com campos adicionais: nota, frequência,
      professor responsável (dropdown com docentes de `dados/Docentes.csv`), parecer
    - **Seção 2B — Editar/Excluir**: manutenção de solicitações existentes
    - **Seção 3 — Memorando**: checklist de casos deferidos, pré-visualização do memorando,
      marcação de envio e histórico (com opção de desfazer)
    - **Seção 4 — Painel de Controle**: tabela filtrável + download de relatório `.txt`

    Dados persistidos em `dados/solicitacoes_validacoes.csv` (exclui registros de matrícula avulsa).
    Disciplinas exibidas no formato padronizado `COD - Nome` via `construir_disciplinas_cod_nome()`.
    """
)

# ---------- Matrículas (Memorandos) ----------
st.subheader("3.9 📨 Matrículas — Memorandos")
st.markdown(
    """
    Controle de **matrículas avulsas** e geração de memorandos:

    - **Seção 1 — Cadastrar**: formulário para registrar matrícula avulsa
      (estudante, disciplina(s), semestre). Solicitações vão diretamente para
      status "Deferido" (sem etapa de avaliação). Suporta fluxo especial para TC2
      (título, orientador, coorientador)
    - **Seção 2 — Editar/Excluir**: manutenção de solicitações existentes (em abas)
    - **Seção 3 — Memorando**: checklist de casos deferidos, pré-visualização do memorando,
      marcação de envio e histórico (com opção de desfazer)
    - **Seção 4 — Painel de Controle**: tabela filtrável + download de relatório `.txt`

    Dados persistidos em `dados/solicitacoes_matricula_avulsa.csv` (CSV exclusivo,
    separado das validações). Migração automática de registros antigos do CSV compartilhado.
    Disciplinas exibidas no formato padronizado `COD - Nome` via `construir_disciplinas_cod_nome()`.
    """
)

# ---------- Reunião do Colegiado ----------
st.subheader("3.10 📋 Reunião do Colegiado")
st.markdown(
    """
    Gerenciamento completo de **reuniões do Colegiado do Curso**:

    - **Criação de reuniões**: diálogo com número, tipo (Ordinária/Extraordinária),
      data (formato DD/MM/AAAA), horário (padrão 10:30–12:30), local (padrão Auditório A112)
    - **Seleção por semestre**: filtro de reuniões por semestre letivo
    - **Foco automático**: ao criar uma reunião, o seletor foca automaticamente na nova reunião
    - **Membros automáticos**: carregados de `dados/Docentes.csv` (Colegiado=True),
      `dados/Coordenadores.csv` (presidente) e `dados/representantes_turma.csv` (discentes)
    - **Lista de presença**: checkboxes de presença com campo de justificativa para ausentes
    - **Pontos de pauta**: adição/remoção dinâmica com título, discussão e encaminhamento
    - **Geração de ata**: texto editável gerado automaticamente com todos os dados da reunião
    - **Lista de presença (PDF)**: download de PDF com cabeçalho e rodapé institucionais
      (`assets/cabecalho.png`, `assets/rodape.png`) e tabela para assinatura
    - **Download da ata**: exportação em TXT
    - **Exclusão**: com confirmação

    Dados persistidos em `dados/reunioes_colegiado.json`.
    """
)

# ---------- Reunião do NDE ----------
st.subheader("3.11 📋 Reunião do NDE")
st.markdown(
    """
    Gerenciamento de **reuniões do Núcleo Docente Estruturante (NDE)**:

    - Funcionalidades idênticas à Reunião do Colegiado (criação, presença, pauta, ata)
    - **Membros automáticos**: carregados de `dados/Docentes.csv` (NDE=True)
      e `dados/Coordenadores.csv` (presidente = Coordenador de EE)
    - Não inclui representantes discentes nem membro técnico (diferente do Colegiado)
    - Geração de ata com nomenclatura específica do NDE

    Dados persistidos em `dados/reunioes_nde.json`.
    """
)

# ---------- Protocolo SIPAC ----------
st.subheader("3.12 📮 Protocolo SIPAC")
st.markdown(
    """
    Registro de **protocolos institucionais** encaminhados via SIPAC:

    - **Cadastrar**: formulário para registrar protocolo
      (número, assunto, destinatário, semestre)
    - **Painel de Controle**: tabela filtrável com download

    Dados persistidos em `dados/protocolos_sipac.csv`.
    """
)

# ---------- Ajustes ----------
st.subheader("3.13 📝 Ajustes de Matrícula")
st.markdown(
    """
    Página para gerenciamento de **ajustes de matrícula** recebidos via
    formulário Google Forms. Os dados são lidos diretamente de uma
    **planilha Google Sheets** publicada na web.

    ---

    #### Funcionalidades

    - **Visualização em tempo real**: os dados são carregados da planilha publicada
      com cache de 5 minutos (atualiza automaticamente quando novos formulários são submetidos)
    - **Filtros**: por **Curso** (coluna E) e por **Parecer da Coordenação** (coluna Q:
      Todos / Pendente / Deferido / Indeferido)
    - **Filtro global de curso**: o curso selecionado na página Home é utilizado como
      valor padrão do filtro, mas pode ser alterado localmente
    - **Ordenação**: registros ordenados por data de solicitação (mais recentes primeiro)
    - **Edição (modo autenticado)**: colunas Q (*Parecer da Coord. de Curso*) e R
      (*Observação*) são editáveis quando as credenciais Google estão configuradas
    - **Resumo**: métricas (Total / Pendentes / Deferidos / Indeferidos) e
      tabela de contagem por tipo de solicitação
    - **Integração com Relatório Geral**: os dados de ajustes aparecem no gráfico
      de evolução e nas métricas do relatório consolidado, filtrados pelo curso
      selecionado na Home

    ---

    #### Modos de Operação

    | Modo | Requisito | Funcionalidades |
    |------|-----------|----------------|
    | **Somente leitura** | Planilha publicada na web | Visualização, filtros, resumo |
    | **Leitura e escrita** | Credenciais Google (JSON) | Tudo acima + edição de colunas Q e R |

    O modo somente leitura é o **padrão** e não requer nenhuma configuração
    adicional — basta que a planilha esteja publicada na web.

    ---

    #### Credenciais Google — Arquivo JSON da Conta de Serviço

    Para habilitar a **edição** dos campos de parecer e observação diretamente
    pelo sistema (sem precisar abrir a planilha no navegador), é necessário
    configurar uma **conta de serviço do Google Cloud**.

    **O que é o arquivo JSON?**

    É uma chave de autenticação (similar a uma senha) que permite ao sistema
    acessar a planilha do Google Sheets via API com permissão de leitura
    e escrita. O arquivo é gerado gratuitamente no Google Cloud Console.

    **Passo a passo para obtenção:**

    1. Acesse [console.cloud.google.com](https://console.cloud.google.com/)
       com a conta institucional (`luiz.radavelli@ifsc.edu.br`)
    2. **Criar projeto** → nome: `painel-academico` → Criar
    3. No menu ☰ → **APIs e Serviços** → **Biblioteca**
       - Pesquise **Google Sheets API** → **Ativar**
       - Pesquise **Google Drive API** → **Ativar**
    4. Menu ☰ → **APIs e Serviços** → **Credenciais**
       - **Criar credenciais** → **Conta de serviço**
       - Nome: `painel` → Criar e continuar → Concluído
    5. Clique na conta de serviço criada → aba **Chaves**
       - **Adicionar chave** → **Criar nova chave** → **JSON** → Criar
       - O arquivo `.json` será baixado automaticamente
    6. **Faça upload** do arquivo JSON na barra lateral da página Ajustes
       (seção ⚙️ Credenciais Google)
    7. Abra a planilha no Google Sheets → **Compartilhar** → cole o e-mail
       `client_email` que consta no JSON (ex.: `painel@painel-academico.iam.gserviceaccount.com`)
       → conceda permissão de **Editor**

    **Estrutura do arquivo JSON:**

    O arquivo contém campos como `type`, `project_id`, `private_key_id`,
    `private_key`, `client_email`, `client_id`, `auth_uri`, `token_uri`, etc.
    O campo mais importante é o `client_email` — esse é o e-mail que deve
    ser adicionado como editor na planilha.

    **Onde as credenciais ficam armazenadas?**

    | Local | Prioridade | Persistência |
    |-------|------------|-------------|
    | `dados/google_credentials.json` | 1ª (arquivo local) | Persiste entre sessões |
    | Upload via sidebar (sessão) | 2ª (memória) | Desaparece ao fechar o navegador |
    | `st.secrets["gcp_service_account"]` | 3ª (Streamlit Cloud) | Deploy em nuvem |

    O upload do JSON pela sidebar salva automaticamente em `dados/google_credentials.json`
    para reutilização em sessões futuras. É possível remover as credenciais a
    qualquer momento pelo botão "🗑️ Remover credenciais" na própria sidebar.

    **Segurança:** O arquivo JSON contém uma chave privada e deve ser tratado
    como informação sensível. Não compartilhe nem versione este arquivo em
    repositórios públicos. O arquivo `dados/google_credentials.json` deve
    constar no `.gitignore`.
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 4. ARQUITETURA
# ══════════════════════════════════════════════════════════════════════════
st.header("4. Arquitetura do Projeto")

st.markdown(
    """
    ```
    painel_academico/
    ├── app.py                          # Entrypoint unificado (st.navigation)
    ├── utils.py                        # Funções utilitárias compartilhadas
    ├── start.sh                        # Script de inicialização
    │
    ├── assets/                         # Imagens e logos
    │   ├── figConselho.png
    │   └── figConselho2.png
    │
    ├── data/                           # Dados estáticos (Python + JSON)
    │   ├── __init__.py
    │   ├── disciplinas.py              # Fonte centralizada de nomes de disciplinas
    │   └── matriz.json                 # Matriz curricular (semestres, pré-req., créditos)
    │
    ├── model/
    │   └── grafo.py                    # Grafo dirigido da matriz (NetworkX)
    │
    ├── service/
    │   ├── planejamento.py             # Classificação e dependências
    │   └── estrategia.py               # Algoritmos de estratégia de matrícula
    │
    ├── dados/                          # Dados dinâmicos (CSVs persistidos)
    │   ├── notas_discentes.csv
    │   ├── Docentes.csv
    │   ├── Coordenadores.csv
    │   ├── solicitacoes_prerequisito.csv
    │   ├── solicitacoes_validacoes.csv
    │   ├── solicitacoes_matricula_avulsa.csv
    │   ├── protocolos_sipac.csv
    │   ├── reunioes_colegiado.json
    │   ├── reunioes_nde.json
    │   ├── audit_edits.csv
    │   └── backups/
    │
    ├── fotos/                          # Fotos dos estudantes (por matrícula)
    │
    └── pages/                          # Todas as páginas do sistema
        ├── home.py                     # Upload de dados SIGAA
        ├── documentacao.py             # Esta documentação
        ├── relatorio_geral.py          # Relatório geral
        │
        ├── coordenacao_tarefas/        # Guia "Coordenação (Tarefas)"
        │   ├── conselho_intermediario.py
        │   ├── pre_requisito.py        # Quebra de pré-requisitos + memorando
        │   ├── validacoes.py           # Validação de disciplinas + memorando
        │   ├── matriculas.py           # Matrícula avulsa + memorando
        │   ├── protocolo_sipac.py      # Protocolo SIPAC
        │   ├── ajustes.py              # Ajustes de matrícula (Google Sheets)
        │   ├── reuniao_colegiado.py    # Reuniões do Colegiado + ata + PDF
        │   └── reuniao_nde.py          # Reuniões do NDE + ata
        │
        ├── coordenacao/                # Guia "Coordenação"
        │   ├── conselho_final.py       # Conselho final (professor)
        │   ├── docentes.py             # Listagem de docentes
        │   ├── discentes.py            # Análise de discentes
        │   └── pedagogico.py           # Análise pedagógica e risco
        │
        └── planejamento/               # Guia "Planejamento Acadêmico"
            ├── painel.py               # Grid da matriz curricular + dependências
            └── estrategias.py          # Estratégias de matrícula
    ```
    """
)

st.subheader("4.1 Camada de Dados (`data/matriz.json`)")
st.markdown(
    """
    Arquivo JSON estruturado por semestre. Cada disciplina declara seus
    pré-requisitos (`pre`), co-requisitos (`co`) e créditos.

    Disciplinas que se estendem por mais de um semestre possuem o campo
    `semestre_fim` indicando o último semestre de vigência.

    ```json
    {
      "5": {
        "CE3": {
          "pre": ["CA4", "CE2"],
          "co": [],
          "creditos": 3
        }
      },
      "9": {
        "EST": {
          "pre": ["PI2", "AUI"],
          "co": [],
          "creditos": 8,
          "semestre_fim": 10
        }
      }
    }
    ```

    O arquivo também contém uma seção `"optativas"` com o catálogo de
    disciplinas optativas e suas dependências.
    """
)

st.subheader("4.2 Camada de Modelo (`model/grafo.py`)")
st.markdown(
    """
    Constrói um **grafo dirigido** (`networkx.DiGraph`) onde:
    - **Nós** = disciplinas (com atributos `semestre`, `semestre_fim` e `creditos`)
    - **Arestas** = dependências tipadas (`pre` ou `co`)
    - Direção: `pré-requisito → disciplina`

    Funções:

    | Função | Descrição |
    |--------|-----------|
    | `aplicar_optativas(curriculo, optativas, selecoes)` | Substitui slots OP1–OP4 pelas optativas selecionadas |
    | `construir_grafo(curriculo)` | Cria o grafo a partir do JSON |
    | `obter_info_disciplina(G, disc)` | Retorna semestre, semestre_fim, pré-requisitos e co-requisitos |
    """
)

st.subheader("4.3 Camada de Serviço (`service/planejamento.py`)")
st.markdown(
    """
    Contém a lógica de negócio para classificação e análise de dependências:

    | Função | Descrição |
    |--------|-----------|
    | `classificar(G, aprovadas)` | Classifica cada disciplina como aprovada, liberada ou bloqueada |
    | `dependencias(G, disc)` | Retorna cadeia completa de pré-requisitos e dependentes (apenas arestas `pre`) |
    | `pre_requisitos_diretos(G, disc)` | Pré-requisitos imediatos |
    | `dependentes_diretos(G, disc)` | Dependentes imediatos |
    | `co_requisitos(G, disc)` | Co-requisitos da disciplina |
    """
)

st.subheader("4.4 Camada de Estratégia (`service/estrategia.py`)")
st.markdown(
    """
    Implementa os algoritmos de recomendação de matrícula:

    | Função | Estratégia |
    |--------|------------|
    | `estrategia_menor_tempo()` | A — Prioriza profundidade no caminho crítico |
    | `estrategia_desbloquear()` | B — Maximiza desbloqueios diretos |
    | `estrategia_gargalos()` | C — Prioriza impacto (nº de descendentes) |
    | `estrategia_balanceamento()` | D — Equilibra por semestre de origem |
    | `estrategia_otima()` | Ótima — score = α·impacto + β·profundidade |

    Helpers internos: `_impacto()`, `_profundidade()`, `_liberadas()`,
    `_selecionar_com_limite()` (knapsack simplificado com co-requisitos).

    A classe `Recomendacao` encapsula cada disciplina recomendada com:
    sigla, score, créditos, impacto, profundidade e motivo textual.
    """
)

st.subheader("4.5 Camada de Apresentação (`pages/planejamento/painel.py`)")
st.markdown(
    """
    Interface Streamlit com:
    - **Sidebar**: seleção de aprovadas (com nomes completos, incluindo EST, ATC e optativas),
      modo de análise (Direta / Raio-X), legenda de cores
    - **Grid**: 10 colunas de cards HTML/CSS com cores e opacidade dinâmica
    - **Cards spanning**: disciplinas multi-semestre (EST) com largura dupla via CSS `overflow`
    - **Card compacto**: Atividades Complementares (ATC) como barra horizontal full-width
    - **Seleção de optativas**: 4 selectboxes para associar disciplinas optativas aos slots OP1–OP4
    - **Detalhes**: painel inferior com análise agrupada por semestre
    """
)

st.subheader("4.6 Módulo Utilitário (`utils.py`)")
st.markdown(
    """
    Concentra constantes e funções compartilhadas por todas as páginas.
    Localizado na raiz do projeto (`utils.py`), importado por todos os módulos.

    > ⚠️ As constantes `NOMES_DISCIPLINAS`, `SIGAA_EXTRA` e `NOMES` **não são mais
    > definidas localmente** — são importadas de `data.disciplinas` (veja seção 4.9).

    **Constantes:**

    | Constante | Origem | Descrição |
    |-----------|--------|-----------|
    | `CORES_GRAFICO` | local | Paleta de cores (notas, faltas, radar) |
    | `GRAFICO_CONFIG` | local | Altura e fundo dos gráficos |
    | `CSS_PADDING` | local | CSS padrão de espaçamento |
    | `NOMES_DISCIPLINAS` | `data.disciplinas` | Dict de siglas → nomes **abreviados** (para cards da matriz) |
    | `NOMES` | `data.disciplinas` | Dict de siglas → nomes **completos** (82 disciplinas) |
    | `SIGAA_EXTRA` | `data.disciplinas` | Mapeamento de códigos SIGAA variantes → código canônico |

    **Funções:**

    | Função | Descrição |
    |--------|-----------|
    | `setup_sidebar_header()` | Configura sidebar com `option_menu` (10 páginas), imagens e navegação |
    | `aplicar_css_padding()` | Aplica CSS de espaçamento padrão |
    | `criar_funcoes_navegacao(key, lista)` | Retorna callbacks (próximo, anterior) para navegação entre estudantes |
    | `normalizar_dados(df)` | Adiciona colunas numéricas `Nota_num` e `Infrequencia_num` |
    | `create_plotly_chart(df)` | Gráfico de barras sobrepostas (notas + faltas) via Plotly |
    | `preparar_dados_radar(df)` | Prepara dados para gráfico Radar (Nivo) |
    | `get_foto_path(matricula, dir)` | Busca foto do estudante (.png/.jpg/.jpeg) |
    | `salvar_dados_sigaa(df, path, header, enc)` | Salva DataFrame no formato SIGAA com cabeçalho |
    | `carregar_dados_sigaa(path, enc)` | Carrega CSV no formato SIGAA → (df, header_lines) |
    | `construir_disciplinas_cod_nome(df)` | 🆕 Constrói lista padronizada `"COD - Nome"` a partir do DataFrame de upload |
    | `renderizar_matriz_curricular(df, matricula, css_prefix)` | Renderiza grid visual da Matriz Curricular com cards coloridos |
    """
)

# ── Fluxo de Dados ───────────────────────────────────────────────────────
st.subheader("4.7 Fluxo de Dados")
st.markdown(
    """
    ```
    Upload CSV (SIGAA)
         │
         ▼
    home.py → st.session_state.df (+ df_original)
         │
         ├── Ao fazer upload: mescla observações do CSV anterior (disco) → DataFrame
         │
         ├──► Conselho Intermediário (leitura)
         ├──► Pedagógico (leitura + escrita → CSV + backup + auditoria)
         ├──► Conselho Final (leitura + escrita → CSV + backup + auditoria)
         ├──► Discentes (leitura)
         │
         └──► Dados independentes:
              ├── data/disciplinas.py ──► NOMES, SIGAA_EXTRA → todas as páginas
              ├── data/matriz.json ──► Matriz Curricular, Painel, Estratégias
              ├── Docentes.csv ──► Docentes, Validações, Matrículas
              ├── Coordenadores.csv ──► Docentes
              ├── solicitacoes_prerequisito.csv ──► Pré-Requisito (+ memorando)
              ├── solicitacoes_validacoes.csv ──► Validações (+ memorando)
              └── solicitacoes_matricula_avulsa.csv ──► Matrículas (+ memorando)
    ```
    """
)

# ── Trilha de Auditoria ─────────────────────────────────────────────────
st.subheader("4.8 Trilha de Auditoria")
st.markdown(
    """
    Toda edição feita nos módulos Pedagógico e Conselho Final é registrada em
    `dados/audit_edits.csv` com os seguintes campos:

    | Campo | Descrição |
    |-------|-----------|
    | `timestamp` | Data/hora da edição |
    | `session_id` | UUID da sessão (criado no upload) |
    | `pagina` | Página de origem da edição |
    | `matricula` | Matrícula do estudante |
    | `campo` | Campo alterado (ex.: `Obs_Pedagogico`, `Caracteristicas_Prof`) |
    | `valor_anterior` | Valor antes da edição |
    | `valor_novo` | Valor após a edição |

    Além da auditoria, cada salvamento gera um **backup** automático do CSV
    em `dados/backups/` com formato `notas_discentes_YYYYMMDD_HHMMSS.csv`.
    """
)

# ── Módulo Centralizado de Disciplinas ────────────────────────────────────
st.subheader("4.9 Módulo Centralizado de Disciplinas (`data/disciplinas.py`)")
st.markdown(
    """
    Fonte **única** de nomes e códigos de disciplinas do currículo, eliminando
    duplicação que existia entre `utils.py`, `pages/planejamento/painel.py` e `pages/planejamento/estrategias.py`.

    **Dicts exportados:**

    | Dict | Qtd | Descrição |
    |------|-----|-----------|
    | `NOMES` | 82 | Código → nome **completo** (obrigatórias + optativas) |
    | `NOMES_ABREVIADOS` | 63 | Código → nome **abreviado** (para cards compactos da matriz) |
    | `SIGAA_EXTRA` | 15 | Código SIGAA alternativo → código canônico do currículo |

    **Funções auxiliares:**

    | Função | Descrição |
    |--------|-----------|
    | `sigla_curriculo(sigla)` | Converte sigla SIGAA (3 chars) → código canônico |
    | `cod_nome(codigo)` | Retorna `"COD - Nome Completo"` para exibição padronizada |
    | `cod_nome_abreviado(codigo)` | Retorna `"COD - Nome Abreviado"` (cards compactos) |
    | `nome_para_codigo(nome)` | Busca reversa: nome completo → código (case-insensitive) |

    **Como importar:**
    - Todas as páginas: `from data.disciplinas import NOMES, cod_nome`
    - Para formato "COD - Nome" com dados SIGAA: `from utils import construir_disciplinas_cod_nome`

    **`construir_disciplinas_cod_nome(df)`** (em `utils.py`):
    recebe o DataFrame de upload e retorna a lista padronizada `"COD - Nome"` usando
    `sigla_curriculo()` para resolver códigos SIGAA e `NOMES` para os nomes canônicos.

    > Para adicionar ou renomear uma disciplina, basta editar `data/disciplinas.py`.
    > Todas as páginas refletem a alteração automaticamente.
    """
)

# ── Reestruturação do Projeto (v5.0) ────────────────────────────────────
st.subheader("4.10 Reestruturação do Projeto (v5.0)")
st.markdown(
    """
    Em **março/2026** o projeto passou por uma **reorganização completa** da estrutura
    de pastas e arquivos. Esta seção documenta a motivação, o resultado e o mapeamento
    de caminhos para referência futura.

    ---

    #### Motivação

    A estrutura anterior mantinha o módulo de Coordenação dentro de uma pasta
    isolada (`ConselhoApp/`) com convenção de nomes do Streamlit antigo
    (`1_Conselho_Intermediario.py`, `2_Pedagogico.py`, etc.) e dependia de symlinks
    (`dados → ConselhoApp/dados`, `fotos → ConselhoApp/fotos`) para compartilhar
    recursos com o restante do projeto. Isso gerava:

    - **Duplicidade de caminhos**: `dados/` aparecia em dois locais (raiz como symlink e dentro de `ConselhoApp/`)
    - **Imports frágeis**: páginas dentro de `ConselhoApp/pages/` precisavam de `sys.path`
      hacks para importar `utils.py` e `data.disciplinas`
    - **Desalinhamento visual**: os nomes dos arquivos no disco não correspondiam
      às guias exibidas na barra lateral (`st.navigation`)
    - **Manutenção dificultada**: encontrar um arquivo exigia saber se pertencia
      ao módulo antigo (`ConselhoApp/`) ou ao novo (`pages/`)

    ---

    #### Princípios da Nova Estrutura

    1. **Pastas espelham a navegação**: as subpastas dentro de `pages/` replicam
       exatamente os grupos de guias definidos em `app.py` via `st.navigation`
    2. **Sem prefixos numéricos**: arquivos usam nomes descritivos em snake_case
       (ex.: `conselho_intermediario.py`), e a ordem é controlada exclusivamente
       pelo `app.py`
    3. **Recursos na raiz**: `dados/`, `fotos/`, `assets/` e `utils.py` ficam
       na raiz do projeto — elimina symlinks e simplifica todos os caminhos relativos
    4. **Imports diretos**: com `sys.path` configurado apenas em `app.py` (raiz),
       todos os módulos usam `from utils import ...` e `from data.disciplinas import ...`
       sem manipulação adicional de caminhos

    ---

    #### Mapeamento Antigo → Novo

    | Caminho antigo | Caminho novo | Observação |
    |----------------|-------------|------------|
    | `ConselhoApp/Home.py` | `pages/home.py` | Entrypoint de upload |
    | `ConselhoApp/pages/1_Conselho_Intermediario.py` | `pages/coordenacao_tarefas/conselho_intermediario.py` | — |
    | `ConselhoApp/pages/2_Pedagogico.py` | `pages/coordenacao/pedagogico.py` | — |
    | `ConselhoApp/pages/3_Conselho_Final.py` | `pages/coordenacao/conselho_final.py` | — |
    | `ConselhoApp/pages/4_Docentes.py` | `pages/coordenacao/docentes.py` | — |
    | `ConselhoApp/pages/5_Discentes.py` | `pages/coordenacao/discentes.py` | — |
    | `ConselhoApp/pages/6_Pre_Requisito.py` | `pages/coordenacao_tarefas/pre_requisito.py` | — |
    | `ConselhoApp/pages/7_Validacoes.py` | `pages/coordenacao_tarefas/validacoes.py` | — |
    | `ConselhoApp/pages/9_Matriculas.py` | `pages/coordenacao_tarefas/matriculas.py` | — |
    | `ConselhoApp/utils.py` | `utils.py` (raiz) | Removeu hacks de `sys.path` |
    | `pages/painel.py` | `pages/planejamento/painel.py` | — |
    | `pages/estrategias.py` | `pages/planejamento/estrategias.py` | — |
    | `pages/Relatorio_Geral.py` | `pages/relatorio_geral.py` | Renomeado para snake_case |
    | `pages/Protocolo_SIPAC.py` | `pages/coordenacao_tarefas/protocolo_sipac.py` | Movido para guia de tarefas |
    | `ConselhoApp/dados/` (+ symlink raiz) | `dados/` (raiz, diretório real) | Symlink eliminado |
    | `ConselhoApp/fotos/` (+ symlink raiz) | `fotos/` (raiz, diretório real) | Symlink eliminado |
    | `ConselhoApp/figConselho*.png` | `assets/figConselho*.png` | Imagens centralizadas |

    ---

    #### Correspondência Pastas ↔ Guias da Navegação

    | Subpasta em `pages/` | Grupo em `st.navigation` | Páginas |
    |----------------------|-------------------------|---------|
    | *(raiz de pages)* | *(sem grupo)* | Home, Documentação, Relatório Geral |
    | `coordenacao_tarefas/` | **Coordenação (Tarefas)** | Conselho Intermediário, Pré-Requisito, Validações, Matrículas, Protocolo SIPAC, Ajustes, Reunião Colegiado, Reunião NDE |
    | `coordenacao/` | **Coordenação** | Conselho Final, Docentes, Discentes, Pedagógico |
    | `planejamento/` | **Planejamento Acadêmico** | Painel (Matriz Curricular), Estratégias |

    ---

    #### Itens Eliminados

    - Diretório `ConselhoApp/` (todo o conteúdo migrado)
    - Symlinks `dados` e `fotos` na raiz
    - Arquivo duplicado `ConselhoApp/pages/8_Documentacao.py` (unificado em `pages/documentacao.py`)
    - Prefixos numéricos nos nomes de arquivos de páginas
    - Manipulação de `sys.path` em páginas individuais (centralizada em `app.py`)
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 5. PROCEDIMENTOS E FLUXOS OPERACIONAIS
# ══════════════════════════════════════════════════════════════════════════
st.header("5. Procedimentos e Fluxos Operacionais")

st.subheader("5.1 Ciclo de Vida dos Dados Acadêmicos (Upload → Persistência)")
st.markdown(
    """
    O arquivo CSV exportado do SIGAA passa pelas seguintes etapas:

    | Etapa | O que acontece | Onde fica |
    |-------|---------------|-----------|
    | **1. Upload** | Usuário arrasta/seleciona o CSV na página Home | Arquivo original **não é alterado** |
    | **2. Parsing** | Sistema detecta encoding, ignora 4 linhas de cabeçalho SIGAA, renomeia colunas | Processamento em memória |
    | **3. Mescla de Observações** | Se `dados/notas_discentes.csv` já existe em disco, as observações pedagógicas e de docentes são mescladas no novo DataFrame (apenas campos vazios no CSV novo) | Upload + disco |
    | **4. Sessão** | DataFrame é armazenado em `st.session_state.df`; cópia original em `df_original`; UUID de sessão criado | Memória (volátil) |
    | **5. Navegação** | Páginas de leitura (Conselho Intermediário, Discentes) consomem o DataFrame sem modificá-lo | Memória |
    | **6. Edição** | Páginas de escrita (Pedagógico, Conselho Final) adicionam colunas de observações e características ao DataFrame | Memória |
    | **7. Salvamento** | Ao clicar em "Salvar", o sistema persiste o DataFrame enriquecido em disco | `dados/notas_discentes.csv` |
    | **8. Backup** | Simultaneamente, cria cópia com timestamp | `dados/backups/notas_discentes_YYYYMMDD_HHMMSS.csv` |
    | **9. Auditoria** | Registra cada campo alterado (valor anterior × novo) | `dados/audit_edits.csv` |

    **Pontos-chave:**
    - O arquivo original do SIGAA **nunca é modificado** pelo sistema
    - Se o navegador for fechado sem salvar, **as edições em memória são perdidas**
    - O arquivo `dados/notas_discentes.csv` é a **fonte única** de todas as observações
      (pedagógicas e de docentes) — ao fazer um novo upload, as observações são
      recuperadas automaticamente desse arquivo
    - O arquivo `dados/notas_discentes.csv` pode ser re-carregado na Home para
      **continuar uma sessão anterior** (preserva todas as observações salvas)
    - A cada salvamento, um backup é criado automaticamente — **nenhum dado é sobrescrito
      sem backup**
    """
)

st.subheader("5.2 Fluxo do Conselho de Classe")
st.markdown(
    """
    Procedimento típico para realização de um Conselho de Classe:

    **Preparação (antes da reunião):**
    1. Exportar o "Mapa de Conceito" do SIGAA (formato CSV com separador `;`)
    2. Acessar o sistema e fazer upload do CSV na página **Home**
    3. Confirmar que os dados foram carregados corretamente

    **Conselho Intermediário:**
    1. Acessar a página **Conselho Intermediário**
    2. Filtrar por fase(s) desejada(s)
    3. Navegar estudante a estudante, analisando gráficos de notas/faltas
       e a Matriz Curricular
    4. (Nenhuma edição é feita nesta etapa — apenas visualização)

    **Conselho Final (por professor):**
    1. Acessar a página **Conselho Final**
    2. Selecionar a(s) disciplina(s) do professor
    3. Para cada estudante: registrar observações e marcar características
       (15 positivas + 15 negativas)
    4. Clicar em **"Salvar Tudo"** ao final de cada sessão de registro

    **Análise Pedagógica (coordenação):**
    1. Acessar a página **Pedagógico** após os professores terem registrado
       suas observações
    2. Analisar os indicadores de risco gerados automaticamente
    3. Registrar observações pedagógicas da coordenação
    4. Salvar as observações pedagógicas
    """
)

st.subheader("5.3 Fluxo de Solicitações (Pré-Requisitos e Validações)")
st.markdown(
    """
    Cada página possui **memorando independente** (checklist → pré-visualização → envio → histórico):

    | Etapa | Página | Ação |
    |-------|--------|------|
    | **Cadastro** | Pré-Requisito, Validações ou Matrículas | Coordenação registra a solicitação do estudante (formulário) |
    | **Avaliação** | Pré-Requisito ou Validações | Coordenação avalia: Deferido ou Indeferido + parecer |
    | **Memorando** | Mesma página da solicitação | Seleciona casos deferidos, gera texto de memorando, faz download `.txt` |
    | **Envio** | Mesma página da solicitação | Marca como "memorando enviado" para controle |

    Dados persistidos em **3 arquivos CSV independentes** (não dependem do upload do SIGAA):
    - `dados/solicitacoes_prerequisito.csv` — quebras de pré-requisito
    - `dados/solicitacoes_validacoes.csv` — validações de disciplinas
    - `dados/solicitacoes_matricula_avulsa.csv` — matrículas avulsas (incluindo TC2)
    """
)

st.subheader("5.4 Manutenção de Dados Estáticos")
st.markdown(
    """
    Alguns arquivos são **alimentados manualmente** (editando o CSV diretamente)
    e não possuem interface de cadastro no sistema:

    | Arquivo | Formato | Quando atualizar |
    |---------|---------|-----------------|
    | `dados/Docentes.csv` | CSV | Gerenciado pela página **Docentes** (cadastro, edição, checkboxes Colegiado/NDE) |
    | `dados/Coordenadores.csv` | CSV (4 colunas: índice, CURSO, SIGLA, COORDENADOR) | Gerenciado pela página **Docentes** (seção Coordenadores) |
    | `data/matriz.json` | JSON | Quando houver alteração na grade curricular (disciplinas, pré-requisitos, créditos) |
    | `data/disciplinas.py` | Python | Quando houver adição, remoção ou renomeação de disciplinas no currículo |

    **Procedimento para atualização:**
    1. Abrir o arquivo em um editor de texto ou planilha
    2. Editar os dados necessários mantendo o formato existente
    3. Salvar o arquivo (manter encoding UTF-8)
    4. Reiniciar o sistema para que as alterações sejam carregadas
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 6. MATRIZ CURRICULAR DO ESTUDANTE
# ══════════════════════════════════════════════════════════════════════════
st.header("6. Matriz Curricular do Estudante")
st.markdown(
    """
    A visualização da Matriz Curricular é um componente compartilhado
    (`renderizar_matriz_curricular` em `utils.py`) usado nas páginas
    **Conselho Intermediário** e **Discentes**.

    **Como funciona:**
    1. Carrega o currículo de `data/matriz.json` (10 semestres, 63+ disciplinas)
    2. Identifica disciplinas **cursando** a partir do DataFrame do estudante
    3. Infere disciplinas **aprovadas** comparando a fase atual com os semestres das disciplinas
    4. Mapeia códigos SIGAA variantes para os códigos canônicos do currículo (`SIGAA_EXTRA`)
    5. Renderiza um grid de 10 colunas com cards HTML/CSS coloridos

    **Classificação por cor:**

    | Status | Cor | Critério |
    |--------|-----|----------|
    | 🟢 Aprovada | Verde (`#27ae60`) | Disciplina de semestre ≤ fase atual e não cursando |
    | 🟡 Cursando | Amarelo (`#f1c40f`) | Código encontrado no DataFrame do estudante |
    | ⚪ Pendente | Cinza (`#bdc3c7`) | Não se enquadra nos anteriores |

    **Disciplinas especiais:**
    - Disciplinas que abrangem múltiplos semestres (ex.: Estágio 9º–10º sem.)
      são renderizadas como cards spanning
    - Atividades Complementares (1º–10º sem.) são renderizadas como barra full-width

    **Resumo exibido:** contagem de aprovadas, cursando, pendentes, fase atual e
    percentual de progresso no currículo.
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 7. MOTOR DE RISCO PEDAGÓGICO
# ══════════════════════════════════════════════════════════════════════════
st.header("7. Motor de Risco Pedagógico")
st.markdown(
    """
    O módulo **Pedagógico** implementa um motor de análise de risco baseado
    nas características registradas pelos professores no **Conselho Final**.

    **Características disponíveis (30 total):**
    - **15 positivas** (POS_01 a POS_15): ex.: Participativo, Dedicado, Organizado
    - **15 negativas** (NEG_01 a NEG_15): com 3 níveis de gravidade

    **Sistema de pontuação:**

    | Nível | Características | Peso |
    |-------|-----------------|------|
    | Leve | NEG_01 a NEG_05 | 1 ponto |
    | Moderado | NEG_06 a NEG_10 | 2 pontos |
    | Grave | NEG_11 a NEG_15 | 3 pontos |

    **Classificação de risco:**
    - 🟢 **Sem Alertas** — pontuação abaixo do limiar mínimo
    - 🟡 **Alerta Disciplinar** — pontuação intermediária
    - 🔴 **Risco Sistêmico** — pontuação ≥ limiar crítico; inclui detecção automática
      de padrões de evasão (ex.: Apatia + Desinteresse simultâneos)
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 8. DADOS E ARQUIVOS
# ══════════════════════════════════════════════════════════════════════════
st.header("8. Dados e Arquivos")

st.subheader("8.1 Arquivo de Entrada — SIGAA CSV")
st.markdown(
    """
    O sistema espera um arquivo exportado do SIGAA no formato **"Mapa de Conceito"**.
    Estrutura esperada:
    - **4 linhas de cabeçalho** (metadados do SIGAA — ignoradas)
    - Colunas mapeadas automaticamente:

    | Coluna SIGAA | Nome Interno | Descrição |
    |-------------|-------------|-----------|
    | `Período` | `Fase` | Semestre/período |
    | `Código` | `Codigo` | Código da disciplina |
    | `Disciplina` | `Disciplina` | Nome da disciplina |
    | `Matrícula` | `Matricula` | Matrícula do estudante |
    | `Nome discente` | `Aluno` | Nome do estudante |
    | `Nota` | `Nota` | Nota/conceito |
    | `Resultado` | `Situacao` | Situação (aprovado, reprovado, etc.) |
    | `Faltas` | `Faltas` | Número de faltas |
    | `Freq.` | `Infrequencia` | Percentual de infrequência |
    """
)

st.subheader("8.2 Arquivos Internos")
st.markdown(
    """
    | Arquivo | Formato | Descrição |
    |---------|---------|-----------|
    | `dados/notas_discentes.csv` | CSV (`;`) | Dados acadêmicos com observações adicionadas |
    | `dados/Docentes.csv` | CSV | Cadastro de docentes do curso |
    | `dados/Coordenadores.csv` | CSV | Cadastro de coordenadores |
    | `dados/solicitacoes_prerequisito.csv` | CSV | Solicitações de quebra de pré-requisito |
    | `dados/solicitacoes_validacoes.csv` | CSV | Solicitações de validação de disciplinas |
    | `dados/solicitacoes_matricula_avulsa.csv` | CSV | 🆕 Solicitações de matrícula avulsa |
    | `dados/protocolos_sipac.csv` | CSV | Protocolos institucionais |
    | `dados/reunioes_colegiado.json` | JSON | Reuniões do Colegiado (membros, pauta, encaminhamentos, ata) |
    | `dados/reunioes_nde.json` | JSON | Reuniões do NDE (membros, pauta, encaminhamentos, ata) |
    | `dados/google_credentials.json` | JSON | Credenciais Google (conta de serviço) — opcional, para edição na página Ajustes |
    | `dados/audit_edits.csv` | CSV | Trilha de auditoria |
    | `dados/backups/*.csv` | CSV | Backups automáticos com timestamp |
    | `data/disciplinas.py` | Python | 🆕 Nomes centralizados das disciplinas (NOMES, SIGAA_EXTRA, etc.) |
    | `data/matriz.json` | JSON | Matriz curricular (semestres, pré-requisitos, créditos) |
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 9. CONCEITOS DE DOMÍNIO
# ══════════════════════════════════════════════════════════════════════════
st.header("9. Conceitos de Domínio")

st.subheader("Pré-requisito")
st.markdown(
    """
    Disciplina que **deve ser aprovada antes** de cursar outra.
    Exemplo: *CA1* é pré-requisito de *CA2*, que é pré-requisito de *CA3*.
    Isso forma uma **cadeia**: se CA1 não for cursada, CA2 e CA3 ficam bloqueadas.
    """
)

st.subheader("Co-requisito")
st.markdown(
    """
    Disciplina que **deve ser cursada simultaneamente** (no mesmo semestre).
    Exemplo: *CE1* tem *FI3* como co-requisito — ambas devem ser matriculadas juntas.
    """
)

st.subheader("Cadeia de Dependência")
st.markdown(
    """
    Sequência transitiva de pré-requisitos. A análise percorre o grafo
    recursivamente para mostrar **todo o impacto** de não cursar uma disciplina,
    não apenas os dependentes diretos.
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 10. TECNOLOGIAS
# ══════════════════════════════════════════════════════════════════════════
st.header("10. Tecnologias Utilizadas")
st.markdown(
    """
    | Tecnologia | Uso |
    |------------|-----|
    | **Python 3** | Linguagem base |
    | **Streamlit** | Framework web / interface interativa |
    | **gspread** | Acesso à API do Google Sheets (leitura e escrita) |
    | **google-auth** | Autenticação via conta de serviço Google |
    | **NetworkX** | Modelagem de grafo dirigido (dependências) |
    | **Pandas** | Manipulação de dados (DataFrames) |
    | **Plotly** | Gráficos de barras (notas e faltas) |
    | **streamlit-elements** | Gráfico Radar (Nivo) |
    | **streamlit-option-menu** | Menu de navegação customizado |
    | **streamlit-wordcloud** | Nuvem de palavras (módulo Pedagógico) |
    """
)

# ══════════════════════════════════════════════════════════════════════════
# 11. HISTÓRICO
# ══════════════════════════════════════════════════════════════════════════
st.header("11. Histórico de Desenvolvimento")

st.markdown(
    """
    | Data | Versão | Alterações |
    |------|--------|------------|
    | 14/02/2026 | v1.0 | Versão inicial com pyvis (grafo interativo) |
    | 14/02/2026 | v2.0 | Refatoração completa: grid por semestre, cards coloridos, análise de dependência com opacidade, painel de detalhes, correção de dados (`matriz.json`), remoção de pyvis |
    | 14/02/2026 | v2.1 | Adição de página de Documentação, reestruturação para multi-page app |
    | 14/02/2026 | v3.0 | Estratégias de matrícula (5 algoritmos), créditos por disciplina, página de recomendações com comparação entre estratégias |
    | 15/02/2026 | v3.1 | Disciplinas optativas (catálogo + slots OP1–OP4), seleção dinâmica com atualização de dependências na matriz |
    | 15/02/2026 | v3.2 | Estágio Curricular Supervisionado (EST) como card spanning 9º–10º semestre; Atividades Complementares (ATC) como card compacto full-width 1º–10º semestre; EST e ATC selecionáveis como aprovadas na sidebar com nomes completos |
    | 20/02/2026 | v4.0 | Integração com ConselhoApp: entrypoint unificado (`app.py`), módulo de Coordenação com 10 páginas (Conselhos, Pedagógico, Docentes, Discentes, Pré-Requisitos, Validações, Matrículas/Memorandos), Matriz Curricular do Estudante como componente compartilhado (`renderizar_matriz_curricular`), motor de risco pedagógico, trilha de auditoria, documentação unificada |
    | 02/03/2026 | v4.1 | Memorandos independentes por página (Pré-Requisito, Validações, Matrículas); matrícula avulsa com CSV exclusivo (`solicitacoes_matricula_avulsa.csv`) e fluxo TC2; centralização de nomes de disciplinas em `data/disciplinas.py`; `construir_disciplinas_cod_nome()` para formato padronizado "COD - Nome" |
    | 02/03/2026 | v5.0 | **Reestruturação completa do projeto** (veja seção 4.10): eliminação da pasta `ConselhoApp/` e symlinks; `utils.py` movido para a raiz; páginas reorganizadas em subpastas espelhando a navegação (`coordenacao_tarefas/`, `coordenacao/`, `planejamento/`); `dados/` e `fotos/` como diretórios reais na raiz; imagens centralizadas em `assets/`; remoção de prefixos numéricos e hacks de `sys.path`; documentação consolidada em `pages/documentacao.py`; correção de todos os paths e imports |
    | 09/03/2026 | v5.1 | **Página Ajustes de Matrícula** (`pages/coordenacao_tarefas/ajustes.py`): integração com Google Sheets (formulário de ajustes); modo somente leitura via planilha publicada + modo escrita via credenciais JSON (conta de serviço Google Cloud); filtros por curso e parecer; edição de colunas Q/R; resumo com métricas; **seletor global de curso** na Home (`st.session_state.curso_selecionado`) propagado para Ajustes e Relatório Geral; gráfico de evolução com colunas separadas (demandas × ajustes) |
    | 16/03/2026 | v5.2 | **Reuniões do Colegiado e NDE**: páginas completas para gerenciamento de reuniões com criação, lista de presença, pontos de pauta, encaminhamentos, geração automática de ata e PDF de lista de presença com cabeçalho/rodapé institucional; **checkbox NDE na página Docentes** (coluna `NDE` no CSV) para marcação direta de membros do NDE, alimentando automaticamente a página de Reunião do NDE; **Portaria do NDE** na página Docentes (geração de texto + download TXT + cópia de e-mails); remoção do seletor manual de membros do NDE; dados padrão: horário 10:30–12:30, local Auditório A112, data DD/MM/AAAA; foco automático na reunião recém-criada |
    | 01/04/2026 | v5.3 | **Persistência de observações via CSV**: ao fazer upload de um novo CSV do SIGAA, o sistema mescla automaticamente as observações (pedagógicas e de docentes) do `dados/notas_discentes.csv` anterior, eliminando a necessidade de arquivo JSON separado — fonte única de dados; **filtro por Discente** na página Pedagógico (busca direta pelo estudante via selectbox); correção dos botões de navegação Próximo/Anterior; slider 1-based ("Estudante 1 de N") |
    """
)
