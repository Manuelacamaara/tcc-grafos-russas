def criar_mapeamento_vertices(grafo):
    """
    Cria uma numeração visual e reproduzível para os vértices.

    Os vértices são ordenados geograficamente:
    1. do norte para o sul;
    2. do oeste para o leste;
    3. pelo identificador interno, em caso de empate.

    Retorna:
        - rotulos_por_vertice: identificador interno -> V01, V02...
        - vertices_por_rotulo: V01, V02... -> identificador interno
    """

    for vertice, dados in grafo.nodes(data=True):
        if "x" not in dados or "y" not in dados:
            raise ValueError(
                f"O vértice {vertice} não possui coordenadas x e y."
            )

    vertices_ordenados = sorted(
        grafo.nodes(),
        key=lambda vertice: (
            -float(grafo.nodes[vertice]["y"]),
            float(grafo.nodes[vertice]["x"]),
            str(vertice)
        )
    )

    rotulos_por_vertice = {
        vertice: f"V{indice:02d}"
        for indice, vertice in enumerate(
            vertices_ordenados,
            start=1
        )
    }

    vertices_por_rotulo = {
        rotulo: vertice
        for vertice, rotulo in rotulos_por_vertice.items()
    }

    return rotulos_por_vertice, vertices_por_rotulo


def obter_rotulos(grafo, vertices):
    """
    Converte uma coleção de identificadores internos
    para os rótulos visuais V01, V02, ..., V26.
    """

    rotulos_por_vertice, _ = criar_mapeamento_vertices(
        grafo
    )

    return [
        rotulos_por_vertice[vertice]
        for vertice in vertices
    ]


def ordenar_rotulos(rotulos):
    """
    Ordena corretamente os rótulos:
    V01, V02, V03, ..., V26.
    """

    return sorted(
        rotulos,
        key=lambda rotulo: int(
            rotulo.removeprefix("V")
        )
    )


def formatar_rotulos(rotulos):
    """
    Produz uma representação textual padronizada.
    """

    return ", ".join(
        ordenar_rotulos(rotulos)
    )