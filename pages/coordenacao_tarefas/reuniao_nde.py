import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date

# Configuração da página
st.set_page_config(page_title="Reunião do NDE", layout="wide")

from utils import setup_sidebar_header, aplicar_css_padding
setup_sidebar_header()
aplicar_css_padding()

# ==================== CONSTANTES ====================
REUNIOES_PATH = os.path.join("dados", "reunioes_nde.json")
DOCENTES_PATH = os.path.join("dados", "Docentes.csv")
COORDENADORES_PATH = os.path.join("dados", "Coordenadores.csv")

MESES_PT = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}

_ano = datetime.now().year
_semestre_atual = f"{_ano}.{1 if datetime.now().month <= 6 else 2}"


# ==================== PERSISTÊNCIA ====================
def carregar_reunioes():
    if os.path.exists(REUNIOES_PATH):
        with open(REUNIOES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_reunioes(reunioes):
    os.makedirs("dados", exist_ok=True)
    with open(REUNIOES_PATH, "w", encoding="utf-8") as f:
        json.dump(reunioes, f, ensure_ascii=False, indent=2)


def proximo_id(reunioes):
    if not reunioes:
        return 1
    return max(r["id"] for r in reunioes) + 1


# ==================== MEMBROS DO NDE ====================
def obter_coordenador_ee():
    """Retorna o nome do coordenador de EE (presidente do NDE)."""
    if os.path.exists(COORDENADORES_PATH):
        df = pd.read_csv(COORDENADORES_PATH, dtype=str).fillna("")
        row_ee = df[df["SIGLA"].str.strip() == "EE"]
        if not row_ee.empty:
            return row_ee.iloc[0]["COORDENADOR"].strip().upper()
    return ""


def obter_membros_nde_para_reuniao():
    """Retorna lista de membros do NDE com papel, lidos do Docentes.csv."""
    resultado = []
    coord_ee = obter_coordenador_ee()
    if coord_ee:
        resultado.append({"nome": coord_ee, "papel": "Presidente"})

    if os.path.exists(DOCENTES_PATH):
        df = pd.read_csv(DOCENTES_PATH, dtype=str).fillna("")
        nde = df[df["NDE"].str.strip().str.upper() == "TRUE"]
        nomes_ja = {m["nome"].upper() for m in resultado}
        for _, r in nde.iterrows():
            nome = r["Docente"].strip().upper()
            if nome and nome not in nomes_ja:
                resultado.append({"nome": nome, "papel": "Membro Docente"})

    return resultado


# ==================== GERAÇÃO DA ATA ====================
def gerar_ata(reuniao):
    data_obj = datetime.strptime(reuniao["data"], "%Y-%m-%d")
    data_extenso = f"{data_obj.day} de {MESES_PT[data_obj.month]} de {data_obj.year}"

    presentes = [m for m in reuniao.get("membros", []) if m.get("presente")]
    ausentes = [m for m in reuniao.get("membros", []) if not m.get("presente")]

    linhas_presentes = "\n".join(
        f"   - {m['nome']} ({m.get('papel', '')})" for m in presentes
    )
    linhas_ausentes = ""
    if ausentes:
        linhas_ausentes = "\nAusentes / Justificados:\n" + "\n".join(
            f"   - {m['nome']} ({m.get('papel', '')})"
            + (f" — Justificativa: {m.get('justificativa', '')}" if m.get("justificativa") else "")
            for m in ausentes
        )

    pontos = reuniao.get("pontos_pauta", [])
    encaminhamentos = {e["ponto"]: e["descricao"] for e in reuniao.get("encaminhamentos", [])}

    texto_pontos = ""
    for p in pontos:
        num = p["numero"]
        texto_pontos += f"\n{num}. {p['titulo']}\n"
        if p.get("discussao"):
            texto_pontos += f"   {p['discussao']}\n"
        enc = encaminhamentos.get(num, "")
        if enc:
            texto_pontos += f"   Encaminhamento: {enc}\n"

    pauta_lista = "\n".join(f"   {p['numero']}. {p['titulo']}" for p in pontos)

    tipo_upper = reuniao.get("tipo", "Ordinária").upper()

    ata = (
        f"ATA DA {reuniao.get('numero', '')}ª REUNIÃO {tipo_upper} DO NÚCLEO DOCENTE "
        f"ESTRUTURANTE (NDE) DO CURSO DE BACHARELADO EM ENGENHARIA ELÉTRICA\n"
        f"CÂMPUS JARAGUÁ DO SUL-RAU\n\n"
        f"Aos {data_extenso}, às {reuniao.get('horario_inicio', '')}, "
        f"reuniram-se no {reuniao.get('local', 'Câmpus Jaraguá do Sul-Rau')}, "
        f"os membros do Núcleo Docente Estruturante (NDE) do Curso de Bacharelado "
        f"em Engenharia Elétrica para a {reuniao.get('numero', '')}ª Reunião "
        f"{reuniao.get('tipo', 'Ordinária')}, "
        f"semestre {reuniao.get('semestre', _semestre_atual)}, "
        f"com a seguinte pauta:\n\n"
        f"PAUTA:\n{pauta_lista}\n\n"
        f"Participantes presentes:\n{linhas_presentes}\n"
        f"{linhas_ausentes}\n\n"
        f"DESENVOLVIMENTO:\n{texto_pontos}\n"
        f"Nada mais havendo a tratar, a reunião foi encerrada às "
        f"{reuniao.get('horario_fim', '')}, e eu, "
        f"{presentes[0]['nome'] if presentes else '___________'}, "
        f"lavrei a presente ata que, após lida e aprovada, será assinada "
        f"por todos os presentes.\n\n"
        f"Jaraguá do Sul, {data_extenso}.\n"
    )

    return ata


# ==================== PÁGINA PRINCIPAL ====================
st.title("📋 Reunião do NDE")

reunioes = carregar_reunioes()
membros_nde_reuniao = obter_membros_nde_para_reuniao()

# ── Semestres disponíveis ───────────────────────
semestres = sorted({r.get("semestre", "") for r in reunioes} | {_semestre_atual})

col_sem, col_nova = st.columns([2, 1])
with col_sem:
    semestre_sel = st.selectbox("Semestre", semestres, index=semestres.index(_semestre_atual) if _semestre_atual in semestres else 0)
with col_nova:
    st.markdown("<div style='margin-top:1.6rem'></div>", unsafe_allow_html=True)
    btn_nova = st.button("➕ Nova Reunião", type="primary", use_container_width=True)

reunioes_sem = [r for r in reunioes if r.get("semestre") == semestre_sel]
reunioes_sem.sort(key=lambda r: r.get("numero", 0))


# ── Diálogo: Nova Reunião ──────────────────────────
@st.dialog("➕ Nova Reunião do NDE", width="large")
def _dialog_nova_reuniao():
    with st.form("form_nova_reuniao_nde"):
        st.subheader("Dados da Reunião")
        col1, col2, col3 = st.columns(3)
        with col1:
            numero = st.number_input("Número da reunião", min_value=1, value=len(reunioes_sem) + 1)
        with col2:
            tipo = st.selectbox("Tipo", ["Ordinária", "Extraordinária"])
        with col3:
            data_reuniao = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")

        col4, col5, col6 = st.columns(3)
        with col4:
            h_inicio = st.text_input("Horário de início", value="10:30")
        with col5:
            h_fim = st.text_input("Horário de término", value="12:30")
        with col6:
            local = st.text_input("Local", value="Auditório A112")

        submit = st.form_submit_button("Criar Reunião", type="primary")
        if submit:
            nova = {
                "id": proximo_id(reunioes),
                "numero": int(numero),
                "tipo": tipo,
                "data": data_reuniao.strftime("%Y-%m-%d"),
                "horario_inicio": h_inicio.strip(),
                "horario_fim": h_fim.strip(),
                "local": local.strip(),
                "semestre": semestre_sel,
                "membros": [{"nome": m["nome"], "papel": m["papel"], "presente": True, "justificativa": ""} for m in membros_nde_reuniao],
                "pontos_pauta": [],
                "encaminhamentos": [],
            }
            reunioes.append(nova)
            salvar_reunioes(reunioes)
            st.session_state["_sel_reuniao_nde"] = nova["id"]
            st.success("✅ Reunião criada!")
            st.rerun()


if btn_nova:
    _dialog_nova_reuniao()

# ── Seletor de reunião ──────────────────────────
if not reunioes_sem:
    st.info("Nenhuma reunião registrada para este semestre. Clique em **➕ Nova Reunião** para iniciar.")
    st.stop()

opcoes_reuniao = {}
for r in reunioes_sem:
    label = f"{r['numero']}ª Reunião {r['tipo']} — {datetime.strptime(r['data'], '%Y-%m-%d').strftime('%d/%m/%Y')}"
    if label in opcoes_reuniao:
        label = f"{label} (#{r['id']})"
    opcoes_reuniao[label] = r["id"]
_sel_default_id = st.session_state.pop("_sel_reuniao_nde", None)
_default_idx = 0
if _sel_default_id is not None:
    for _i, _rid in enumerate(opcoes_reuniao.values()):
        if _rid == _sel_default_id:
            _default_idx = _i
            break
label_sel = st.selectbox("Selecione a reunião", list(opcoes_reuniao.keys()), index=_default_idx)
reuniao_id = opcoes_reuniao[label_sel]
reuniao = next(r for r in reunioes if r["id"] == reuniao_id)
reuniao_idx = reunioes.index(reuniao)

st.markdown("---")

# ==================== DADOS DA REUNIÃO ====================
st.subheader("📝 Dados da Reunião")
col_d1, col_d2, col_d3 = st.columns(3)
with col_d1:
    ed_numero = st.number_input("Número", min_value=1, value=reuniao.get("numero", 1), key=f"ed_num_{reuniao_id}")
    ed_tipo = st.selectbox("Tipo", ["Ordinária", "Extraordinária"], index=0 if reuniao.get("tipo") == "Ordinária" else 1, key=f"ed_tipo_{reuniao_id}")
with col_d2:
    ed_data = st.date_input("Data", value=datetime.strptime(reuniao["data"], "%Y-%m-%d").date(), key=f"ed_data_{reuniao_id}", format="DD/MM/YYYY")
    ed_local = st.text_input("Local", value=reuniao.get("local", ""), key=f"ed_local_{reuniao_id}")
with col_d3:
    ed_h_inicio = st.text_input("Horário de início", value=reuniao.get("horario_inicio", ""), key=f"ed_h_ini_{reuniao_id}")
    ed_h_fim = st.text_input("Horário de término", value=reuniao.get("horario_fim", ""), key=f"ed_h_fim_{reuniao_id}")

# ==================== LISTA DE PRESENÇA ====================
st.markdown("---")
st.subheader("✅ Lista de Presença")

membros_reuniao = reuniao.get("membros", [])
# Sincroniza membros atuais com os da reunião
nomes_reuniao = {m["nome"] for m in membros_reuniao}
for m in membros_nde_reuniao:
    if m["nome"] not in nomes_reuniao:
        membros_reuniao.append({"nome": m["nome"], "papel": m["papel"], "presente": True, "justificativa": ""})

presenca_atualizada = []
for i, m in enumerate(membros_reuniao):
    col_check, col_nome, col_just = st.columns([0.5, 2, 2])
    with col_check:
        presente = st.checkbox("Presente", value=m.get("presente", True), key=f"pres_{reuniao_id}_{i}", label_visibility="collapsed")
    with col_nome:
        st.markdown(f"**{m['nome']}** — *{m.get('papel', '')}*")
    with col_just:
        justificativa = ""
        if not presente:
            justificativa = st.text_input("Justificativa", value=m.get("justificativa", ""), key=f"just_{reuniao_id}_{i}", label_visibility="collapsed", placeholder="Justificativa da ausência...")
    presenca_atualizada.append({
        "nome": m["nome"],
        "papel": m.get("papel", ""),
        "presente": presente,
        "justificativa": justificativa,
    })

# ==================== PONTOS DE PAUTA E ENCAMINHAMENTOS ====================
st.markdown("---")
st.subheader("📌 Pontos de Pauta e Encaminhamentos")

pontos = reuniao.get("pontos_pauta", [])
encaminhamentos_map = {e["ponto"]: e["descricao"] for e in reuniao.get("encaminhamentos", [])}

ss_key = f"n_pontos_nde_{reuniao_id}"
if ss_key not in st.session_state:
    st.session_state[ss_key] = max(len(pontos), 1)

col_add, col_rem = st.columns([1, 1])
with col_add:
    if st.button("➕ Adicionar Ponto de Pauta", key="add_ponto"):
        st.session_state[ss_key] += 1
        st.rerun()
with col_rem:
    if st.session_state[ss_key] > 1:
        if st.button("➖ Remover Último Ponto", key="rem_ponto"):
            st.session_state[ss_key] -= 1
            st.rerun()

pontos_atualizados = []
encaminhamentos_atualizados = []

for idx in range(st.session_state[ss_key]):
    num = idx + 1
    ponto_existente = pontos[idx] if idx < len(pontos) else {}
    enc_existente = encaminhamentos_map.get(num, "")

    with st.expander(f"**{num}. {ponto_existente.get('titulo', 'Novo ponto de pauta')}**", expanded=True if not ponto_existente.get("titulo") else False):
        titulo = st.text_input("Título do ponto de pauta", value=ponto_existente.get("titulo", ""), key=f"pt_tit_{reuniao_id}_{idx}", placeholder="Ex.: Aprovação da ata anterior")
        discussao = st.text_area("Discussão / Desenvolvimento", value=ponto_existente.get("discussao", ""), key=f"pt_disc_{reuniao_id}_{idx}", height=100, placeholder="Descreva a discussão realizada sobre este ponto...")
        encaminhamento = st.text_area("Encaminhamento", value=enc_existente, key=f"pt_enc_{reuniao_id}_{idx}", height=80, placeholder="Decisão ou encaminhamento aprovado...")

    pontos_atualizados.append({"numero": num, "titulo": titulo, "discussao": discussao})
    if encaminhamento.strip():
        encaminhamentos_atualizados.append({"ponto": num, "descricao": encaminhamento})

# ==================== BOTÕES DE AÇÃO ====================
st.markdown("---")
col_salvar, col_excluir = st.columns([2, 1])

with col_salvar:
    if st.button("💾 Salvar Reunião", type="primary", use_container_width=True):
        reunioes[reuniao_idx]["numero"] = int(ed_numero)
        reunioes[reuniao_idx]["tipo"] = ed_tipo
        reunioes[reuniao_idx]["data"] = ed_data.strftime("%Y-%m-%d")
        reunioes[reuniao_idx]["horario_inicio"] = ed_h_inicio.strip()
        reunioes[reuniao_idx]["horario_fim"] = ed_h_fim.strip()
        reunioes[reuniao_idx]["local"] = ed_local.strip()
        reunioes[reuniao_idx]["membros"] = presenca_atualizada
        reunioes[reuniao_idx]["pontos_pauta"] = pontos_atualizados
        reunioes[reuniao_idx]["encaminhamentos"] = encaminhamentos_atualizados
        salvar_reunioes(reunioes)
        st.session_state[f"ata_ver_nde_{reuniao_id}"] = st.session_state.get(f"ata_ver_nde_{reuniao_id}", 0) + 1
        st.success("✅ Reunião salva com sucesso!")
        st.rerun()

with col_excluir:
    if st.button("🗑️ Excluir Reunião", use_container_width=True):
        st.session_state[f"confirmar_exclusao_nde_{reuniao_id}"] = True

    if st.session_state.get(f"confirmar_exclusao_nde_{reuniao_id}", False):
        st.warning("Tem certeza que deseja excluir esta reunião?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Sim, excluir", key=f"conf_exc_{reuniao_id}"):
                reunioes = [r for r in reunioes if r["id"] != reuniao_id]
                salvar_reunioes(reunioes)
                del st.session_state[f"confirmar_exclusao_nde_{reuniao_id}"]
                st.success("Reunião excluída.")
                st.rerun()
        with c2:
            if st.button("❌ Cancelar", key=f"canc_exc_{reuniao_id}"):
                del st.session_state[f"confirmar_exclusao_nde_{reuniao_id}"]
                st.rerun()

# ==================== GERAÇÃO DA ATA ====================
st.markdown("---")
st.subheader("📄 Ata da Reunião")

reuniao_para_ata = {
    **reuniao,
    "numero": int(ed_numero),
    "tipo": ed_tipo,
    "data": ed_data.strftime("%Y-%m-%d"),
    "horario_inicio": ed_h_inicio.strip(),
    "horario_fim": ed_h_fim.strip(),
    "local": ed_local.strip(),
    "membros": presenca_atualizada,
    "pontos_pauta": pontos_atualizados,
    "encaminhamentos": encaminhamentos_atualizados,
}

# Gera a ata sempre com os dados atuais do formulário
ata_gerada = gerar_ata(reuniao_para_ata)

_ata_ver = st.session_state.get(f"ata_ver_nde_{reuniao_id}", 0)
ata_texto = st.text_area(
    "Prévia da Ata (editável)",
    value=ata_gerada,
    height=500,
    key=f"ata_edit_{reuniao_id}_v{_ata_ver}",
)

st.download_button(
    label="📥 Baixar Ata (TXT)",
    data=ata_texto.encode("utf-8"),
    file_name=f"ata_nde_{reuniao.get('numero', '')}_{semestre_sel}.txt",
    mime="text/plain",
    use_container_width=True,
)
