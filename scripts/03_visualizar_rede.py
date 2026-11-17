from pathlib import Path

import matplotlib.pyplot as plt
import osmnx as ox


# ---------------------------------------------------------
# Caminhos
# ---------------------------------------------------------

PASTA_PROJETO = Path(__file__).resolve().parent.parent
PASTA_DADOS = PASTA_PROJETO / "dados"
PASTA_RESULTADOS = PASTA_PROJETO / "resultados"

CAMINHO_GRAFO = (
    PASTA_DADOS
    / "rede_osm_bruta.graphml"
)

CAMINHO_IMAGEM = (
    PASTA_RESULTADOS
    / "rede_osm_bruta.png"
)


# ---------------------------------------------------------
# Carregamento
# ---------------------------------------------------------

if not CAMINHO_GRAFO.exists():
    raise FileNotFoundError(
        f"O grafo não foi encontrado em: {CAMINHO_GRAFO}"
    )

PASTA_RESULTADOS.mkdir(
    parents=True,
    exist_ok=True
)

print("Carregando a rede viária bruta...")

grafo = ox.io.load_graphml(
    CAMINHO_GRAFO
)

print("Rede carregada com sucesso!")

print(
    f"Quantidade de vértices: "
    f"{grafo.number_of_nodes()}"
)

print(
    f"Quantidade de arestas direcionadas: "
    f"{grafo.number_of_edges()}"
)


# ---------------------------------------------------------
# Visualização
# ---------------------------------------------------------

print("Gerando a imagem...")

fig, ax = ox.plot_graph(
    grafo,
    node_size=18,
    node_color="#D32F2F",
    edge_color="#37474F",
    edge_linewidth=1.2,
    bgcolor="white",
    show=False,
    close=False
)

ax.set_title(
    "Rede viária bruta da área de estudo",
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