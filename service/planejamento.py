import networkx as nx


def classificar(G, aprovadas):
    """Classifica cada disciplina: aprovada, liberada ou bloqueada."""
    status = {}
    for node in G.nodes():
        pre = [u for u, v, d in G.in_edges(node, data=True) if d["tipo"] == "pre"]

        if node in aprovadas:
            status[node] = "aprovada"
        elif all(p in aprovadas for p in pre):
            status[node] = "liberada"
        else:
            status[node] = "bloqueada"

    return status


def dependencias(G, disciplina):
    """Retorna pré-requisitos (cadeia completa) e dependentes (cadeia completa).

    Filtra apenas arestas do tipo 'pre' para construir as cadeias.
    """
    # Subgrafo apenas com arestas de pré-requisito
    pre_edges = [(u, v) for u, v, d in G.edges(data=True) if d["tipo"] == "pre"]
    G_pre = nx.DiGraph(pre_edges)

    pre = []
    pos = []

    if disciplina in G_pre:
        pre = list(nx.ancestors(G_pre, disciplina))
        pos = list(nx.descendants(G_pre, disciplina))

    return pre, pos


def pre_requisitos_diretos(G, disciplina):
    """Retorna apenas os pré-requisitos diretos (não a cadeia toda)."""
    return [u for u, _, d in G.in_edges(disciplina, data=True) if d["tipo"] == "pre"]


def dependentes_diretos(G, disciplina):
    """Retorna apenas os dependentes diretos (não a cadeia toda)."""
    return [v for _, v, d in G.out_edges(disciplina, data=True) if d["tipo"] == "pre"]


def co_requisitos(G, disciplina):
    """Retorna co-requisitos de uma disciplina (unidirecional: quem ela declara)."""
    co = set()
    for _, v, d in G.out_edges(disciplina, data=True):
        if d["tipo"] == "co":
            co.add(v)
    return list(co)
