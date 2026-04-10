"""
Fonte centralizada dos nomes das disciplinas do currículo de Engenharia Elétrica.

Todas as páginas do projeto devem importar daqui em vez de manter dicts locais.

Uso (páginas do app principal — CWD = raiz do projeto):
    from data.disciplinas import NOMES, NOMES_ABREVIADOS, SIGAA_EXTRA, cod_nome

Uso (ConselhoApp — CWD = ConselhoApp/):
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from data.disciplinas import NOMES, NOMES_ABREVIADOS, SIGAA_EXTRA, cod_nome
"""

# ── Nomes completos das disciplinas ──────────────────────────────────────
NOMES: dict[str, str] = {
    # Semestre 1-10 (spanning)
    "ATC": "Atividades Complementares",
    # Semestre 1
    "AE1": "Atividade de Extensão I",
    "CA1": "Cálculo I",
    "COM": "Comunicação e Expressão",
    "GMT": "Geometria Analítica",
    "IEE": "Introdução à Engenharia Elétrica",
    "QMG": "Química Geral",
    # Semestre 2
    "ALG": "Álgebra Linear",
    "CA2": "Cálculo II",
    "CMT": "Ciência e Tecnologia dos Materiais",
    "ELB": "Eletricidade Básica",
    "ETP": "Estatística e Probabilidade",
    "FI1": "Física I — Mecânica",
    "MPQ": "Metodologia de Pesquisa",
    "PI1": "Projeto Integrador I — Iniciação Científica",
    # Semestre 3
    "CA3": "Cálculo III",
    "CE1": "Circuitos Elétricos I",
    "FEX": "Física Experimental",
    "FI3": "Física III — Eletricidade e Eletromagnetismo",
    "MEC": "Mecânica dos Sólidos",
    "PRG": "Programação de Computadores",
    "SEG": "Segurança em Eletricidade",
    # Semestre 4
    "CA4": "Cálculo IV",
    "CE2": "Circuitos Elétricos II",
    "DTE": "Desenho Técnico",
    "EMG": "Eletromagnetismo",
    "FEN": "Fenômenos de Transporte",
    "FI2": "Física II — Termodinâmica e Ondas",
    # Semestre 5
    "AE2": "Atividade de Extensão II",
    "CAN": "Cálculo Numérico",
    "CE3": "Circuitos Elétricos III",
    "CO1": "Conversão Eletromecânica de Energia I",
    "EL1": "Eletrônica I",
    "ESC": "Engenharia, Sociedade e Cidadania",
    # Semestre 6
    "ASL": "Análise de Sistemas Lineares",
    "CO2": "Conversão Eletromecânica de Energia II",
    "ELD": "Eletrônica Digital",
    "EL2": "Eletrônica II",
    "QEE": "Qualidade e Eficiência Energética",
    # Semestre 7
    "ACI": "Acionamentos Industriais",
    "CTC": "Sistemas de Controle I",
    "EP1": "Eletrônica de Potência I",
    "IST": "Instrumentação Eletrônica",
    "MIC": "Microcontroladores",
    "PEP": "Projetos Elétricos Prediais",
    # Semestre 8
    "AUI": "Automação Industrial",
    "EP2": "Eletrônica de Potência II",
    "PEI": "Projetos Elétricos Industriais",
    "PI2": "Projeto Integrador II — Instrumentação Eletrônica",
    "SEE": "Sistemas de Energia Elétrica",
    # Semestre 9
    "AE3": "Atividade de Extensão III",
    "ADM": "Administração para Engenharia",
    "ENS": "Engenharia e Sustentabilidade",
    "SGT": "Sistemas de Transmissão e Distribuição",
    "TC1": "Trabalho de Conclusão de Curso I",
    "OP1": "Optativa I",
    "OP2": "Optativa II",
    # Semestre 9-10 (spanning)
    "EST": "Estágio Curricular Supervisionado",
    # Semestre 10
    "ECO": "Economia para Engenharia",
    "IND": "Manutenção Industrial",
    "TC2": "Trabalho de Conclusão de Curso II",
    "OP3": "Optativa III",
    "OP4": "Optativa IV",
    # Optativas
    "ATE": "Aterramento Elétrico",
    "CDI": "Controle Digital",
    "CEM": "Compatibilidade Eletromagnética",
    "CME": "Controle de Máquinas Elétricas",
    "CTM": "Controle Moderno",
    "DLP": "Dispositivos de Lógica Programável",
    "EGP": "Empreendedorismo e Gerenciamento de Projetos",
    "ELA": "Eletrônica Analógica Avançada",
    "EPT": "Tópicos Especiais em Eletrônica de Potência",
    "ICO": "Introdução às Comunicações Ópticas",
    "IDW": "Introdução ao Desenvolvimento Web",
    "OTM": "Técnicas de Otimização",
    "PDS": "Processamento de Sinais",
    "POO": "Programação Orientada a Objetos",
    "PRD": "Programação para Dispositivos Móveis",
    "PSC": "Princípios de Sistemas de Comunicação",
    "PSE": "Proteção de Sistemas Elétricos",
    "REC": "Recursos Energéticos Distribuídos",
    "RED": "Redes de Comunicação",
}

# ── Nomes abreviados (para cards compactos da matriz curricular) ─────────
NOMES_ABREVIADOS: dict[str, str] = {
    "ATC": "Atividades Complementares",
    "AE1": "Ativ. de Extensão I",
    "CA1": "Cálculo I",
    "COM": "Comunicação e Expressão",
    "GMT": "Geometria Analítica",
    "IEE": "Intro. à Eng. Elétrica",
    "QMG": "Química Geral",
    "ALG": "Álgebra Linear",
    "CA2": "Cálculo II",
    "CMT": "Ciência dos Materiais",
    "ELB": "Eletricidade Básica",
    "ETP": "Estatística e Probab.",
    "FI1": "Física I",
    "MPQ": "Metodologia de Pesquisa",
    "PI1": "Projeto Integrador I",
    "CA3": "Cálculo III",
    "CE1": "Circuitos Elétricos I",
    "FEX": "Física Experimental",
    "FI3": "Física III",
    "MEC": "Mecânica dos Sólidos",
    "PRG": "Programação",
    "SEG": "Segurança em Eletric.",
    "CA4": "Cálculo IV",
    "CE2": "Circuitos Elétricos II",
    "DTE": "Desenho Técnico",
    "EMG": "Eletromagnetismo",
    "FEN": "Fenômenos de Transporte",
    "FI2": "Física II",
    "AE2": "Ativ. de Extensão II",
    "CAN": "Cálculo Numérico",
    "CE3": "Circuitos Elétricos III",
    "CO1": "Conversão de Energia I",
    "EL1": "Eletrônica I",
    "ESC": "Eng., Sociedade e Cid.",
    "ASL": "Análise Sist. Lineares",
    "CO2": "Conversão de Energia II",
    "ELD": "Eletrônica Digital",
    "EL2": "Eletrônica II",
    "QEE": "Qualid. e Efic. Energ.",
    "ACI": "Acionamentos Industriais",
    "CTC": "Sistemas de Controle I",
    "EP1": "Eletrônica de Potência I",
    "IST": "Instrumentação Eletr.",
    "MIC": "Microcontroladores",
    "PEP": "Proj. Elétricos Prediais",
    "AUI": "Automação Industrial",
    "EP2": "Eletrônica de Potência II",
    "PEI": "Proj. Elétricos Indust.",
    "PI2": "Projeto Integrador II",
    "SEE": "Sistemas de Energia",
    "AE3": "Ativ. de Extensão III",
    "ADM": "Administração p/ Eng.",
    "ENS": "Eng. e Sustentabilidade",
    "SGT": "Sist. Transm. e Distrib.",
    "TC1": "TCC I",
    "OP1": "Optativa I",
    "OP2": "Optativa II",
    "EST": "Estágio Curricular",
    "ECO": "Economia p/ Engenharia",
    "IND": "Manutenção Industrial",
    "TC2": "TCC II",
    "OP3": "Optativa III",
    "OP4": "Optativa IV",
}

# ── Mapeamento de códigos SIGAA alternativos → código curricular ─────────
SIGAA_EXTRA: dict[str, str] = {
    "ACX": "ACI", "AUX": "AUI", "CAL": "CA4",
    "COX": "CO2", "EXX": "EST", "FIS": "FI3",
    "MPE": "MPQ", "MSO": "MEC", "PEX": "PEI",
    "PIX": "PI2", "SIX": "CTC", "STX": "SGT",
    "TCX": "TC2", "COE": "COM", "CDG": "CDI",
}


# ── Funções auxiliares ───────────────────────────────────────────────────

def sigla_curriculo(sigla_sigaa: str) -> str:
    """Converte uma sigla SIGAA (3 primeiros caracteres) para o código curricular."""
    c3 = str(sigla_sigaa).strip()[:3].upper()
    return SIGAA_EXTRA.get(c3, c3)


def cod_nome(codigo: str) -> str:
    """Retorna 'COD - Nome Completo' para exibição padronizada."""
    return f"{codigo} - {NOMES.get(codigo, codigo)}"


def cod_nome_abreviado(codigo: str) -> str:
    """Retorna 'COD - Nome Abreviado' (para cards compactos)."""
    return f"{codigo} - {NOMES_ABREVIADOS.get(codigo, NOMES.get(codigo, codigo))}"


def nome_para_codigo(nome_disciplina: str) -> str:
    """Busca o código curricular a partir do nome completo (case-insensitive)."""
    nome_lower = nome_disciplina.strip().lower()
    for cod, nome in NOMES.items():
        if nome.lower() == nome_lower:
            return cod
    return ""
