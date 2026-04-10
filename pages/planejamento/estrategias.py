import streamlit as st
import json
import pandas as pd
from model.grafo import aplicar_optativas, construir_grafo
from service.planejamento import classificar
from service.estrategia import ESTRATEGIAS, DESCRICOES, estrategia_otima
from data.disciplinas import NOMES

# ── Dados ────────────────────────────────────────────────────────────────
with open("data/matriz.json", encoding="utf-8") as f:
    dados_json = json.load(f)

curriculo_base = {k: v for k, v in dados_json.items() if k != "optativas"}
optativas = dados_json.get("optativas", {})

selecoes_op = {
    f"OP{i}": st.session_state.get(f"opt_op{i}")
    for i in range(1, 5)
}
curriculo = aplicar_optativas(curriculo_base, optativas, selecoes_op)
G = construir_grafo(curriculo)

# Mapeamento de nomes para exibição (OPx → código da optativa selecionada)
_op_display = {slot: code for slot, code in selecoes_op.items() if code}

# ── Estado da sessão ─────────────────────────────────────────────────────
if "aprovadas" not in st.session_state:
    st.session_state.aprovadas = set()

# ── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configurações")

    todas = sorted(G.nodes())

    def _label_aprovada(code):
        display_code = _op_display.get(code, code)
        nome = NOMES.get(display_code, NOMES.get(code, code))
        return f"{display_code} — {nome}" if nome != display_code else display_code
        # return display_code

    aprovadas_sel = st.multiselect(
        "Disciplinas aprovadas",
        todas,
        default=sorted(st.session_state.aprovadas),
        format_func=_label_aprovada,
        key="sel_aprovadas_est",
    )
    st.session_state.aprovadas = set(aprovadas_sel)

# ── CSS ──────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .rec-card {
        border-radius: 10px;
        padding: 14px 16px;
        margin: 6px 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.12);
        line-height: 1.4;
    }
    .rec-rank {
        font-size: 1.6rem;
        font-weight: 800;
        opacity: 0.3;
        float: left;
        margin-right: 12px;
        line-height: 1;
    }
    .rec-sigla {
        font-size: 1.1rem;
        font-weight: 700;
    }
    .rec-meta {
        font-size: 0.78rem;
        opacity: 0.8;
        margin-top: 2px;
    }
    .score-bar {
        height: 6px;
        border-radius: 3px;
        margin-top: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Título ───────────────────────────────────────────────────────────────
st.markdown("# 📊 Estratégias de Matrícula")
st.caption("Recomendação inteligente de disciplinas com base em diferentes objetivos")

# ── Resumo do progresso ─────────────────────────────────────────────────
aprovadas = st.session_state.aprovadas
total = len(G.nodes())
n_aprov = len(aprovadas)
status = classificar(G, aprovadas)
n_lib = sum(1 for s in status.values() if s == "liberada")
n_bloq = sum(1 for s in status.values() if s == "bloqueada")
cred_aprov = sum(G.nodes[d].get("creditos", 4) for d in aprovadas if d in G)
cred_total = sum(G.nodes[d].get("creditos", 4) for d in G.nodes())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Aprovadas", f"{n_aprov}/{total}", f"{n_aprov*100//total}%")
c2.metric("Liberadas", n_lib)
c3.metric("Bloqueadas", n_bloq)
c4.metric("Créditos", f"{cred_aprov}/{cred_total}")

if n_lib == 0 and n_aprov < total:
    st.warning("⚠️ Nenhuma disciplina liberada no momento. Verifique as aprovadas na sidebar.")
    st.stop()

if n_aprov == total:
    st.success("🎉 Todas as disciplinas foram aprovadas! Parabéns pela formatura!")
    st.stop()

# ── Seleção de estratégia ────────────────────────────────────────────────
col_strat, col_params = st.columns([3, 2])

with col_strat:
    nomes = list(ESTRATEGIAS.keys())
    nome_estrategia = st.selectbox("Estratégia", nomes, index=len(nomes) - 1)
    st.info(DESCRICOES.get(nome_estrategia, ""))

with col_params:
    max_creditos = st.slider(
        "Limite de créditos por semestre",
        min_value=8, max_value=36, value=24, step=2,
        help="Máximo de créditos a matricular no semestre",
    )

    if nome_estrategia == "Ótima — Heurística ponderada":
        st.markdown("**Pesos do algoritmo**")
        alfa = st.slider("α (impacto)", 0.0, 1.0, 0.6, 0.05)
        beta = round(1.0 - alfa, 2)
        st.caption(f"β (profundidade) = {beta}")

# ── Executar estratégia ─────────────────────────────────────────────────
if nome_estrategia == "Ótima — Heurística ponderada":
    recomendacoes = estrategia_otima(G, aprovadas, max_creditos, alfa, beta)
else:
    fn = ESTRATEGIAS[nome_estrategia]
    recomendacoes = fn(G, aprovadas, max_creditos)

# ── Resultados ───────────────────────────────────────────────────────────
st.divider()

if not recomendacoes:
    st.warning("Nenhuma disciplina recomendada com os parâmetros atuais.")
    st.stop()

total_cred_rec = sum(r.creditos for r in recomendacoes)
st.subheader(
    f"📋 Matrícula Recomendada — {len(recomendacoes)} disciplinas "
    f"({total_cred_rec} créditos)"
)

# Score máximo para normalizar barra
max_score = max(r.score for r in recomendacoes) if recomendacoes else 1

# Cards de recomendação
for i, rec in enumerate(recomendacoes, 1):
    sem = G.nodes[rec.sigla]["semestre"]
    bar_pct = (rec.score / max_score * 100) if max_score > 0 else 0

    # Cor baseada na posição
    cores = ["#27ae60", "#2ecc71", "#3498db", "#2980b9", "#9b59b6",
             "#8e44ad", "#f39c12", "#e67e22", "#e74c3c", "#c0392b"]
    cor = cores[min(i - 1, len(cores) - 1)]

    st.markdown(
        f'<div class="rec-card" style="border-left: 4px solid {cor};">'
        f'<span class="rec-rank">{i}</span>'
        f'<span class="rec-sigla">{rec.sigla}</span>'
        f' &nbsp;·&nbsp; {sem}º sem &nbsp;·&nbsp; {rec.creditos} créditos'
        f'<div class="rec-meta">{rec.motivo}</div>'
        f'<div class="rec-meta">Impacto: {rec.impacto} · '
        f'Profundidade: {rec.profundidade} · '
        f'Score: {rec.score:.2f}</div>'
        f'<div class="score-bar" style="width:{bar_pct}%; '
        f'background:{cor};"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Tabela comparativa ──────────────────────────────────────────────────
st.divider()
with st.expander("📊 Tabela detalhada", expanded=False):
    df = pd.DataFrame([
        {
            "Posição": i,
            "Disciplina": r.sigla,
            "Semestre": G.nodes[r.sigla]["semestre"],
            "Créditos": r.creditos,
            "Score": round(r.score, 2),
            "Impacto": r.impacto,
            "Profundidade": r.profundidade,
            "Motivo": r.motivo,
        }
        for i, r in enumerate(recomendacoes, 1)
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)

# ── Comparação entre estratégias ─────────────────────────────────────────
st.divider()
with st.expander("🔀 Comparar todas as estratégias", expanded=False):
    st.caption("Quais disciplinas cada estratégia recomenda com os mesmos parâmetros")

    comparacao = {}
    for nome, fn in ESTRATEGIAS.items():
        if nome == "Ótima — Heurística ponderada":
            recs = estrategia_otima(G, aprovadas, max_creditos)
        else:
            recs = fn(G, aprovadas, max_creditos)
        comparacao[nome] = recs

    linhas = []
    for nome, recs in comparacao.items():
        siglas = [r.sigla for r in recs]
        cred = sum(r.creditos for r in recs)
        linhas.append({
            "Estratégia": nome,
            "Disciplinas": ", ".join(siglas),
            "Qtd": len(siglas),
            "Créditos": cred,
        })

    df_comp = pd.DataFrame(linhas)
    st.dataframe(df_comp, use_container_width=True, hide_index=True)
