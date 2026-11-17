from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import osmnx as ox
from shapely.geometry import Polygon


# ---------------------------------------------------------
# Caminhos
# ---------------------------------------------------------

PASTA_PROJETO = Path(__file__).resolve().parent.parent
PASTA_DADOS = PASTA_PROJETO / "dados"

CAMINHO_KMZ = (
    PASTA_DADOS
    / "area_estudo_russas_nova.kmz"
)

CAMINHO_GRAFO = (
    PASTA_DADOS
    / "rede_osm_bruta.graphml"
)


# ---------------------------------------------------------
# Leitura do polígono armazenado no KMZ
# ---------------------------------------------------------

def ler_poligono_kmz(caminho_kmz):
    if not caminho_kmz.exists():
        raise FileNotFoundError(
            f"O arquivo não foi encontrado em: {caminho_kmz}"
        )

    with ZipFile(caminho_kmz, "r") as arquivo_kmz:
        arquivos_kml = [
            nome
            for nome in arquivo_kmz.namelist()
            if nome.lower().endswith(".kml")
        ]

        if not arquivos_kml:
            raise ValueError(
                "Nenhum KML foi encontrado dentro do KMZ."
            )

        conteudo_kml = arquivo_kmz.read(
            arquivos_kml[0]
        )

    raiz = ET.fromstring(conteudo_kml)

    elemento_coordenadas = raiz.find(
        ".//{*}Polygon//{*}outerBoundaryIs//{*}coordinates"
    )

    if elemento_coordenadas is None:
        raise ValueError(
            "Nenhum polígono foi encontrado no KMZ."
        )

    if elemento_coordenadas.text is None:
        raise ValueError(
            "O polígono encontrado não possui coordenadas."
        )

    coordenadas = []

    for item in elemento_coordenadas.text.split():
        valores = item.split(",")

        longitude = float(valores[0])
        latitude = float(valores[1])

        coordenadas.append(
            (longitude, latitude)
        )

    if coordenadas[0] == coordenadas[-1]:
        coordenadas = coordenadas[:-1]

    return Polygon(coordenadas)


# ---------------------------------------------------------
# Configurações do OSMnx
# ---------------------------------------------------------

ox.settings.use_cache = True
ox.settings.log_console = True
ox.settings.requests_timeout = 180

PASTA_DADOS.mkdir(
    parents=True,
    exist_ok=True
)


# ---------------------------------------------------------
# Coleta
# ---------------------------------------------------------

print("Lendo o polígono da área de estudo...")

poligono = ler_poligono_kmz(
    CAMINHO_KMZ
)

print("Polígono lido com sucesso!")

print(
    "\nColetando a rede viária bruta "
    "no OpenStreetMap..."
)

grafo = ox.graph.graph_from_polygon(
    poligono,
    network_type="all_public",
    simplify=False,
    retain_all=True,
    truncate_by_edge=False
)

print("\nColeta concluída!")

print(
    f"Tipo do grafo: "
    f"{type(grafo).__name__}"
)

print(
    f"Quantidade de vértices brutos: "
    f"{grafo.number_of_nodes()}"
)

print(
    f"Quantidade de arestas direcionadas: "
    f"{grafo.number_of_edges()}"
)


# ---------------------------------------------------------
# Salvamento
# ---------------------------------------------------------

ox.io.save_graphml(
    grafo,
    filepath=CAMINHO_GRAFO
)

print(
    f"\nRede bruta salva em: "
    f"{CAMINHO_GRAFO}"
)