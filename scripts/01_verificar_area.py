from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.ops import transform


# Caminho do projeto e do novo polígono
PASTA_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_KMZ = (
    PASTA_PROJETO
    / "dados"
    / "area_estudo_russas_nova.kmz"
)


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
            raise ValueError("Nenhum arquivo KML foi encontrado dentro do KMZ.")

        conteudo_kml = arquivo_kmz.read(arquivos_kml[0])

    raiz = ET.fromstring(conteudo_kml)
    elemento_coordenadas = raiz.find(
        ".//{*}Polygon//{*}outerBoundaryIs//{*}coordinates"
    )

    if elemento_coordenadas is None:
        raise ValueError("Nenhum polígono foi encontrado no arquivo KMZ.")

    coordenadas = []

    for item in elemento_coordenadas.text.split():
        valores = item.split(",")
        longitude = float(valores[0])
        latitude = float(valores[1])
        coordenadas.append((longitude, latitude))

    # Remove a repetição do primeiro ponto usada para fechar o polígono
    if coordenadas[0] == coordenadas[-1]:
        coordenadas = coordenadas[:-1]

    if len(coordenadas) < 3:
        raise ValueError("O polígono precisa possuir pelo menos três pontos.")

    return Polygon(coordenadas), coordenadas


print(f"Arquivo utilizado: {CAMINHO_KMZ}")

poligono, coordenadas = ler_poligono_kmz(CAMINHO_KMZ)

# Russas-CE pertence à zona UTM 24 Sul
transformador = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:32724",
    always_xy=True
)

poligono_metros = transform(
    transformador.transform,
    poligono
)

area_m2 = poligono_metros.area
area_km2 = area_m2 / 1_000_000
area_hectares = area_m2 / 10_000
perimetro_km = poligono_metros.length / 1_000

longitude_minima, latitude_minima, longitude_maxima, latitude_maxima = (
    poligono.bounds
)

print("\nArquivo KMZ encontrado com sucesso!")
print(f"Polígono válido: {poligono.is_valid}")
print(f"Quantidade de pontos do polígono: {len(coordenadas)}")

print("\nMedidas do polígono:")
print(f"Área: {area_m2:.2f} m²")
print(f"Área: {area_km2:.6f} km²")
print(f"Área: {area_hectares:.4f} hectares")
print(f"Perímetro: {perimetro_km:.6f} km")

print("\nLimites geográficos:")
print(f"Latitude mínima: {latitude_minima}")
print(f"Latitude máxima: {latitude_maxima}")
print(f"Longitude mínima: {longitude_minima}")
print(f"Longitude máxima: {longitude_maxima}")