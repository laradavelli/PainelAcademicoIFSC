import streamlit as st
import json
from model.grafo import aplicar_optativas, construir_grafo, obter_info_disciplina
from service.planejamento import (
    classificar,
    dependencias,
    pre_requisitos_diretos,
    dependentes_diretos,
    co_requisitos,
)
from data.disciplinas import NOMES

# ── Dados ────────────────────────────────────────────────────────────────
with open("data/matriz.json", encoding="utf-8") as f:
    dados_json = json.load(f)

curriculo_base = {k: v for k, v in dados_json.items() if k != "optativas"}
optativas = dados_json.get("optativas", {})

# ── Estado da sessão ─────────────────────────────────────────────────────
if "aprovadas" not in st.session_state:
    st.session_state.aprovadas = set()
if "foco" not in st.session_state:
    st.session_state.foco = None
if "modo_analise" not in st.session_state:
    st.session_state.modo_analise = "Direta"

# ── Optativas selecionadas ───────────────────────────────────────────────
selecoes_op = {
    f"OP{i}": st.session_state.get(f"opt_op{i}")
    for i in range(1, 5)
}
curriculo = aplicar_optativas(curriculo_base, optativas, selecoes_op)
G = construir_grafo(curriculo)

# Mapeamento de nomes para exibição (OPx → código da optativa selecionada)
op_display = {slot: code for slot, code in selecoes_op.items() if code}

# ── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configurações")

    todas = sorted(G.nodes())

    def _label_aprovada(code):
        """Rótulo de exibição no multiselect de aprovadas."""
        display_code = op_display.get(code, code)
        nome = NOMES.get(display_code, NOMES.get(code, code))
        return f"{display_code} — {nome}" if nome != display_code else display_code

    aprovadas_sel = st.multiselect(
        "Disciplinas aprovadas",
        todas,
        default=sorted(st.session_state.aprovadas),
        format_func=_label_aprovada,
        key="sel_aprovadas",
    )
    st.session_state.aprovadas = set(aprovadas_sel)

    st.divider()
    modo = st.radio(
        "🔎 Modo de análise ao clicar",
        ["🔍 Direta", "🔬 Raio-X"],
        index=0 if st.session_state.modo_analise == "Direta" else 1,
        help="Direta: mostra apenas pré-requisitos e dependentes imediatos.\n"
             "Raio-X: mostra toda a cadeia por transitividade.",
        horizontal=True,
    )
    st.session_state.modo_analise = "Direta" if modo == "🔍 Direta" else "Raio-X"

    st.divider()
    st.markdown(
        """
        **Legenda**
        - 🟢 Aprovada
        - 🟡 Liberada para matrícula
        - ⚪ Bloqueada
        - 🔵 Pré-requisito (da selecionada)
        - 🔴 Dependente / impactada
        - 🟠 Co-requisito
        - 🟣 Disciplina em foco
        """
    )

# ── Classificação ────────────────────────────────────────────────────────
status = classificar(G, st.session_state.aprovadas)

pre_foco: list[str] = []
pos_foco: list[str] = []
co_foco: list[str] = []

if st.session_state.foco:
    if st.session_state.modo_analise == "Raio-X":
        pre_foco, pos_foco = dependencias(G, st.session_state.foco)
    else:
        pre_foco = pre_requisitos_diretos(G, st.session_state.foco)
        pos_foco = dependentes_diretos(G, st.session_state.foco)
    co_foco = co_requisitos(G, st.session_state.foco)


# ── Funções auxiliares de estilo ─────────────────────────────────────────
def _cor_card(disc: str) -> str:
    """Retorna cor de fundo do card conforme contexto."""
    if st.session_state.foco:
        if disc == st.session_state.foco:
            return "#9b59b6"  # roxo – foco
        if disc in pre_foco:
            if disc in st.session_state.aprovadas:
                return "#27ae60"  # verde – pré-requisito já aprovado
            return "#2980b9"  # azul – pré-requisito pendente
        if disc in pos_foco:
            return "#e74c3c"  # vermelho – dependente
        if disc in co_foco:
            return "#e67e22"  # laranja – co-requisito

    if disc in st.session_state.aprovadas:
        return "#27ae60"  # verde – aprovada
    if status[disc] == "liberada":
        return "#f1c40f"  # amarelo – liberada
    return "#bdc3c7"  # cinza – bloqueada


def _opacidade(disc: str) -> float:
    if not st.session_state.foco:
        return 1.0
    if disc in (
        [st.session_state.foco] + pre_foco + pos_foco + co_foco
    ):
        return 1.0
    return 0.18


def _cor_texto(disc: str) -> str:
    cor = _cor_card(disc)
    claros = {"#f1c40f", "#bdc3c7"}
    return "#2c3e50" if cor in claros else "#ffffff"


def _toggle_foco(disc: str):
    """Callback para alternar o foco ao clicar em um card."""
    if st.session_state.foco == disc:
        st.session_state.foco = None
    else:
        st.session_state.foco = disc


# ── CSS global ───────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .main .block-container { padding-top: 1rem; max-width: 100%; }
    h1 { text-align: center; margin-bottom: 0.2rem; }
    .sem-header {
        text-align: center;
        font-weight: 700;
        font-size: 0.85rem;
        color: #7f8c8d;
        margin-bottom: 0.4rem;
        letter-spacing: 1px;
    }
    /* Card visual */
    .disc-card {
        border-radius: 8px;
        padding: 8px 6px;
        text-align: center;
        font-weight: 700;
        font-size: 0.82rem;
        line-height: 1.25;
        min-height: 62px;
        max-height: 62px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.15);
        cursor: pointer;
    }
    .disc-card .sub {
        font-weight: 400;
        font-size: 0.5rem;
        opacity: 0.8;
        display: block;
        margin-top: 1px;
        line-height: 1.15;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        max-width: 100%;
    }
    /* Wrapper com efeito hover */
    [class*="st-key-wrap_"] {
        transition: transform 0.18s ease, box-shadow 0.18s ease;
        border-radius: 8px;
        margin: 4px 0;
    }
    [class*="st-key-wrap_"]:hover {
        transform: scale(1.12);
        box-shadow: 0 6px 18px rgba(0,0,0,0.30);
        z-index: 10;
        position: relative;
    }
    /* Botão transparente sobreposto ao card */
    [class*="st-key-card_"] {
        margin-top: -66px;
        position: relative;
        z-index: 5;
    }
    [class*="st-key-card_"] button {
        opacity: 0 !important;
        min-height: 62px !important;
        border: none !important;
        cursor: pointer !important;
    }
    /* ── Partial spanning cards rendered inside the grid (e.g. EST 9º-10º) ── */
    [class*="st-key-wrap_dspan_"] {
        overflow: visible !important;
        transition: transform 0.18s ease, box-shadow 0.18s ease;
        border-radius: 8px;
        margin: 4px 0;
    }
    [class*="st-key-wrap_dspan_"] .disc-card {
        width: calc(200% + 1rem);
        min-width: calc(200% + 1rem);
    }
    [class*="st-key-wrap_dspan_"]:hover {
        transform: scale(1.06);
        box-shadow: 0 6px 18px rgba(0,0,0,0.30);
        z-index: 10;
        position: relative;
    }
    [class*="st-key-card_dspan_"] {
        margin-top: -66px;
        position: relative;
        z-index: 5;
        overflow: visible !important;
    }
    [class*="st-key-card_dspan_"] button {
        opacity: 0 !important;
        min-height: 62px !important;
        width: calc(200% + 1rem) !important;
        border: none !important;
        cursor: pointer !important;
    }
    /* ── Compact spanning cards (e.g. Atividades Complementares) ── */
    .disc-card-span-compact {
        border-radius: 6px;
        padding: 4px 10px;
        text-align: center;
        font-weight: 600;
        font-size: 0.72rem;
        line-height: 1.2;
        min-height: 32px;
        max-height: 32px;
        overflow: hidden;
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: center;
        gap: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.15);
        cursor: pointer;
    }
    [class*="st-key-wrap_spanc_"] {
        transition: transform 0.18s ease, box-shadow 0.18s ease;
        border-radius: 6px;
        margin: 4px 0;
    }
    [class*="st-key-wrap_spanc_"]:hover {
        transform: scale(1.03);
        box-shadow: 0 4px 14px rgba(0,0,0,0.25);
        z-index: 10;
        position: relative;
    }
    [class*="st-key-card_spanc_"] {
        margin-top: -36px;
        position: relative;
        z-index: 5;
    }
    [class*="st-key-card_spanc_"] button {
        opacity: 0 !important;
        min-height: 32px !important;
        border: none !important;
        cursor: pointer !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Título ───────────────────────────────────────────────────────────────
st.markdown("# 🎓 Painel de Planejamento Acadêmico")
st.caption("Bacharelado em Engenharia Elétrica — Matriz Curricular com análise de dependências")

# Não gostei de colocar isso aqui. Deixar comentado por enquanto até decidir melhor onde encaixar essa informação de análise de foco. 
# if st.session_state.foco:
#     st.info(
#         f"🔍 Analisando **{st.session_state.foco}** — "
#         f"🔵 Pré-requisitos ({len(pre_foco)})  "
#         f"🔴 Dependentes ({len(pos_foco)})  "
#         f"🟠 Co-requisitos ({len(co_foco)})"
#     )

# ── Grid da Matriz Curricular ───────────────────────────────────────────
num_semestres = len(curriculo)
cols = st.columns(num_semestres, gap="small")

for i, (semestre, disciplinas) in enumerate(
    sorted(curriculo.items(), key=lambda x: int(x[0]))
):
    with cols[i]:
        st.markdown(
            f'<div class="sem-header">{semestre}º SEM</div>',
            unsafe_allow_html=True,
        )

        for j, disc in enumerate(disciplinas):
            # Skip full-width spanning disciplines (rendered in a dedicated row below)
            sfim = disciplinas[disc].get("semestre_fim")
            if sfim and (sfim - int(semestre) + 1) >= num_semestres:
                continue

            cor = _cor_card(disc)
            opac = _opacidade(disc)
            cor_txt = _cor_texto(disc)

            info = obter_info_disciplina(G, disc)
            pre_dir = info["pre_diretos"]
            co_dir = info["co_requisitos"]

            # Nome de exibição (optativa selecionada ou código original)
            display = op_display.get(disc, disc)
            nome_completo = NOMES.get(display, display)

            # Monta subtexto com pré e co-requisitos
            sub_parts = []
            if pre_dir:
                pre_nomes = [op_display.get(p, p) for p in pre_dir]
                sub_parts.append(f'<span class="sub">← {", ".join(pre_nomes)}</span>')
            if co_dir:
                co_nomes = [op_display.get(c, c) for c in co_dir]
                sub_parts.append(f'<span class="sub">⇄ {", ".join(co_nomes)}</span>')
            sub_html = "".join(sub_parts)

            # Card visual + botão transparente dentro de um wrapper
            sfim_disc = disciplinas[disc].get("semestre_fim")
            if sfim_disc:
                wrap_key = f"wrap_dspan_{disc}"
                card_key = f"card_dspan_{disc}"
                btn_key = f"btn_dspan_{disc}"
            else:
                wrap_key = f"wrap_{i}_{j}"
                card_key = f"card_{i}_{j}"
                btn_key = f"btn_{i}_{j}"
            with st.container(key=wrap_key):
                st.markdown(
                    f'<div class="disc-card" '
                    f'style="background:{cor}; opacity:{opac}; color:{cor_txt};">'
                    f"{display}{sub_html}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                with st.container(key=card_key):
                    st.button(
                        display,
                        key=btn_key,
                        help=f"Clique para analisar as dependências de {nome_completo}",
                        use_container_width=True,
                        on_click=_toggle_foco,
                        args=(disc,),
                    )

# ── Cards que abrangem toda a grade (e.g. Atividades Complementares) ────
spanning_discs = []
for semestre, disciplinas in sorted(curriculo.items(), key=lambda x: int(x[0])):
    for disc, data in disciplinas.items():
        sfim = data.get("semestre_fim")
        if sfim and (sfim - int(semestre) + 1) >= num_semestres:
            spanning_discs.append((disc, int(semestre), sfim))

for disc, sem_inicio, sem_fim in spanning_discs:
    span_width = sem_fim - sem_inicio + 1

    span_cols = st.columns([1], gap="small")

    cor = _cor_card(disc)
    opac = _opacidade(disc)
    cor_txt = _cor_texto(disc)

    display = op_display.get(disc, disc)
    nome_completo = NOMES.get(display, display)

    with span_cols[0]:
        wrap_key = f"wrap_spanc_{disc}"
        with st.container(key=wrap_key):
            st.markdown(
                f'<div class="disc-card-span-compact" '
                f'style="background:{cor}; opacity:{opac}; color:{cor_txt};">' 
                f"{nome_completo}"
                f"</div>",
                unsafe_allow_html=True,
            )

            card_key = f"card_spanc_{disc}"
            with st.container(key=card_key):
                st.button(
                    display,
                    key=f"btn_spanc_{disc}",
                    help=f"Clique para analisar as dependências de {nome_completo}",
                    use_container_width=True,
                    on_click=_toggle_foco,
                    args=(disc,),
                )
st.markdown("#### 📋 Disciplinas Optativas")
st.caption(
    "Selecione as disciplinas para cada slot optativo. "
    "As dependências na matriz serão atualizadas automaticamente."
)

_op_row1 = st.columns(2)
_op_row2 = st.columns(2)
_op_slots_cols = [
    ("OP1", _op_row1[0]),
    ("OP2", _op_row1[1]),
    ("OP3", _op_row2[0]),
    ("OP4", _op_row2[1]),
]
_opt_list = sorted(optativas.keys())

def _label_optativa(code):
    nome = NOMES.get(code, code)
    return f"{code} — {nome}" if nome != code else code

for _slot, _col in _op_slots_cols:
    with _col:
        st.selectbox(
            _slot,
            options=_opt_list,
            index=None,
            format_func=_label_optativa,
            placeholder="Selecione...",
            key=f"opt_{_slot.lower()}",
        )

# ── Painel de detalhes ──────────────────────────────────────────────────
if st.session_state.foco:
    st.divider()
    disc = st.session_state.foco
    disc_display = op_display.get(disc, disc)
    info = obter_info_disciplina(G, disc)
    is_raio = st.session_state.modo_analise == "Raio-X"

    icone_modo = "🔬" if is_raio else "🔍"
    label_modo = "Raio-X" if is_raio else "Análise direta"
    st.markdown(f"### {icone_modo} {label_modo}: **{disc_display}**")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.subheader("🔵 Pré-requisitos")
        if pre_foco:
            if is_raio:
                pre_dir = pre_requisitos_diretos(G, disc)
                pre_dir_d = [op_display.get(p, p) for p in sorted(pre_dir)]
                st.markdown(f"**Diretos:** {', '.join(pre_dir_d) or '—'}")
            por_sem: dict[int, list[str]] = {}
            for p in pre_foco:
                s = G.nodes[p]["semestre"]
                por_sem.setdefault(s, []).append(p)
            titulo_lista = f"Cadeia completa ({len(pre_foco)})" if is_raio else f"Total: {len(pre_foco)}"
            st.markdown(f"**{titulo_lista}**")
            for s in sorted(por_sem):
                marcados = []
                for d in sorted(por_sem[s]):
                    marca = "✅" if d in st.session_state.aprovadas else "⬜"
                    marcados.append(f"{marca} {op_display.get(d, d)}")
                st.markdown(f"**{s}º Sem:** {', '.join(marcados)}")
        else:
            st.write("Nenhum pré-requisito.")

    with c2:
        st.subheader("🟣 Detalhes")
        if info.get("semestre_fim"):
            st.metric("Semestre", f"{info['semestre']}º — {info['semestre_fim']}º")
        else:
            st.metric("Semestre", f"{info['semestre']}º")
        pre_dir_d2 = [op_display.get(p, p) for p in info['pre_diretos']]
        st.write(f"**Pré-req. diretos:** {', '.join(pre_dir_d2) or '—'}")
        co_d = [op_display.get(c, c) for c in info['co_requisitos']]
        st.write(f"**Co-requisitos:** {', '.join(co_d) or '—'}")
        dep_dir = dependentes_diretos(G, disc)
        dep_dir_d = [op_display.get(d, d) for d in dep_dir]
        st.write(f"**Dependentes diretos:** {', '.join(dep_dir_d) or '—'}")
        st.write(f"**Status:** {status[disc].capitalize()}")
        if is_raio:
            st.metric("Cadeia total", f"{len(pre_foco)} pré / {len(pos_foco)} dep")

    with c3:
        st.subheader("🔴 Impacto Futuro")
        if pos_foco:
            if is_raio:
                dep_dir2 = dependentes_diretos(G, disc)
                dep_dir2_d = [op_display.get(d, d) for d in sorted(dep_dir2)]
                st.markdown(f"**Diretos:** {', '.join(dep_dir2_d) or '—'}")
            por_sem2: dict[int, list[str]] = {}
            for p in pos_foco:
                s = G.nodes[p]["semestre"]
                por_sem2.setdefault(s, []).append(p)
            titulo_lista2 = f"Cadeia completa ({len(pos_foco)})" if is_raio else f"Total: {len(pos_foco)}"
            st.markdown(f"**{titulo_lista2}**")
            for s in sorted(por_sem2):
                nomes = [op_display.get(d, d) for d in sorted(por_sem2[s])]
                st.markdown(f"**{s}º Sem:** {', '.join(nomes)}")
            msg = (
                f"⚠️ **{disc_display}** impacta **{len(pos_foco)} disciplina(s)** ao longo de toda a matriz."
                if is_raio else
                f"⚠️ Se **{disc_display}** não for cursada, **{len(pos_foco)} disciplina(s)** serão impactadas."
            )
            st.warning(msg)
        else:
            st.write("Nenhuma disciplina depende desta.")
