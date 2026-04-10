# Painel Acadêmico

Sistema de gestão acadêmica para coordenação de curso de Engenharia Elétrica,
desenvolvido com [Streamlit](https://streamlit.io/). Permite acompanhamento de
notas e frequência, emissão de memorandos, planejamento curricular com grafo de
pré-requisitos e estratégias de matrícula.

---

## Como executar

### Opção 1 — Docker (recomendado para distribuição)

> Funciona em **macOS** (Intel / Apple Silicon), **Windows** e **Linux** sem
> precisar instalar Python.

**Pré-requisito:** instalar o [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
# 1. Copie a pasta do projeto para o computador destino

# 2. Abra um terminal na pasta do projeto e execute:
docker compose up --build

# 3. Acesse no navegador:
#    http://localhost:8501
```

**Atalhos rápidos:**

| Sistema     | Script                             |
|-------------|------------------------------------|
| macOS/Linux | `./start-docker.sh`               |
| Windows     | duplo-clique em `start.bat`        |

**Para parar:**

```bash
docker compose down
```

---

### Opção 2 — Python local (para desenvolvimento)

**Pré-requisitos:** Python 3.10+ instalado.

```bash
# 1. Crie um ambiente virtual
python -m venv .venv

# 2. Ative o ambiente
#    macOS / Linux:
source .venv/bin/activate
#    Windows:
.venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute
streamlit run app.py
```

Ou simplesmente: `./start.sh` (macOS/Linux com `.venv` já criado).

---

## Estrutura do projeto

```
├── app.py                          # Ponto de entrada — configura página e navegação
├── utils.py                        # Funções utilitárias, constantes e gráficos Plotly
├── requirements.txt                # Dependências Python
├── start.sh                        # Inicialização rápida (venv local)
├── start-docker.sh                 # Inicialização via Docker (macOS/Linux)
├── start.bat                       # Inicialização via Docker (Windows)
├── Dockerfile                      # Imagem Docker multi-estágio
├── docker-compose.yml              # Orquestração com volume de dados
├── .dockerignore                   # Exclusões do build Docker
│
├── assets/                         # Recursos visuais
│   ├── figConselho.png
│   └── figConselho2.png
│
├── dados/                          # Dados CSV da aplicação
│   ├── audit_edits.csv             #   Histórico de edições
│   ├── Coordenadores.csv           #   Coordenadores do curso
│   ├── Docentes.csv                #   Corpo docente
│   ├── notas_discentes.csv         #   Notas e frequência
│   ├── pre_requisitos.csv          #   Pré-requisitos
│   ├── protocolos_sipac.csv        #   Protocolos SIPAC
│   ├── solicitacoes_validacoes.csv  #   Solicitações de validação
│   ├── solicitacoes_matricula_avulsa.csv
│   ├── solicitacoes_prerequisito.csv
│   └── backups/                    #   Backups automáticos de edições
│
├── data/                           # Módulos de dados
│   ├── __init__.py
│   ├── disciplinas.py              #   Nomes, siglas e códigos SIGAA
│   └── matriz.json                 #   Matriz curricular (pré/co-requisitos, créditos)
│
├── model/                          # Modelos de domínio
│   └── grafo.py                    #   Grafo de pré/co-requisitos (NetworkX)
│
├── service/                        # Lógica de negócio
│   ├── estrategia.py               #   Estratégias de matrícula (ranking de disciplinas)
│   └── planejamento.py             #   Classificação aprovado/desbloqueado/bloqueado
│
├── pages/                          # Páginas Streamlit
│   ├── home.py                     #   Home — upload de CSV e bootstrap
│   ├── documentacao.py             #   Documentação do sistema
│   ├── relatorio_geral.py          #   Relatório geral da coordenação
│   │
│   ├── coordenacao/                #   📂 Coordenação
│   │   ├── conselho_final.py       #     Conselho final — notas e edição SIGAA
│   │   ├── discentes.py            #     Listagem de discentes
│   │   ├── docentes.py             #     Listagem de docentes
│   │   └── pedagogico.py           #     Análise pedagógica intermediária
│   │
│   ├── coordenacao_tarefas/        #   📂 Tarefas da coordenação
│   │   ├── conselho_intermediario.py #    Conselho intermediário (gráficos, radar)
│   │   ├── matriculas.py           #     Memorandos de matrícula
│   │   ├── pre_requisito.py        #     Dispensas de pré-requisito
│   │   ├── protocolo_sipac.py      #     Protocolos SIPAC
│   │   └── validacoes.py           #     Validação/aproveitamento de disciplinas
│   │
│   └── planejamento/               #   📂 Planejamento acadêmico
│       ├── painel.py               #     Painel interativo da matriz curricular
│       └── estrategias.py          #     Comparativo de estratégias de matrícula
│
└── fotos/                          # Fotos dos discentes (opcional)
```

---

## Funcionalidades

| Módulo | Descrição |
|--------|-----------|
| **Home** | Upload da base de dados CSV e inicialização da sessão |
| **Conselho Final** | Visualização de notas/faltas por aluno com gráficos e edição SIGAA |
| **Conselho Intermediário** | Análise de meio de semestre com gráficos radar |
| **Pedagógico** | Análise pedagógica com matriz curricular |
| **Matrículas** | Geração e acompanhamento de memorandos de matrícula |
| **Pré-Requisito** | Gestão de dispensas de pré-requisito |
| **Validações** | Aproveitamento e transferência de disciplinas |
| **Protocolo SIPAC** | CRUD de protocolos por docente/semestre |
| **Painel Acadêmico** | Visualização interativa do grafo curricular |
| **Estratégias** | Ranking de disciplinas por diferentes heurísticas de matrícula |
| **Relatório Geral** | Dados agregados de toda a coordenação |

---

## Distribuição para outros computadores

### Opção A — Copiar o projeto + Docker

Copie a pasta inteira para o computador destino (que tenha Docker instalado) e
execute `docker compose up --build`. Todas as dependências são instaladas
automaticamente dentro do container.

### Opção B — Exportar a imagem Docker (sem internet no destino)

```bash
# No seu computador (que já tem a imagem construída):
docker compose build
docker save painel-academico-painel-academico | gzip > painel-academico.tar.gz

# Copie para o outro PC:
#   - painel-academico.tar.gz
#   - docker-compose.yml
#   - pasta dados/

# No computador destino (com Docker instalado):
docker load < painel-academico.tar.gz
docker compose up -d
```

Acesse: **http://localhost:8501**

---

## Tecnologias

- **Python 3.12** (no container Docker)
- **Streamlit 1.51** — interface web
- **Pandas** — manipulação de dados
- **Plotly** — gráficos interativos
- **NetworkX** — grafo de pré-requisitos
- **Docker** — distribuição multiplataforma
# PainelAcademicoIFSC
