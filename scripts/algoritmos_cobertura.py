import networkx as nx
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_array


def chave_identificador(vertice):
    """Ordena os identificadores internos numericamente."""
    return int(vertice)


def normalizar_aresta(origem, destino):
    """Cria uma representação única para uma aresta não direcionada."""
    return tuple(
        sorted(
            (origem, destino),
            key=chave_identificador
        )
    )


def heuristica_gulosa_por_grau(
    grafo,
    rotulos_por_vertice=None
):
    """
    Seleciona, em cada iteração, o vértice incidente à maior
    quantidade de arestas ainda não cobertas.

    Em caso de empate, seleciona o menor identificador interno.
    A função não recebe nem consulta resultados de outros métodos.
    """

    if rotulos_por_vertice is None:
        rotulos_por_vertice = {
            vertice: str(vertice)
            for vertice in grafo.nodes()
        }

    arestas_nao_cobertas = {
        normalizar_aresta(origem, destino)
        for origem, destino in grafo.edges()
    }

    arestas_incidentes = {
        vertice: set()
        for vertice in grafo.nodes()
    }

    for aresta in arestas_nao_cobertas:
        origem, destino = aresta
        arestas_incidentes[origem].add(aresta)
        arestas_incidentes[destino].add(aresta)

    graus_residuais = {
        vertice: len(arestas)
        for vertice, arestas in arestas_incidentes.items()
    }

    vertices_selecionados = []
    historico = []
    iteracao = 1

    while arestas_nao_cobertas:
        maior_grau = max(
            graus_residuais.values()
        )

        candidatos = [
            vertice
            for vertice in grafo.nodes()
            if graus_residuais[vertice] == maior_grau
        ]

        escolhido = min(
            candidatos,
            key=chave_identificador
        )

        cobertas_agora = (
            arestas_incidentes[escolhido]
            & arestas_nao_cobertas
        )

        for aresta in cobertas_agora:
            arestas_nao_cobertas.remove(aresta)

            origem, destino = aresta
            graus_residuais[origem] -= 1
            graus_residuais[destino] -= 1

        vertices_selecionados.append(
            escolhido
        )

        historico.append({
            "iteracao": iteracao,
            "vertice": rotulos_por_vertice[escolhido],
            "identificador_interno": escolhido,
            "grau_residual": maior_grau,
            "arestas_cobertas": len(cobertas_agora),
            "arestas_restantes": len(
                arestas_nao_cobertas
            ),
        })

        iteracao += 1

    return vertices_selecionados, historico


def aproximacao_networkx(grafo):
    """
    Executa a aproximação oficial de cobertura
    de vértices do NetworkX.
    """

    return set(
        nx.algorithms.approximation
        .min_weighted_vertex_cover(
            grafo,
            weight=None
        )
    )


def solucao_exata_milp(
    grafo,
    limite_segundos=None
):
    """
    Resolve a Cobertura Mínima de Vértices
    com SciPy/HiGHS.
    """

    vertices = sorted(
        grafo.nodes(),
        key=chave_identificador
    )

    indice = {
        vertice: i
        for i, vertice in enumerate(vertices)
    }

    arestas = list(
        grafo.edges()
    )

    linhas = []
    colunas = []
    valores = []

    for i, (origem, destino) in enumerate(arestas):
        linhas.extend((i, i))

        colunas.extend((
            indice[origem],
            indice[destino]
        ))

        valores.extend((1.0, 1.0))

    matriz = coo_array(
        (
            valores,
            (linhas, colunas)
        ),
        shape=(
            len(arestas),
            len(vertices)
        ),
    ).tocsc()

    restricoes = LinearConstraint(
        matriz,
        lb=np.ones(len(arestas)),
        ub=np.full(
            len(arestas),
            np.inf
        ),
    )

    opcoes = {
        "presolve": True,
        "mip_rel_gap": 0.0,
        "disp": False,
    }

    if limite_segundos is not None:
        opcoes["time_limit"] = float(
            limite_segundos
        )

    resultado = milp(
        c=np.ones(len(vertices)),
        integrality=np.ones(
            len(vertices),
            dtype=int
        ),
        bounds=Bounds(
            lb=np.zeros(len(vertices)),
            ub=np.ones(len(vertices)),
        ),
        constraints=restricoes,
        options=opcoes,
    )

    metadados = {
        "status": int(resultado.status),
        "mensagem": str(resultado.message),
        "mip_gap": getattr(
            resultado,
            "mip_gap",
            None
        ),
    }

    if (
        not resultado.success
        or resultado.status != 0
    ):
        return None, metadados

    solucao = {
        vertice
        for vertice, valor in zip(
            vertices,
            resultado.x
        )
        if valor >= 0.5
    }

    metadados["valor_objetivo"] = float(
        resultado.fun
    )

    return solucao, metadados


def cobertura_valida(grafo, solucao):
    """
    Verifica se toda aresta possui pelo menos
    uma extremidade selecionada.
    """

    if solucao is None:
        return False

    conjunto = set(solucao)

    return all(
        origem in conjunto
        or destino in conjunto
        for origem, destino in grafo.edges()
    )