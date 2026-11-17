from pathlib import Path
from statistics import mean, median, stdev
from time import perf_counter_ns
import csv

import networkx as nx
import osmnx as ox

from algoritmos_cobertura import (
    aproximacao_networkx,
    cobertura_valida,
    heuristica_gulosa_por_grau,
    solucao_exata_milp,
)

from utilitarios_vertices import (
    criar_mapeamento_vertices
)


REPETICOES_AQUECIMENTO = 10
REPETICOES_MEDIDAS = 100

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
    / "comparacao_metodos_referencia.txt"
)

CAMINHO_CSV = (
    PASTA_RESULTADOS
    / "comparacao_metodos_referencia.csv"
)


def executar_heuristica(grafo):
    selecionados, _ = (
        heuristica_gulosa_por_grau(grafo)
    )

    return set(selecionados), {}


def executar_networkx(grafo):
    return aproximacao_networkx(grafo), {}


def executar_scipy(grafo):
    solucao, metadados = (
        solucao_exata_milp(grafo)
    )

    if solucao is None:
        raise RuntimeError(
            "O SciPy não comprovou a solução ótima. "
            f"Status: {metadados['status']}. "
            f"Mensagem: {metadados['mensagem']}"
        )

    return solucao, metadados


def medir(funcao, grafo):
    inicio = perf_counter_ns()

    solucao, metadados = funcao(grafo)

    tempo_ms = (
        perf_counter_ns() - inicio
    ) / 1_000_000

    return solucao, metadados, tempo_ms


def resumo(tempos):
    return {
        "media": mean(tempos),
        "mediana": median(tempos),
        "desvio": stdev(tempos),
        "minimo": min(tempos),
        "maximo": max(tempos),
    }


def texto_resumo(nome, dados):
    return (
        f"{nome}: "
        f"média={dados['media']:.6f} ms; "
        f"mediana={dados['mediana']:.6f} ms; "
        f"desvio-padrão={dados['desvio']:.6f} ms; "
        f"mínimo={dados['minimo']:.6f} ms; "
        f"máximo={dados['maximo']:.6f} ms"
    )


def ordenar_rotulos(
    solucao,
    rotulos
):
    return sorted(
        (
            rotulos[vertice]
            for vertice in solucao
        ),
        key=lambda rotulo: int(
            rotulo.removeprefix("V")
        ),
    )


if not CAMINHO_REDE.exists():
    raise FileNotFoundError(
        f"A rede não foi encontrada em: "
        f"{CAMINHO_REDE}"
    )


print("Carregando a rede final validada...")

grafo = nx.Graph(
    ox.io.load_graphml(CAMINHO_REDE)
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


if (
    quantidade_vertices != 26
    or quantidade_arestas != 37
):
    raise ValueError(
        "A comparação esperava o grafo final "
        "com 26 vértices e 37 arestas."
    )


rotulos_por_vertice, _ = (
    criar_mapeamento_vertices(grafo)
)


metodos = {
    "heuristica": executar_heuristica,
    "networkx": executar_networkx,
    "scipy": executar_scipy,
}

nomes = {
    "heuristica": "Heurística proposta",
    "networkx": "Aproximação do NetworkX",
    "scipy": "Solução exata do SciPy/HiGHS",
}

ordens = [
    [
        "heuristica",
        "networkx",
        "scipy"
    ],
    [
        "networkx",
        "scipy",
        "heuristica"
    ],
    [
        "scipy",
        "heuristica",
        "networkx"
    ],
    [
        "heuristica",
        "scipy",
        "networkx"
    ],
    [
        "networkx",
        "heuristica",
        "scipy"
    ],
    [
        "scipy",
        "networkx",
        "heuristica"
    ],
]


print(
    f"\nExecutando "
    f"{REPETICOES_AQUECIMENTO} "
    f"repetições de aquecimento..."
)

for repeticao in range(
    REPETICOES_AQUECIMENTO
):
    ordem = ordens[
        repeticao % len(ordens)
    ]

    for nome in ordem:
        solucao, _ = metodos[nome](
            grafo
        )

        if not cobertura_valida(
            grafo,
            solucao
        ):
            raise RuntimeError(
                "Cobertura inválida no "
                f"aquecimento: {nome}."
            )


print(
    f"Executando "
    f"{REPETICOES_MEDIDAS} "
    f"repetições medidas..."
)

tempos = {
    nome: []
    for nome in metodos
}

solucoes = {}
quantidades = {}
metadados_scipy = None
registros = []


for repeticao in range(
    1,
    REPETICOES_MEDIDAS + 1
):
    registro = {
        "repeticao": repeticao
    }

    ordem = ordens[
        (repeticao - 1) % len(ordens)
    ]

    for nome in ordem:
        (
            solucao,
            metadados,
            tempo_ms
        ) = medir(
            metodos[nome],
            grafo
        )

        if not cobertura_valida(
            grafo,
            solucao
        ):
            raise RuntimeError(
                f"O método {nome} produziu "
                "uma cobertura inválida."
            )

        quantidade = len(solucao)

        if nome not in quantidades:
            quantidades[nome] = quantidade
            solucoes[nome] = set(solucao)

        elif quantidade != quantidades[nome]:
            raise RuntimeError(
                f"A quantidade de {nome} "
                "variou entre as repetições."
            )

        tempos[nome].append(
            tempo_ms
        )

        registro[
            f"tempo_{nome}_ms"
        ] = f"{tempo_ms:.9f}"

        registro[
            f"vertices_{nome}"
        ] = quantidade

        if nome == "scipy":
            metadados_scipy = metadados

    registros.append(registro)


resumos = {
    nome: resumo(valores)
    for nome, valores in tempos.items()
}

otimo = quantidades["scipy"]

media_heuristica = (
    resumos["heuristica"]["media"]
)


linhas = [
    "COMPARAÇÃO COM MÉTODOS DE REFERÊNCIA",
    "",
    (
        "Vértices do grafo: "
        f"{quantidade_vertices}"
    ),
    (
        "Arestas do grafo: "
        f"{quantidade_arestas}"
    ),
    (
        "Repetições de aquecimento: "
        f"{REPETICOES_AQUECIMENTO}"
    ),
    (
        "Repetições medidas: "
        f"{REPETICOES_MEDIDAS}"
    ),
    "Unidade dos tempos: milissegundos",
    "",
    "QUALIDADE DAS SOLUÇÕES",
    "",
]


for nome in metodos:
    quantidade = quantidades[nome]

    diferenca = (
        quantidade - otimo
    )

    desvio = (
        diferenca
        / otimo
        * 100
    )

    rotulos = ordenar_rotulos(
        solucoes[nome],
        rotulos_por_vertice
    )

    linhas.extend([
        nomes[nome],
        (
            "Vértices selecionados: "
            f"{quantidade}"
        ),
        (
            "Identificações: "
            + ", ".join(rotulos)
        ),
        (
            "Diferença para o ótimo: "
            f"{diferenca}"
        ),
        (
            "Desvio percentual: "
            f"{desvio:.2f}%"
        ),
        (
            "Razão em relação ao ótimo: "
            f"{quantidade / otimo:.4f}"
        ),
        "",
    ])


linhas.extend([
    "DESEMPENHO",
    ""
])


for nome in metodos:
    linhas.append(
        texto_resumo(
            nomes[nome],
            resumos[nome]
        )
    )

    linhas.append(
        "Razão do tempo médio em relação "
        "à heurística: "
        f"{resumos[nome]['media'] / media_heuristica:.4f}"
    )

    linhas.append("")


gap = metadados_scipy["mip_gap"]

linhas.extend([
    "VALIDAÇÃO DO MÉTODO EXATO",
    "",
    (
        "Status do SciPy: "
        f"{metadados_scipy['status']}"
    ),
    (
        "Mensagem: "
        f"{metadados_scipy['mensagem']}"
    ),
    (
        "Valor ótimo da função objetivo: "
        f"{metadados_scipy['valor_objetivo']:.0f}"
    ),
    (
        "Gap final do solucionador: "
        + (
            "não informado"
            if gap is None
            else f"{float(gap):.8f}"
        )
    ),
])


relatorio = "\n".join(
    linhas
)

print(
    "\n" + relatorio
)


PASTA_RESULTADOS.mkdir(
    parents=True,
    exist_ok=True
)

CAMINHO_RELATORIO.write_text(
    relatorio,
    encoding="utf-8"
)


with CAMINHO_CSV.open(
    "w",
    newline="",
    encoding="utf-8-sig"
) as arquivo:
    campos = [
        "repeticao",
        "tempo_heuristica_ms",
        "vertices_heuristica",
        "tempo_networkx_ms",
        "vertices_networkx",
        "tempo_scipy_ms",
        "vertices_scipy",
    ]

    escritor = csv.DictWriter(
        arquivo,
        fieldnames=campos
    )

    escritor.writeheader()
    escritor.writerows(registros)


print(
    f"\nRelatório salvo em: "
    f"{CAMINHO_RELATORIO}"
)

print(
    f"Medições em CSV salvas em: "
    f"{CAMINHO_CSV}"
)