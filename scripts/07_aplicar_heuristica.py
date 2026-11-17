from pathlib import Path
from time import perf_counter
import csv

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx
import osmnx as ox

from algoritmos_cobertura import (
    cobertura_valida,
    heuristica_gulosa_por_grau,
)

from utilitarios_vertices import (
    criar_mapeamento_vertices
)


PASTA_PROJETO = (
    Path(__file__).resolve().parent.parent
)

PASTA_RESULTADOS = (
    PASTA_PROJETO / "resultados"
)

CAMINHO_REDE = (
    PASTA_RESULTADOS
    / "rede_osm_ajustada.graphml"
)

CAMINHO_RELATORIO = (
    PASTA_RESULTADOS
    / "resultado_heuristica.txt"
)

CAMINHO_CSV = (
    PASTA_RESULTADOS
    / "resultado_heuristica.csv"
)

CAMINHO_IMAGEM = (
    PASTA_RESULTADOS
    / "heuristica_cobertura_vertices.png"
)


if not CAMINHO_REDE.exists():
    raise FileNotFoundError(
        f"A rede não foi encontrada em: "
        f"{CAMINHO_REDE}"
    )


print("Carregando a rede final validada...")

grafo_original = ox.io.load_graphml(
    CAMINHO_REDE
)

grafo = nx.Graph(
    grafo_original
)

quantidade_vertices = (
    grafo.number_of_nodes()
)

quantidade_arestas = (
    grafo.number_of_edges()
)

print(
    f"Quantidade de vértices: "
    f"{quantidade_vertices}"
)

print(
    f"Quantidade de arestas: "
    f"{quantidade_arestas}"
)


rotulos_por_vertice, _ = (
    criar_mapeamento_vertices(grafo)
)


print(
    "\nExecutando a heurística "
    "gulosa por grau..."
)

inicio = perf_counter()

vertices_selecionados, historico = (
    heuristica_gulosa_por_grau(
        grafo,
        rotulos_por_vertice
    )
)

tempo_execucao = (
    perf_counter() - inicio
)


if not cobertura_valida(
    grafo,
    vertices_selecionados
):
    raise RuntimeError(
        "A heurística produziu uma "
        "cobertura inválida."
    )


conjunto_selecionado = set(
    vertices_selecionados
)

arestas_nao_cobertas = [
    (origem, destino)
    for origem, destino in grafo.edges()
    if (
        origem not in conjunto_selecionado
        and destino not in conjunto_selecionado
    )
]

quantidade_selecionados = len(
    vertices_selecionados
)

quantidade_nao_cobertas = len(
    arestas_nao_cobertas
)

quantidade_cobertas = (
    quantidade_arestas
    - quantidade_nao_cobertas
)

percentual_cobertura = (
    quantidade_cobertas
    / quantidade_arestas
    * 100
)

rotulos_ordem = [
    rotulos_por_vertice[vertice]
    for vertice in vertices_selecionados
]

rotulos_ordenados = sorted(
    rotulos_ordem,
    key=lambda rotulo: int(
        rotulo.removeprefix("V")
    )
)


linhas = [
    "RESULTADO DA HEURÍSTICA GULOSA",
    "",
    (
        "Quantidade de vértices do grafo: "
        f"{quantidade_vertices}"
    ),
    (
        "Quantidade de arestas do grafo: "
        f"{quantidade_arestas}"
    ),
    (
        "Quantidade de vértices selecionados: "
        f"{quantidade_selecionados}"
    ),
    (
        "Vértices selecionados: "
        + ", ".join(rotulos_ordenados)
    ),
    (
        "Ordem de seleção: "
        + ", ".join(rotulos_ordem)
    ),
    (
        "Arestas cobertas: "
        f"{quantidade_cobertas}"
    ),
    (
        "Arestas não cobertas: "
        f"{quantidade_nao_cobertas}"
    ),
    (
        "Percentual de cobertura: "
        f"{percentual_cobertura:.2f}%"
    ),
    (
        "Cobertura completa: "
        f"{quantidade_nao_cobertas == 0}"
    ),
    (
        "Tempo de execução: "
        f"{tempo_execucao:.8f} segundos"
    ),
]

relatorio = "\n".join(
    linhas
)


print("\nHeurística concluída!")

print(
    f"Quantidade de vértices selecionados: "
    f"{quantidade_selecionados}"
)

print(
    "Vértices selecionados: "
    + ", ".join(rotulos_ordenados)
)

print(
    "Ordem de seleção: "
    + ", ".join(rotulos_ordem)
)

print(
    f"Arestas cobertas: "
    f"{quantidade_cobertas}"
)

print(
    f"Arestas não cobertas: "
    f"{quantidade_nao_cobertas}"
)

print(
    f"Percentual de cobertura: "
    f"{percentual_cobertura:.2f}%"
)

print(
    f"Cobertura completa: "
    f"{quantidade_nao_cobertas == 0}"
)

print(
    f"Tempo de execução: "
    f"{tempo_execucao:.8f} segundos"
)


PASTA_RESULTADOS.mkdir(
    parents=True,
    exist_ok=True
)

CAMINHO_RELATORIO.write_text(
    relatorio,
    encoding="utf-8"
)

print(
    f"\nRelatório salvo em: "
    f"{CAMINHO_RELATORIO}"
)


with CAMINHO_CSV.open(
    "w",
    newline="",
    encoding="utf-8-sig"
) as arquivo:
    campos = [
        "iteracao",
        "vertice",
        "identificador_interno",
        "grau_residual",
        "arestas_cobertas",
        "arestas_restantes",
    ]

    escritor = csv.DictWriter(
        arquivo,
        fieldnames=campos
    )

    escritor.writeheader()
    escritor.writerows(historico)


print(
    f"Histórico em CSV salvo em: "
    f"{CAMINHO_CSV}"
)


print("Gerando a imagem da cobertura...")

cores = [
    (
        "#D32F2F"
        if vertice in conjunto_selecionado
        else "#B0BEC5"
    )
    for vertice in grafo_original.nodes()
]

tamanhos = [
    (
        58
        if vertice in conjunto_selecionado
        else 42
    )
    for vertice in grafo_original.nodes()
]

fig, ax = ox.plot_graph(
    grafo_original,
    node_size=tamanhos,
    node_color=cores,
    edge_color="#455A64",
    edge_linewidth=1.3,
    bgcolor="white",
    show=False,
    close=False,
)


for vertice in grafo.nodes():
    selecionado = (
        vertice in conjunto_selecionado
    )

    ax.annotate(
        rotulos_por_vertice[vertice],
        xy=(
            float(
                grafo.nodes[vertice]["x"]
            ),
            float(
                grafo.nodes[vertice]["y"]
            ),
        ),
        xytext=(5, 5),
        textcoords="offset points",
        fontsize=7,
        fontweight=(
            "bold"
            if selecionado
            else "normal"
        ),
        color="#111111",
        bbox={
            "boxstyle": "round,pad=0.15",
            "facecolor": "white",
            "edgecolor": (
                "#D32F2F"
                if selecionado
                else "#90A4AE"
            ),
            "linewidth": 0.8,
            "alpha": 0.95,
        },
    )


legenda = [
    Line2D(
        [0],
        [0],
        marker="o",
        color="none",
        markerfacecolor="#D32F2F",
        markeredgecolor="#D32F2F",
        markersize=8,
        label="Vértice selecionado",
    ),
    Line2D(
        [0],
        [0],
        marker="o",
        color="none",
        markerfacecolor="#B0BEC5",
        markeredgecolor="#B0BEC5",
        markersize=8,
        label="Vértice não selecionado",
    ),
]

ax.legend(
    handles=legenda,
    loc="upper right",
    frameon=True,
    fontsize=8
)

ax.set_title(
    "Cobertura de vértices obtida "
    "pela heurística gulosa",
    fontsize=12,
    pad=15,
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