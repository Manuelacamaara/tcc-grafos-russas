from pathlib import Path
from collections import deque

import networkx as nx
import osmnx as ox

from utilitarios_vertices import criar_mapeamento_vertices


# ---------------------------------------------------------
# Caminhos
# ---------------------------------------------------------

PASTA_PROJETO = Path(__file__).resolve().parent.parent
PASTA_RESULTADOS = PASTA_PROJETO / "resultados"

CAMINHO_REDE = (
    PASTA_RESULTADOS
    / "rede_osm_ajustada.graphml"
)

CAMINHO_RELATORIO = (
    PASTA_RESULTADOS
    / "validacao_rede.txt"
)


# ---------------------------------------------------------
# Implementação do BFS
# ---------------------------------------------------------

def busca_em_largura(
    grafo,
    vertice_inicial,
    rotulos_por_vertice
):
    visitados = {vertice_inicial}
    fila = deque([vertice_inicial])

    ordem_visita = []
    niveis = {vertice_inicial: 0}

    while fila:
        vertice_atual = fila.popleft()
        ordem_visita.append(vertice_atual)

        vizinhos_ordenados = sorted(
            grafo.neighbors(vertice_atual),
            key=lambda vertice: rotulos_por_vertice[
                vertice
            ]
        )

        for vizinho in vizinhos_ordenados:
            if vizinho not in visitados:
                visitados.add(vizinho)
                fila.append(vizinho)

                niveis[vizinho] = (
                    niveis[vertice_atual] + 1
                )

    return ordem_visita, niveis


# ---------------------------------------------------------
# Carregamento
# ---------------------------------------------------------

if not CAMINHO_REDE.exists():
    raise FileNotFoundError(
        f"A rede não foi encontrada em: {CAMINHO_REDE}"
    )


print("Carregando a rede ajustada...")

grafo_original = ox.io.load_graphml(
    CAMINHO_REDE
)

grafo = nx.Graph(grafo_original)


# ---------------------------------------------------------
# Numeração visual padronizada
# ---------------------------------------------------------

(
    rotulos_por_vertice,
    vertices_por_rotulo
) = criar_mapeamento_vertices(grafo)


# ---------------------------------------------------------
# Verificações estruturais
# ---------------------------------------------------------

quantidade_vertices = grafo.number_of_nodes()
quantidade_arestas = grafo.number_of_edges()

quantidade_lacos = nx.number_of_selfloops(
    grafo
)

vertices_isolados = list(
    nx.isolates(grafo)
)

quantidade_componentes = (
    nx.number_connected_components(grafo)
)

tamanhos_componentes = sorted(
    (
        len(componente)
        for componente
        in nx.connected_components(grafo)
    ),
    reverse=True
)

arestas_multigrafo = (
    grafo_original.number_of_edges()
)

arestas_grafo_simples = (
    grafo.number_of_edges()
)

arestas_paralelas = (
    arestas_multigrafo
    - arestas_grafo_simples
)


# ---------------------------------------------------------
# Escolha reproduzível do vértice inicial
# ---------------------------------------------------------

grau_maximo_encontrado = max(
    grau
    for _, grau in grafo.degree()
)

candidatos_iniciais = [
    vertice
    for vertice, grau in grafo.degree()
    if grau == grau_maximo_encontrado
]

vertice_inicial = min(
    candidatos_iniciais,
    key=lambda vertice: rotulos_por_vertice[
        vertice
    ]
)

rotulo_vertice_inicial = (
    rotulos_por_vertice[vertice_inicial]
)


# ---------------------------------------------------------
# Execução do BFS
# ---------------------------------------------------------

ordem_visita, niveis = busca_em_largura(
    grafo,
    vertice_inicial,
    rotulos_por_vertice
)

ordem_visita_rotulos = [
    rotulos_por_vertice[vertice]
    for vertice in ordem_visita
]

quantidade_visitados = len(
    ordem_visita
)

rede_conectada = (
    quantidade_visitados
    == quantidade_vertices
)

maior_nivel = max(
    niveis.values()
)


# ---------------------------------------------------------
# Estatísticas dos graus
# ---------------------------------------------------------

graus = [
    grau
    for _, grau
    in grafo.degree()
]

grau_minimo = min(graus)
grau_maximo = max(graus)
grau_medio = sum(graus) / len(graus)


# ---------------------------------------------------------
# Relatório
# ---------------------------------------------------------

linhas_relatorio = [
    "VALIDAÇÃO DA REDE VIÁRIA",
    "",
    f"Tipo original: {type(grafo_original).__name__}",
    f"Grafo direcionado: {grafo_original.is_directed()}",
    f"Quantidade de vértices: {quantidade_vertices}",
    f"Quantidade de arestas: {quantidade_arestas}",
    f"Laços: {quantidade_lacos}",
    f"Arestas paralelas: {arestas_paralelas}",
    f"Vértices isolados: {len(vertices_isolados)}",
    f"Componentes conexos: {quantidade_componentes}",
    (
        "Tamanhos dos componentes: "
        f"{tamanhos_componentes}"
    ),
    "",
    "RESULTADO DO BFS",
    "",
    f"Vértice inicial: {rotulo_vertice_inicial}",
    (
        "Grau do vértice inicial: "
        f"{grafo.degree(vertice_inicial)}"
    ),
    f"Vértices visitados: {quantidade_visitados}",
    f"Total de vértices: {quantidade_vertices}",
    f"Maior nível alcançado: {maior_nivel}",
    f"Rede conectada: {rede_conectada}",
    "",
    "ESTATÍSTICAS DE GRAU",
    "",
    f"Grau mínimo: {grau_minimo}",
    f"Grau máximo: {grau_maximo}",
    f"Grau médio: {grau_medio:.2f}",
    "",
    "Ordem de visita do BFS:",
    ", ".join(ordem_visita_rotulos)
]

relatorio = "\n".join(
    linhas_relatorio
)

print("\n" + relatorio)

CAMINHO_RELATORIO.write_text(
    relatorio,
    encoding="utf-8"
)

print(
    f"\nRelatório salvo em: "
    f"{CAMINHO_RELATORIO}"
)