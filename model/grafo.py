import copy

import networkx as nx


def aplicar_optativas(curriculo_base, optativas, selecoes):
    """Aplica seleções de optativas ao currículo base.

    Substitui os pré/co-requisitos dos slots OP1–OP4 pelos da optativa
    selecionada.  Quando uma optativa depende de outra que também foi
    selecionada em outro slot, a referência é redirecionada ao slot.

    Parâmetros
    ----------
    curriculo_base : dict   – semestres 1-10 (sem chave "optativas").
    optativas      : dict   – catálogo de optativas.
    selecoes       : dict   – {"OP1": "PSC", "OP2": None, ...}.

    Retorna cópia do currículo com as substituições aplicadas.
    """
    curriculo = copy.deepcopy(curriculo_base)

    # Mapa inverso: código da optativa → slot que a selecionou
    opt_para_slot = {v: k for k, v in selecoes.items() if v}

    for slot, opt_code in selecoes.items():
        if not opt_code or opt_code not in optativas:
            continue
        opt = optativas[opt_code]

        # Remapeia pré-requisitos de optativas cruzadas
        new_pre = []
        for pre in opt.get("pre", []):
            if pre in opt_para_slot and opt_para_slot[pre] != slot:
                new_pre.append(opt_para_slot[pre])
            else:
                new_pre.append(pre)

        for sem, discs in curriculo.items():
            if slot in discs:
                discs[slot]["pre"] = new_pre
                discs[slot]["co"] = opt.get("co", [])
                discs[slot]["creditos"] = opt.get("creditos", 2)
                break

    return curriculo


def construir_grafo(curriculo):
    """Constrói um grafo dirigido a partir da matriz curricular.

    Nós: disciplinas com atributo 'semestre'.
    Arestas: pré-requisito (pre→disciplina) e co-requisito (disc→co, unidirecional).
    """
    G = nx.DiGraph()

    for semestre, disciplinas in curriculo.items():
        for nome, deps in disciplinas.items():
            G.add_node(
                nome,
                semestre=int(semestre),
                semestre_fim=deps.get("semestre_fim"),
                creditos=deps.get("creditos", 4),
            )

            for pre in deps.get("pre", []):
                if pre:  # ignora strings vazias residuais
                    G.add_edge(pre, nome, tipo="pre")

            for co in deps.get("co", []):
                if co:
                    G.add_edge(nome, co, tipo="co")

    return G


def obter_info_disciplina(G, disciplina):
    """Retorna dicionário com informações completas de uma disciplina."""
    pre_diretos = [
        u for u, _, d in G.in_edges(disciplina, data=True) if d["tipo"] == "pre"
    ]
    co_requisitos = [
        v for _, v, d in G.out_edges(disciplina, data=True) if d["tipo"] == "co"
    ]
    return {
        "semestre": G.nodes[disciplina]["semestre"],
        "semestre_fim": G.nodes[disciplina].get("semestre_fim"),
        "pre_diretos": pre_diretos,
        "co_requisitos": list(set(co_requisitos)),
    }
