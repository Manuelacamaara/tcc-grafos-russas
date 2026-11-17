from pathlib import Path
import ast

import matplotlib.pyplot as plt
import networkx as nx
import osmnx as ox


# ---------------------------------------------------------
# Caminhos dos arquivos
# ---------------------------------------------------------

PASTA_PROJETO = Path(__file__).resolve().parent.parent
PASTA_DADOS = PASTA_PROJETO / "dados"
PASTA_RESULTADOS = PASTA_PROJETO / "resultados"

CAMINHO_REDE_BRUTA = (
    PASTA_DADOS
    / "rede_osm_bruta.graphml"
)

CAMINHO_REDE_TOPOLOGICA = (
    PASTA_RESULTADOS
    / "rede_osm_topologica.graphml"
)

CAMINHO_IMAGEM = (
    PASTA_RESULTADOS
    / "rede_osm_topologica.png"
)


# ---------------------------------------------------------
# Elementos validados manualmente
# ---------------------------------------------------------

# Pequenos elementos de acessibilidade que não representam
# caminhos independentes.
PASSAGENS_ACESSIBILIDADE = {
    frozenset({"7043367054", "2388100682"}),
    frozenset({"4953731040", "2388100684"})
}

# Becos públicos destinados à circulação de pedestres.
# Esses identificadores foram encontrados no GraphML.
BECOS_PEDESTRES_MANTIDOS = {
    "256660340",
    "256660341"
}


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


def eh_caminho_sem_nome(dados_aresta):
    tipos_via = transformar_em_lista(
        dados_aresta.get("highway")
    )

    tipos_via = {
        str(tipo)
        for tipo in tipos_via
    }

    nome = dados_aresta.get("name")

    sem_nome = (
        nome is None
        or str(nome).strip() == ""
        or str(nome).lower() == "nan"
    )

    return "footway" in tipos_via and sem_nome


def obter_osmids(dados_aresta):
    valores = transformar_em_lista(
        dados_aresta.get("osmid")
    )

    return {
        str(valor)
        for valor in valores
    }


# ---------------------------------------------------------
# Carregamento da rede bruta
# ---------------------------------------------------------

if not CAMINHO_REDE_BRUTA.exists():
    raise FileNotFoundError(
        "A rede bruta não foi encontrada em: "
        f"{CAMINHO_REDE_BRUTA}"
    )

PASTA_RESULTADOS.mkdir(
    parents=True,
    exist_ok=True
)

print("Carregando a rede bruta...")

grafo_bruto = ox.io.load_graphml(
    CAMINHO_REDE_BRUTA
)

print(
    f"Vértices da rede bruta: "
    f"{grafo_bruto.number_of_nodes()}"
)

print(
    f"Arestas direcionadas da rede bruta: "
    f"{grafo_bruto.number_of_edges()}"
)


# ---------------------------------------------------------
# Identificação das arestas
# ---------------------------------------------------------

arestas_remover = []

quantidade_becos_mantidos = 0
quantidade_caminhos_sem_nome_removidos = 0
quantidade_passagens_acessibilidade = 0

for origem, destino, chave, dados in grafo_bruto.edges(
    keys=True,
    data=True
):
    identificadores_vertices = frozenset({
        str(origem),
        str(destino)
    })

    osmids_aresta = obter_osmids(
        dados
    )

    beco_pedestre_mantido = bool(
        osmids_aresta
        & BECOS_PEDESTRES_MANTIDOS
    )

    caminho_sem_nome_detectado = (
        eh_caminho_sem_nome(dados)
    )

    # Um caminho sem nome será removido somente se
    # não corresponder a um dos dois becos públicos.
    caminho_sem_nome_removivel = (
        caminho_sem_nome_detectado
        and not beco_pedestre_mantido
    )

    passagem_acessibilidade = (
        identificadores_vertices
        in PASSAGENS_ACESSIBILIDADE
    )

    if beco_pedestre_mantido:
        quantidade_becos_mantidos += 1

    if caminho_sem_nome_removivel:
        quantidade_caminhos_sem_nome_removidos += 1

    if passagem_acessibilidade:
        quantidade_passagens_acessibilidade += 1

    if (
        caminho_sem_nome_removivel
        or passagem_acessibilidade
    ):
        arestas_remover.append(
            (origem, destino, chave)
        )


print(
    "\nArestas direcionadas dos becos mantidas: "
    f"{quantidade_becos_mantidos}"
)

print(
    "Arestas direcionadas de outros caminhos "
    "sem nome removidas: "
    f"{quantidade_caminhos_sem_nome_removidos}"
)

print(
    "Arestas direcionadas de passagens "
    "de acessibilidade removidas: "
    f"{quantidade_passagens_acessibilidade}"
)

print(
    "Total de arestas direcionadas removidas: "
    f"{len(arestas_remover)}"
)


# ---------------------------------------------------------
# Remoção das arestas e dos vértices isolados
# ---------------------------------------------------------

grafo_bruto.remove_edges_from(
    arestas_remover
)

vertices_isolados = list(
    nx.isolates(grafo_bruto)
)

grafo_bruto.remove_nodes_from(
    vertices_isolados
)

print(
    f"Vértices isolados removidos: "
    f"{len(vertices_isolados)}"
)


# ---------------------------------------------------------
# Simplificação topológica
# ---------------------------------------------------------

print("\nRealizando a simplificação topológica...")

grafo_topologico = ox.simplification.simplify_graph(
    grafo_bruto,
    edge_attrs_differ=["name"],
    remove_rings=False
)

print("\nPreparação topológica concluída!")

print(
    f"Vértices resultantes: "
    f"{grafo_topologico.number_of_nodes()}"
)

print(
    f"Arestas direcionadas resultantes: "
    f"{grafo_topologico.number_of_edges()}"
)


# ---------------------------------------------------------
# Salvamento
# ---------------------------------------------------------

ox.io.save_graphml(
    grafo_topologico,
    filepath=CAMINHO_REDE_TOPOLOGICA
)

print(
    f"\nRede salva em: "
    f"{CAMINHO_REDE_TOPOLOGICA}"
)


# ---------------------------------------------------------
# Geração da imagem intermediária
# ---------------------------------------------------------

print("Gerando a imagem intermediária...")

fig, ax = ox.plot_graph(
    grafo_topologico,
    node_size=25,
    node_color="#D32F2F",
    edge_color="#37474F",
    edge_linewidth=1.2,
    bgcolor="white",
    show=False,
    close=False
)

ax.set_title(
    "Rede viária após a preparação topológica",
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
    f"Imagem intermediária salva em: "
    f"{CAMINHO_IMAGEM}"
)