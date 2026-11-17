from pathlib import Path
import csv

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx
import osmnx as ox

from utilitarios_vertices import criar_mapeamento_vertices


# ---------------------------------------------------------
# Caminhos dos arquivos
# ---------------------------------------------------------

PASTA_PROJETO = Path(__file__).resolve().parent.parent
PASTA_RESULTADOS = PASTA_PROJETO / "resultados"

CAMINHO_REDE = (
    PASTA_RESULTADOS
    / "rede_osm_ajustada.graphml"
)

CAMINHO_RESULTADO_HEURISTICA = (
    PASTA_RESULTADOS
    / "resultado_heuristica.csv"
)

CAMINHO_NUMERACAO = (
    PASTA_RESULTADOS
    / "numeracao_vertices.csv"
)

CAMINHO_IMAGEM = (
    PASTA_RESULTADOS
    / "mapa_vertices_numerados.png"
)


# ---------------------------------------------------------
# Ajustes visuais dos rótulos
# ---------------------------------------------------------

DESLOCAMENTOS_ROTULOS = {
    "V04": (-2, 9),
    "V05": (7, -8),
    "V16": (6, 8),
    "V17": (-18, -11),
    "V23": (18, 7),
    "V24": (-28, 8),
    "V25": (5, -13)
}


# ---------------------------------------------------------
# Carregamento do grafo
# ---------------------------------------------------------

if not CAMINHO_REDE.exists():
    raise FileNotFoundError(
        f"A rede não foi encontrada em: {CAMINHO_REDE}"
    )

if not CAMINHO_RESULTADO_HEURISTICA.exists():
    raise FileNotFoundError(
        "O resultado da heurística não foi encontrado. "
        "Execute primeiro:\n"
        "python scripts\\07_aplicar_heuristica.py"
    )


print("Carregando a rede final validada...")

grafo_original = ox.io.load_graphml(
    CAMINHO_REDE
)

grafo = nx.Graph(
    grafo_original
)

quantidade_vertices = grafo.number_of_nodes()
quantidade_arestas = grafo.number_of_edges()

print(
    f"Quantidade de vértices: "
    f"{quantidade_vertices}"
)

print(
    f"Quantidade de arestas: "
    f"{quantidade_arestas}"
)


# ---------------------------------------------------------
# Numeração visual padronizada
# ---------------------------------------------------------

(
    rotulos_por_vertice,
    vertices_por_rotulo
) = criar_mapeamento_vertices(
    grafo
)

rotulos_por_identificador = {
    str(vertice): rotulo
    for vertice, rotulo
    in rotulos_por_vertice.items()
}


# ---------------------------------------------------------
# Leitura do resultado da heurística
# ---------------------------------------------------------

rotulos_selecionados = set()

colunas_candidatas = [
    "vertice_selecionado",
    "vertice_escolhido",
    "vertice",
    "rotulo"
]

with CAMINHO_RESULTADO_HEURISTICA.open(
    mode="r",
    encoding="utf-8-sig",
    newline=""
) as arquivo_csv:
    leitor = csv.DictReader(
        arquivo_csv
    )

    if leitor.fieldnames is None:
        raise ValueError(
            "O arquivo resultado_heuristica.csv "
            "não possui cabeçalho."
        )

    coluna_vertices = next(
        (
            coluna
            for coluna in colunas_candidatas
            if coluna in leitor.fieldnames
        ),
        None
    )

    if coluna_vertices is None:
        raise ValueError(
            "O arquivo resultado_heuristica.csv não possui "
            "uma coluna reconhecida para os vértices.\n"
            "Colunas encontradas: "
            + ", ".join(leitor.fieldnames)
        )

    for linha in leitor:
        valor = linha.get(
            coluna_vertices,
            ""
        ).strip()

        if not valor:
            continue

        if valor in vertices_por_rotulo:
            rotulo = valor

        elif valor in rotulos_por_identificador:
            rotulo = rotulos_por_identificador[
                valor
            ]

        else:
            raise ValueError(
                "O vértice informado no resultado da "
                f"heurística não pertence ao grafo: {valor}"
            )

        rotulos_selecionados.add(
            rotulo
        )


if not rotulos_selecionados:
    raise ValueError(
        "Nenhum vértice selecionado foi encontrado em "
        "resultado_heuristica.csv."
    )


rotulos_inexistentes = (
    rotulos_selecionados
    - set(vertices_por_rotulo)
)

if rotulos_inexistentes:
    raise ValueError(
        "Foram encontrados rótulos que não pertencem "
        "ao grafo atual: "
        + ", ".join(
            sorted(rotulos_inexistentes)
        )
    )


vertices_selecionados = {
    vertices_por_rotulo[rotulo]
    for rotulo in rotulos_selecionados
}

rotulos_selecionados_ordenados = sorted(
    rotulos_selecionados,
    key=lambda rotulo: int(
        rotulo.removeprefix("V")
    )
)

print(
    "Vértices selecionados pela heurística: "
    + ", ".join(
        rotulos_selecionados_ordenados
    )
)


# ---------------------------------------------------------
# Geração da tabela de numeração
# ---------------------------------------------------------

vertices_ordenados = sorted(
    grafo.nodes(),
    key=lambda vertice: int(
        rotulos_por_vertice[
            vertice
        ].removeprefix("V")
    )
)

with CAMINHO_NUMERACAO.open(
    mode="w",
    encoding="utf-8-sig",
    newline=""
) as arquivo_csv:
    campos = [
        "vertice",
        "identificador_interno",
        "selecionado",
        "grau",
        "longitude",
        "latitude"
    ]

    escritor = csv.DictWriter(
        arquivo_csv,
        fieldnames=campos
    )

    escritor.writeheader()

    for vertice in vertices_ordenados:
        rotulo = rotulos_por_vertice[
            vertice
        ]

        escritor.writerow({
            "vertice": rotulo,
            "identificador_interno": vertice,
            "selecionado": (
                "Sim"
                if vertice in vertices_selecionados
                else "Não"
            ),
            "grau": grafo.degree(vertice),
            "longitude": grafo.nodes[
                vertice
            ]["x"],
            "latitude": grafo.nodes[
                vertice
            ]["y"]
        })

print(
    f"Tabela de numeração salva em: "
    f"{CAMINHO_NUMERACAO}"
)


# ---------------------------------------------------------
# Geração da imagem
# ---------------------------------------------------------

print(
    "Gerando o mapa com todos os vértices numerados..."
)

cores_vertices = [
    "#D32F2F"
    if vertice in vertices_selecionados
    else "#B0BEC5"
    for vertice in grafo_original.nodes()
]

tamanhos_vertices = [
    62
    if vertice in vertices_selecionados
    else 46
    for vertice in grafo_original.nodes()
]

fig, ax = ox.plot_graph(
    grafo_original,
    node_size=tamanhos_vertices,
    node_color=cores_vertices,
    edge_color="#455A64",
    edge_linewidth=1.4,
    bgcolor="white",
    show=False,
    close=False
)

fig.set_size_inches(
    10,
    12
)

for vertice in vertices_ordenados:
    rotulo = rotulos_por_vertice[
        vertice
    ]

    x = float(
        grafo.nodes[vertice]["x"]
    )

    y = float(
        grafo.nodes[vertice]["y"]
    )

    selecionado = (
        vertice in vertices_selecionados
    )

    deslocamento = DESLOCAMENTOS_ROTULOS.get(
        rotulo,
        (5, 5)
    )

    ax.annotate(
        rotulo,
        xy=(x, y),
        xytext=deslocamento,
        textcoords="offset points",
        fontsize=8,
        fontweight=(
            "bold"
            if selecionado
            else "normal"
        ),
        color="#111111",
        zorder=5,
        bbox={
            "boxstyle": "round,pad=0.16",
            "facecolor": "white",
            "edgecolor": (
                "#D32F2F"
                if selecionado
                else "#90A4AE"
            ),
            "linewidth": 0.9,
            "alpha": 0.96
        }
    )

legenda = [
    Line2D(
        [0],
        [0],
        marker="o",
        color="none",
        markerfacecolor="#D32F2F",
        markeredgecolor="#D32F2F",
        markersize=9,
        label="Vértice selecionado"
    ),
    Line2D(
        [0],
        [0],
        marker="o",
        color="none",
        markerfacecolor="#B0BEC5",
        markeredgecolor="#B0BEC5",
        markersize=9,
        label="Vértice não selecionado"
    )
]

ax.legend(
    handles=legenda,
    loc="upper right",
    frameon=True,
    fontsize=9
)

ax.set_title(
    "Rede viária com vértices numerados "
    "e cobertura da heurística",
    fontsize=13,
    pad=16
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

print("\nMapa concluído!")

print(
    f"Total de vértices numerados: "
    f"{quantidade_vertices}"
)

print(
    f"Vértices selecionados pela heurística: "
    f"{len(vertices_selecionados)}"
)