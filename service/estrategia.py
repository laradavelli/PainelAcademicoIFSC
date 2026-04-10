"""Serviço de estratégias de matrícula.

Cada estratégia recebe o grafo G, o conjunto de aprovadas e o limite de
créditos por semestre, retornando uma lista ordenada de disciplinas
recomendadas com seus scores e justificativas.
"""

from __future__ import annotations

import networkx as nx
from service.planejamento import classificar, co_requisitos


# ─── helpers ─────────────────────────────────────────────────────────────

def _subgrafo_pre(G: nx.DiGraph) -> nx.DiGraph:
    """Retorna subgrafo apenas com arestas de pré-requisito."""
    return nx.DiGraph(
        [(u, v) for u, v, d in G.edges(data=True) if d["tipo"] == "pre"]
    )


def _liberadas(G: nx.DiGraph, aprovadas: set[str]) -> list[str]:
    """Disciplinas liberadas (não aprovadas e com todos os pré-req. atendidos)."""
    status = classificar(G, aprovadas)
    return [d for d, s in status.items() if s == "liberada"]


def _impacto(G_pre: nx.DiGraph, disc: str) -> int:
    """Número de descendentes (disciplinas que dependem desta)."""
    if disc not in G_pre:
        return 0
    return len(nx.descendants(G_pre, disc))


def _profundidade(G_pre: nx.DiGraph, disc: str) -> int:
    """Comprimento do caminho mais longo partindo desta disciplina."""
    if disc not in G_pre:
        return 0
    return nx.dag_longest_path_length(
        G_pre.subgraph(nx.descendants(G_pre, disc) | {disc})
    )


def _creditos(G: nx.DiGraph, disc: str) -> int:
    return G.nodes[disc].get("creditos", 4)


def _incluir_co_requisitos(
    G: nx.DiGraph, selecionadas: list[str], aprovadas: set[str]
) -> list[str]:
    """Adiciona co-requisitos obrigatórios das disciplinas selecionadas."""
    extras: list[str] = []
    for disc in selecionadas:
        for co in co_requisitos(G, disc):
            if co not in aprovadas and co not in selecionadas and co not in extras:
                extras.append(co)
    return selecionadas + extras


# ─── Resultado ───────────────────────────────────────────────────────────

class Recomendacao:
    """Uma disciplina recomendada com metadados de scoring."""

    def __init__(
        self, sigla: str, score: float, creditos: int,
        impacto: int, profundidade: int, motivo: str,
    ):
        self.sigla = sigla
        self.score = score
        self.creditos = creditos
        self.impacto = impacto
        self.profundidade = profundidade
        self.motivo = motivo

    def __repr__(self):
        return f"<Rec {self.sigla} score={self.score:.1f} cr={self.creditos}>"


# ─── Estratégias ─────────────────────────────────────────────────────────

def estrategia_menor_tempo(
    G: nx.DiGraph, aprovadas: set[str], max_creditos: int,
) -> list[Recomendacao]:
    """Estratégia A — Menor tempo até formatura.

    Prioriza disciplinas que estão no caminho crítico (maior profundidade
    no grafo de dependências), pois atrasá-las implica atrasar a formatura.
    """
    G_pre = _subgrafo_pre(G)
    livres = _liberadas(G, aprovadas)
    recs: list[Recomendacao] = []

    for disc in livres:
        prof = _profundidade(G_pre, disc)
        imp = _impacto(G_pre, disc)
        score = prof * 3 + imp  # peso forte em profundidade
        recs.append(Recomendacao(
            sigla=disc, score=score, creditos=_creditos(G, disc),
            impacto=imp, profundidade=prof,
            motivo=f"Profundidade {prof} — no caminho crítico",
        ))

    recs.sort(key=lambda r: r.score, reverse=True)
    return _selecionar_com_limite(G, recs, aprovadas, max_creditos)


def estrategia_desbloquear(
    G: nx.DiGraph, aprovadas: set[str], max_creditos: int,
) -> list[Recomendacao]:
    """Estratégia B — Desbloquear mais disciplinas.

    Prioriza disciplinas cujos dependentes diretos já terão todos os
    pré-requisitos atendidos após aprovação (maximiza desbloqueios imediatos).
    """
    G_pre = _subgrafo_pre(G)
    livres = _liberadas(G, aprovadas)
    recs: list[Recomendacao] = []

    for disc in livres:
        # Simula aprovação desta disciplina
        simuladas = aprovadas | {disc}
        desbloqueios = 0
        for suc in (G_pre.successors(disc) if disc in G_pre else []):
            pre_suc = [
                u for u, _, d in G.in_edges(suc, data=True) if d["tipo"] == "pre"
            ]
            if all(p in simuladas for p in pre_suc):
                desbloqueios += 1

        imp = _impacto(G_pre, disc)
        score = desbloqueios * 5 + imp
        recs.append(Recomendacao(
            sigla=disc, score=score, creditos=_creditos(G, disc),
            impacto=imp, profundidade=_profundidade(G_pre, disc),
            motivo=f"Desbloqueia {desbloqueios} disciplina(s) diretamente",
        ))

    recs.sort(key=lambda r: r.score, reverse=True)
    return _selecionar_com_limite(G, recs, aprovadas, max_creditos)


def estrategia_gargalos(
    G: nx.DiGraph, aprovadas: set[str], max_creditos: int,
) -> list[Recomendacao]:
    """Estratégia C — Minimizar gargalos.

    Prioriza disciplinas que pertencem às cadeias mais longas (medido
    pelo número total de descendentes — impacto).
    """
    G_pre = _subgrafo_pre(G)
    livres = _liberadas(G, aprovadas)
    recs: list[Recomendacao] = []

    for disc in livres:
        imp = _impacto(G_pre, disc)
        prof = _profundidade(G_pre, disc)
        score = imp * 3 + prof  # peso forte em impacto
        recs.append(Recomendacao(
            sigla=disc, score=score, creditos=_creditos(G, disc),
            impacto=imp, profundidade=prof,
            motivo=f"Impacta {imp} disciplina(s) — gargalo crítico"
            if imp >= 5 else f"Impacta {imp} disciplina(s)",
        ))

    recs.sort(key=lambda r: r.score, reverse=True)
    return _selecionar_com_limite(G, recs, aprovadas, max_creditos)


def estrategia_balanceamento(
    G: nx.DiGraph, aprovadas: set[str], max_creditos: int,
) -> list[Recomendacao]:
    """Estratégia D — Balanceamento de carga.

    Tenta preencher o semestre de forma equilibrada, priorizando
    disciplinas do semestre mais atrasado e respeitando créditos.
    """
    G_pre = _subgrafo_pre(G)
    livres = _liberadas(G, aprovadas)
    recs: list[Recomendacao] = []

    for disc in livres:
        sem = G.nodes[disc]["semestre"]
        imp = _impacto(G_pre, disc)
        prof = _profundidade(G_pre, disc)
        # Prioridade: semestre mais baixo + impacto secundário
        score = (11 - sem) * 2 + imp * 0.5 + prof * 0.3
        recs.append(Recomendacao(
            sigla=disc, score=score, creditos=_creditos(G, disc),
            impacto=imp, profundidade=prof,
            motivo=f"{sem}º semestre — equilibrar carga",
        ))

    recs.sort(key=lambda r: r.score, reverse=True)
    return _selecionar_com_limite(G, recs, aprovadas, max_creditos)


def estrategia_otima(
    G: nx.DiGraph, aprovadas: set[str], max_creditos: int,
    alfa: float = 0.6, beta: float = 0.4,
) -> list[Recomendacao]:
    """Estratégia Ótima — Heurística ponderada.

    score = α · impacto_norm + β · profundidade_norm

    Passo 1: Calcular disciplinas liberadas
    Passo 2: Para cada liberada, calcular score ponderado
    Passo 3: Ordenar por score decrescente
    Passo 4: Selecionar até atingir limite de créditos
    """
    G_pre = _subgrafo_pre(G)
    livres = _liberadas(G, aprovadas)

    if not livres:
        return []

    # Calcular métricas brutas
    metricas = {}
    for disc in livres:
        imp = _impacto(G_pre, disc)
        prof = _profundidade(G_pre, disc)
        metricas[disc] = (imp, prof)

    # Normalizar (0-1)
    max_imp = max(m[0] for m in metricas.values()) or 1
    max_prof = max(m[1] for m in metricas.values()) or 1

    recs: list[Recomendacao] = []
    for disc in livres:
        imp, prof = metricas[disc]
        imp_norm = imp / max_imp
        prof_norm = prof / max_prof
        score = alfa * imp_norm + beta * prof_norm
        recs.append(Recomendacao(
            sigla=disc, score=score, creditos=_creditos(G, disc),
            impacto=imp, profundidade=prof,
            motivo=f"Score = {alfa}×{imp_norm:.2f} + {beta}×{prof_norm:.2f}",
        ))

    recs.sort(key=lambda r: r.score, reverse=True)
    return _selecionar_com_limite(G, recs, aprovadas, max_creditos)


# ─── Seleção com limite de créditos ──────────────────────────────────────

def _selecionar_com_limite(
    G: nx.DiGraph,
    recs: list[Recomendacao],
    aprovadas: set[str],
    max_creditos: int,
) -> list[Recomendacao]:
    """Seleciona disciplinas do ranking até atingir o limite de créditos.

    Inclui co-requisitos obrigatórios automaticamente.
    """
    selecionadas: list[Recomendacao] = []
    creditos_total = 0
    siglas_sel: set[str] = set()

    for rec in recs:
        if rec.sigla in siglas_sel:
            continue

        # Verificar co-requisitos que precisam ser incluídos
        cos = co_requisitos(G, rec.sigla)
        cos_pendentes = [
            c for c in cos
            if c not in aprovadas and c not in siglas_sel
        ]

        custo = rec.creditos + sum(_creditos(G, c) for c in cos_pendentes)

        if creditos_total + custo <= max_creditos:
            selecionadas.append(rec)
            siglas_sel.add(rec.sigla)
            creditos_total += rec.creditos

            # Adicionar co-requisitos
            for co in cos_pendentes:
                co_imp = _impacto(_subgrafo_pre(G), co)
                co_prof = _profundidade(_subgrafo_pre(G), co)
                selecionadas.append(Recomendacao(
                    sigla=co, score=rec.score * 0.9,
                    creditos=_creditos(G, co),
                    impacto=co_imp, profundidade=co_prof,
                    motivo=f"Co-requisito de {rec.sigla}",
                ))
                siglas_sel.add(co)
                creditos_total += _creditos(G, co)

    return selecionadas


# ─── Mapa de estratégias ────────────────────────────────────────────────

ESTRATEGIAS = {
    "A — Menor tempo até formatura": estrategia_menor_tempo,
    "B — Desbloquear mais disciplinas": estrategia_desbloquear,
    "C — Minimizar gargalos": estrategia_gargalos,
    "D — Balanceamento de carga": estrategia_balanceamento,
    "Ótima — Heurística ponderada": estrategia_otima,
}

DESCRICOES = {
    "A — Menor tempo até formatura": (
        "Minimiza o número de semestres restantes priorizando disciplinas "
        "no **caminho crítico** (maior profundidade no grafo). "
        "Ideal para quem quer se formar o mais rápido possível."
    ),
    "B — Desbloquear mais disciplinas": (
        "Maximiza o número de disciplinas **liberadas no próximo semestre**. "
        "Ideal para quem quer mais flexibilidade nas escolhas futuras."
    ),
    "C — Minimizar gargalos": (
        "Prioriza disciplinas que pertencem a **cadeias longas** de dependência. "
        "Ideal para evitar atrasos em cascata."
    ),
    "D — Balanceamento de carga": (
        "Preenche o semestre de forma **equilibrada**, priorizando disciplinas "
        "atrasadas (semestre mais baixo). Ideal para manter ritmo constante."
    ),
    "Ótima — Heurística ponderada": (
        "Combina impacto e profundidade com pesos ajustáveis "
        "(**score = α·impacto + β·profundidade**). "
        "O melhor dos dois mundos."
    ),
}
