from pathlib import Path
from collections import defaultdict
import ast

import matplotlib.pyplot as plt
import networkx as nx
import osmnx as ox


# ---------------------------------------------------------
# Configurações
# ---------------------------------------------------------

NOME_AVENIDA = "Avenida Coronel Araújo Lima"
TOLERANCIA_METROS = 5.0

PASTA_PROJETO = Path(__file__).resolve().parent.parent
PASTA_RESULTADOS = PASTA_PROJETO / "resultados"

CAMINHO_REDE_TOPOLOGICA = (
    PASTA_RESULTADOS
    / "rede_osm_topologica.graphml"
)

CAMINHO_REDE_AJUSTADA = (
    PASTA_RESULTADOS
    / "rede_osm_ajustada.graphml"
)

CAMINHO_IMAGEM = (
    PASTA_RESULTADOS
    / "rede_osm_ajustada.png"
)


# ---------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------

def transformar_em_lista(valor):
    if isinstance(valor, list):
        return valor

    if valor is None:
        return []

    if isinstance(valor, str) and valor.startswith("["):
        try:
            resultado = ast.literal_eval(valor)

            if isinstance(resultado, list):
                return resultado

        except (ValueError, SyntaxError):
            pass

    return [valor]


def pertence_araujo_lima(dados_aresta):
    nomes = transformar_em_lista(
        dados_aresta.get("name")
    )

    return NOME_AVENIDA in nomes


def encontrar_vertices_araujo(grafo):
    vertices = set()

    for origem, destino, chave, dados in grafo.edges(
        keys=True,
        data=True
    ):
        if pertence_araujo_lima(dados):
            vertices.add(origem)
            vertices.add(destino)

    return vertices


# ---------------------------------------------------------
# Carregamento
# ---------------------------------------------------------

if not CAMINHO_REDE_TOPOLOGICA.exists():
    raise FileNotFoundError(
        "A rede topológica não foi encontrada em: "
        f"{CAMINHO_REDE_TOPOLOGICA}"
    )


print("Carregando a rede topológica...")

grafo = ox.io.load_graphml(
    CAMINHO_REDE_TOPOLOGICA
)

print(f"Vértices antes do ajuste: {grafo.number_of_nodes()}")
print(
    f"Arestas direcionadas antes do ajuste: "
    f"{grafo.number_of_edges()}"
)


# ---------------------------------------------------------
# Projeção para coordenadas em metros
# ---------------------------------------------------------

print("\nProjetando a rede para coordenadas métricas...")

grafo_projetado = ox.projection.project_graph(
    grafo
)

vertices_araujo = encontrar_vertices_araujo(
    grafo_projetado
)

print(
    "Vértices associados à Coronel Araújo Lima: "
    f"{len(vertices_araujo)}"
)


# Somente os vértices da Coronel Araújo Lima recebem
# tolerância de consolidação.
tolerancias = {
    vertice: TOLERANCIA_METROS
    for vertice in vertices_araujo
}


# ---------------------------------------------------------
# Consolidação seletiva
# ---------------------------------------------------------

print("\nConsolidando somente a Coronel Araújo Lima...")

grafo_consolidado = (
    ox.simplification.consolidate_intersections(
        grafo_projetado,
        tolerance=tolerancias,
        rebuild_graph=True,
        max_length=15,
        dead_ends=True,
        reconnect_edges=True
    )
)


# Retorno para latitude e longitude
grafo_consolidado = ox.projection.project_graph(
    grafo_consolidado,
    to_latlong=True
)


# ---------------------------------------------------------
# Conversão para grafo não direcionado
# ---------------------------------------------------------

grafo_nao_direcionado = ox.convert.to_undirected(
    grafo_consolidado
)


# Remove laços criados pela união dos dois lados da avenida.
lacos = list(
    nx.selfloop_edges(
        grafo_nao_direcionado,
        keys=True
    )
)

grafo_nao_direcionado.remove_edges_from(
    lacos
)


# ---------------------------------------------------------
# União das duas linhas da Coronel Araújo Lima
# ---------------------------------------------------------

arestas_araujo_por_par = defaultdict(list)

for origem, destino, chave, dados in (
    grafo_nao_direcionado.edges(
        keys=True,
        data=True
    )
):
    if pertence_araujo_lima(dados):
        par = frozenset({
            origem,
            destino
        })

        arestas_araujo_por_par[par].append(
            (origem, destino, chave)
        )


arestas_paralelas_removidas = 0

for arestas in arestas_araujo_por_par.values():
    origem, destino, chave = arestas[0]

    # Remove a geometria lateral da pista mantida.
    # A linha será desenhada entre os vértices consolidados.
    grafo_nao_direcionado.edges[
        origem,
        destino,
        chave
    ].pop("geometry", None)

    grafo_nao_direcionado.edges[
        origem,
        destino,
        chave
    ]["oneway"] = False

    for aresta_excedente in arestas[1:]:
        grafo_nao_direcionado.remove_edge(
            *aresta_excedente
        )

        arestas_paralelas_removidas += 1

# ---------------------------------------------------------
# Remoção dos vértices intermediários da avenida
# ---------------------------------------------------------

vertices_intermediarios_removidos = 0

while True:
    vertice_encontrado = None

    for vertice in list(
        grafo_nao_direcionado.nodes()
    ):
        # Um vértice intermediário possui exatamente
        # duas arestas incidentes.
        if grafo_nao_direcionado.degree(vertice) != 2:
            continue

        arestas_incidentes = list(
            grafo_nao_direcionado.edges(
                vertice,
                keys=True,
                data=True
            )
        )

        if len(arestas_incidentes) != 2:
            continue

        # As duas arestas precisam pertencer
        # à Avenida Coronel Araújo Lima.
        if not all(
            pertence_araujo_lima(dados)
            for _, _, _, dados
            in arestas_incidentes
        ):
            continue

        vizinhos = []

        for origem, destino, chave, dados in (
            arestas_incidentes
        ):
            if origem == vertice:
                vizinhos.append(destino)
            else:
                vizinhos.append(origem)

        # Evita criar uma ligação do vértice
        # para ele mesmo.
        if vizinhos[0] == vizinhos[1]:
            continue

        vertice_encontrado = (
            vertice,
            vizinhos,
            arestas_incidentes
        )

        break

    # Para quando não existir mais nenhum
    # vértice intermediário na avenida.
    if vertice_encontrado is None:
        break

    vertice, vizinhos, arestas_incidentes = (
        vertice_encontrado
    )

    comprimento_total = sum(
        float(dados.get("length", 0))
        for _, _, _, dados
        in arestas_incidentes
    )

    primeiro_vizinho = vizinhos[0]
    segundo_vizinho = vizinhos[1]

    # Remove o vértice intermediário e
    # suas duas arestas.
    grafo_nao_direcionado.remove_node(
        vertice
    )

    # Cria uma única aresta entre os
    # vértices vizinhos.
    grafo_nao_direcionado.add_edge(
        primeiro_vizinho,
        segundo_vizinho,
        name=NOME_AVENIDA,
        highway="residential",
        oneway=False,
        length=comprimento_total
    )

    vertices_intermediarios_removidos += 1


print(
    "Vértices intermediários removidos da avenida: "
    f"{vertices_intermediarios_removidos}"
)

vertices_araujo_depois = encontrar_vertices_araujo(
    grafo_nao_direcionado
)


print("\nConsolidação concluída!")

print(
    "Vértices da Coronel Araújo Lima após o ajuste: "
    f"{len(vertices_araujo_depois)}"
)

print(
    "Arestas paralelas removidas da avenida: "
    f"{arestas_paralelas_removidas}"
)

print(
    f"Vértices totais da rede ajustada: "
    f"{grafo_nao_direcionado.number_of_nodes()}"
)

print(
    f"Arestas não direcionadas da rede ajustada: "
    f"{grafo_nao_direcionado.number_of_edges()}"
)


# ---------------------------------------------------------
# Salvamento
# ---------------------------------------------------------

ox.io.save_graphml(
    grafo_nao_direcionado,
    filepath=CAMINHO_REDE_AJUSTADA
)

print(
    f"\nRede ajustada salva em: "
    f"{CAMINHO_REDE_AJUSTADA}"
)


# ---------------------------------------------------------
# Visualização
# ---------------------------------------------------------

print("Gerando a imagem da rede ajustada...")

fig, ax = ox.plot_graph(
    grafo_nao_direcionado,
    node_size=28,
    node_color="#D32F2F",
    edge_color="#37474F",
    edge_linewidth=1.2,
    bgcolor="white",
    show=False,
    close=False
)

ax.set_title(
    "Rede viária após a consolidação da "
    "Avenida Coronel Araújo Lima",
    fontsize=14,
    pad=15
)

fig.savefig(
    CAMINHO_IMAGEM,
    dpi=300,
    bbox_inches="tight",
    facecolor="white"
)

plt.close(fig)

print(
    f"Imagem salva em: "
    f"{CAMINHO_IMAGEM}"
)
