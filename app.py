import streamlit as st
import sys
import os

# ── Configuração da página (chamada UMA ÚNICA VEZ) ─────────────────────
_real_set_page_config = getattr(st, "_real_set_page_config", st.set_page_config)
st._real_set_page_config = _real_set_page_config
_real_set_page_config(
    page_title="Sistema Acadêmico",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Impede que páginas chamem set_page_config novamente
st.set_page_config = lambda *a, **kw: None

# ── Adiciona raiz ao sys.path (para `from utils import ...`) ────────────
_root_dir = os.path.dirname(os.path.abspath(__file__))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

# ── Patch da navegação ──────────────────────────────────────────────────
# Substituímos setup_sidebar_header para exibir apenas as imagens do sidebar.
import utils

def _sidebar_logos():
    """Exibe logos no sidebar."""
    st.sidebar.image(os.path.join("assets", "figConselho2.png"))
    st.sidebar.image(os.path.join("assets", "figConselho.png"))

utils.setup_sidebar_header = _sidebar_logos
utils.show_sidebar = _sidebar_logos

# ── Páginas diretas (sidebar raiz) ───────────────────────────────────────
home = st.Page(
    "pages/home.py",
    title="Home",
    icon="🏠",
    default=True,
)
documentacao = st.Page(
    "pages/documentacao.py",
    title="Documentação",
    icon="📚",
)
relatorio_geral = st.Page(
    "pages/relatorio_geral.py",
    title="Relatório Geral",
    icon="📊",
)

# ── Coordenação (Tarefas) ───────────────────────────────────────────────
conselho_interm = st.Page(
    "pages/coordenacao_tarefas/conselho_intermediario.py",
    title="Conselho Intermediário",
    icon="📋",
)
pre_requisito = st.Page(
    "pages/coordenacao_tarefas/pre_requisito.py",
    title="Pré-Requisito",
    icon="🔗",
)
validacoes = st.Page(
    "pages/coordenacao_tarefas/validacoes.py",
    title="Validação",
    icon="📄",
)
matriculas = st.Page(
    "pages/coordenacao_tarefas/matriculas.py",
    title="Matrículas",
    icon="📨",
)
protocolo_sipac = st.Page(
    "pages/coordenacao_tarefas/protocolo_sipac.py",
    title="Protocolo (SIPAC)",
    icon="📑",
)
ajustes = st.Page(
    "pages/coordenacao_tarefas/ajustes.py",
    title="Ajustes",
    icon="📝",
)
reuniao_colegiado = st.Page(
    "pages/coordenacao_tarefas/reuniao_colegiado.py",
    title="Reunião do Colegiado",
    icon="🏛️",
)
reuniao_nde = st.Page(
    "pages/coordenacao_tarefas/reuniao_nde.py",
    title="Reunião do NDE",
    icon="📋",
)

# ── Coordenação ──────────────────────────────────────────────────────────
conselho_final = st.Page(
    "pages/coordenacao/conselho_final.py",
    title="Conselho Final",
    icon="👨‍🏫",
)
docentes = st.Page(
    "pages/coordenacao/docentes.py",
    title="Docentes",
    icon="👥",
)
discentes = st.Page(
    "pages/coordenacao/discentes.py",
    title="Discentes",
    icon="🎓",
)
pedagogico = st.Page(
    "pages/coordenacao/pedagogico.py",
    title="Pedagógico",
    icon="📝",
)

# ── Planejamento Acadêmico ───────────────────────────────────────────────
painel = st.Page(
    "pages/planejamento/painel.py",
    title="Painel Acadêmico",
    icon="📐",
)
estrategias = st.Page(
    "pages/planejamento/estrategias.py",
    title="Estratégias de Matrícula",
    icon="📊",
)

# ── Desenvolvedor ────────────────────────────────────────────────────────
desenvolvedor = st.Page(
    "pages/desenvolvedor.py",
    title="Desenvolvedor",
    icon="🛠️",
)

# ── Navegação unificada com seções separadas ─────────────────────────────
nav = st.navigation(
    {
        "": [
            home,
            documentacao,
            relatorio_geral,
        ],
        "Coordenação (Tarefas)": [
            conselho_interm,
            pre_requisito,
            validacoes,
            matriculas,
            protocolo_sipac,
            ajustes,
            reuniao_colegiado,
            reuniao_nde,
        ],
        "Coordenação": [
            conselho_final,
            docentes,
            discentes,
            pedagogico,
        ],
        "Planejamento Acadêmico": [
            painel,
            estrategias,
        ],
        " ": [
            desenvolvedor,
        ],
    }
)
nav.run()
