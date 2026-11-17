from pathlib import Path
from statistics import mean, median, stdev
from time import perf_counter_ns
import csv

import networkx as nx

from algoritmos_cobertura import (
    aproximacao_networkx,
    cobertura_valida,
    heuristica_gulosa_por_grau,
    solucao_exata_milp,
)


LADOS_DAS_GRADES = [
    5,
    7,
    10,
    15,
    20
]

REPETICOES_AQUECIMENTO = 5
REPETICOES_MEDIDAS = 30
LIMITE_MILP_SEGUNDOS = 60.0

PASTA_PROJETO = (
    Path(__file__).resolve().parent.parent
)

PASTA_RESULTADOS = (
    PASTA_PROJETO / "resultados"
)

CAMINHO_RELATORIO = (
    PASTA_RESULTADOS
    / "resultado_escalabilidade_referencias.txt"
)

CAMINHO_CSV = (
    PASTA_RESULTADOS
    / "resultado_escalabilidade_referencias.csv"
)


def gerar_grafo_grade(lado):
    grafo = nx.grid_2d_graph(
        lado,
        lado
    )

    return nx.convert_node_labels_to_integers(
        grafo,
        first_label=0,
        ordering="sorted"
    )


def executar_heuristica(grafo):
    selecionados, _ = (
        heuristica_gulosa_por_grau(grafo)
    )

    return set(selecionados), {
        "status": "concluído"
    }


def executar_networkx(grafo):
    return aproximacao_networkx(grafo), {
        "status": "concluído"
    }


def executar_scipy(grafo):
    solucao, metadados = (
        solucao_exata_milp(
            grafo,
            limite_segundos=(
                LIMITE_MILP_SEGUNDOS
            )
        )
    )

    metadados["status_texto"] = (
        "ótimo comprovado"
        if solucao is not None
        else (
            "ótimo não comprovado "
            "dentro do limite"
        )
    )

    return solucao, metadados


def medir(funcao, grafo):
    inicio = perf_counter_ns()

    solucao, metadados = funcao(
        grafo
    )

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


def formatar(valor):
    if valor is None:
        return ""

    return f"{valor:.6f}"


metodos = {
    "heuristica": executar_heuristica,
    "networkx": executar_networkx,
    "scipy": executar_scipy,
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
]


print(
    "ESCALABILIDADE COM "
    "MÉTODOS DE REFERÊNCIA"
)

print(
    "Grades testadas: "
    + ", ".join(
        f"{lado}x{lado}"
        for lado in LADOS_DAS_GRADES
    )
)

print(
    "Repetições de aquecimento "
    "por instância: "
    f"{REPETICOES_AQUECIMENTO}"
)

print(
    "Repetições medidas por instância: "
    f"{REPETICOES_MEDIDAS}"
)

print(
    "Limite do SciPy por execução: "
    f"{LIMITE_MILP_SEGUNDOS:.0f} segundos"
)


registros = []

linhas = [
    "ESCALABILIDADE COM MÉTODOS DE REFERÊNCIA",
    "",
    "Tipo de grafo: grade quadrada conectada",
    (
        "Repetições de aquecimento "
        "por instância: "
        f"{REPETICOES_AQUECIMENTO}"
    ),
    (
        "Repetições medidas por instância: "
        f"{REPETICOES_MEDIDAS}"
    ),
    (
        "Limite do SciPy por execução: "
        f"{LIMITE_MILP_SEGUNDOS:.0f} segundos"
    ),
    "Unidade dos tempos: milissegundos",
    "",
]


for lado in LADOS_DAS_GRADES:
    grafo = gerar_grafo_grade(
        lado
    )

    quantidade_vertices = (
        grafo.number_of_nodes()
    )

    quantidade_arestas = (
        grafo.number_of_edges()
    )

    print(
        f"\nGrade {lado}x{lado}: "
        f"{quantidade_vertices} vértices e "
        f"{quantidade_arestas} arestas"
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

            if (
                solucao is not None
                and not cobertura_valida(
                    grafo,
                    solucao
                )
            ):
                raise RuntimeError(
                    "Cobertura inválida no "
                    f"aquecimento: {nome}."
                )


    tempos = {
        nome: []
        for nome in metodos
    }

    quantidades = {}
    status_scipy = "não executado"


    for repeticao in range(
        REPETICOES_MEDIDAS
    ):
        ordem = ordens[
            repeticao % len(ordens)
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

            if nome == "scipy":
                status_scipy = (
                    metadados["status_texto"]
                )

                if solucao is None:
                    continue

            if not cobertura_valida(
                grafo,
                solucao
            ):
                raise RuntimeError(
                    f"O método {nome} produziu "
                    "uma cobertura inválida."
                )

            quantidade = len(
                solucao
            )

            if nome not in quantidades:
                quantidades[nome] = quantidade

            elif quantidade != quantidades[nome]:
                raise RuntimeError(
                    f"A quantidade de {nome} "
                    "variou entre as repetições."
                )

            tempos[nome].append(
                tempo_ms
            )


    resumos = {
        nome: resumo(valores)
        for nome, valores in tempos.items()
        if len(valores) >= 2
    }

    quantidade_heuristica = (
        quantidades["heuristica"]
    )

    quantidade_networkx = (
        quantidades["networkx"]
    )

    quantidade_otima = (
        quantidades.get("scipy")
    )


    if quantidade_otima is None:
        diferenca_heuristica = None
        diferenca_networkx = None
        desvio_heuristica = None
        desvio_networkx = None

    else:
        diferenca_heuristica = (
            quantidade_heuristica
            - quantidade_otima
        )

        diferenca_networkx = (
            quantidade_networkx
            - quantidade_otima
        )

        desvio_heuristica = (
            diferenca_heuristica
            / quantidade_otima
            * 100
        )

        desvio_networkx = (
            diferenca_networkx
            / quantidade_otima
            * 100
        )


    print(
        "Heurística: "
        f"{quantidade_heuristica} vértices; "
        f"média="
        f"{resumos['heuristica']['media']:.6f} ms"
    )

    print(
        "NetworkX: "
        f"{quantidade_networkx} vértices; "
        f"média="
        f"{resumos['networkx']['media']:.6f} ms"
    )

    if quantidade_otima is not None:
        print(
            "SciPy/HiGHS: "
            f"{quantidade_otima} vértices ótimos; "
            f"média="
            f"{resumos['scipy']['media']:.6f} ms"
        )

    else:
        print(
            "SciPy/HiGHS: ótimo não comprovado "
            "dentro do limite."
        )


    registros.append({
        "grade": f"{lado}x{lado}",
        "vertices": quantidade_vertices,
        "arestas": quantidade_arestas,
        "vertices_heuristica": (
            quantidade_heuristica
        ),
        "tempo_heuristica_media_ms": formatar(
            resumos["heuristica"]["media"]
        ),
        "vertices_networkx": (
            quantidade_networkx
        ),
        "tempo_networkx_media_ms": formatar(
            resumos["networkx"]["media"]
        ),
        "status_scipy": status_scipy,
        "vertices_otimos_scipy": (
            ""
            if quantidade_otima is None
            else quantidade_otima
        ),
        "tempo_scipy_media_ms": (
            ""
            if "scipy" not in resumos
            else formatar(
                resumos["scipy"]["media"]
            )
        ),
        "diferenca_heuristica": (
            ""
            if diferenca_heuristica is None
            else diferenca_heuristica
        ),
        "desvio_heuristica_percentual": (
            formatar(desvio_heuristica)
        ),
        "diferenca_networkx": (
            ""
            if diferenca_networkx is None
            else diferenca_networkx
        ),
        "desvio_networkx_percentual": (
            formatar(desvio_networkx)
        ),
    })


    linhas.extend([
        f"Grade {lado}x{lado}",
        (
            "Vértices: "
            f"{quantidade_vertices}"
        ),
        (
            "Arestas: "
            f"{quantidade_arestas}"
        ),
        (
            "Heurística - vértices "
            "selecionados: "
            f"{quantidade_heuristica}"
        ),
        (
            "Heurística - tempo médio: "
            f"{resumos['heuristica']['media']:.6f} ms"
        ),
        (
            "NetworkX - vértices "
            "selecionados: "
            f"{quantidade_networkx}"
        ),
        (
            "NetworkX - tempo médio: "
            f"{resumos['networkx']['media']:.6f} ms"
        ),
        (
            "SciPy - status: "
            f"{status_scipy}"
        ),
        (
            "SciPy - vértices ótimos: "
            + (
                "não comprovado"
                if quantidade_otima is None
                else str(quantidade_otima)
            )
        ),
        (
            "SciPy - tempo médio: "
            + (
                "não disponível"
                if "scipy" not in resumos
                else (
                    f"{resumos['scipy']['media']:.6f} ms"
                )
            )
        ),
        (
            "Diferença da heurística "
            "para o ótimo: "
            + (
                "não calculada"
                if diferenca_heuristica is None
                else str(diferenca_heuristica)
            )
        ),
        (
            "Diferença do NetworkX "
            "para o ótimo: "
            + (
                "não calculada"
                if diferenca_networkx is None
                else str(diferenca_networkx)
            )
        ),
        "",
    ])


PASTA_RESULTADOS.mkdir(
    parents=True,
    exist_ok=True
)

CAMINHO_RELATORIO.write_text(
    "\n".join(linhas),
    encoding="utf-8"
)


with CAMINHO_CSV.open(
    "w",
    newline="",
    encoding="utf-8-sig"
) as arquivo:
    campos = [
        "grade",
        "vertices",
        "arestas",
        "vertices_heuristica",
        "tempo_heuristica_media_ms",
        "vertices_networkx",
        "tempo_networkx_media_ms",
        "status_scipy",
        "vertices_otimos_scipy",
        "tempo_scipy_media_ms",
        "diferenca_heuristica",
        "desvio_heuristica_percentual",
        "diferenca_networkx",
        "desvio_networkx_percentual",
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
    f"Resultados em CSV salvos em: "
    f"{CAMINHO_CSV}"
)