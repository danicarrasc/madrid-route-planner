"""
callejero.py

Matemática Discreta - IMAT
ICAI, Universidad Pontificia Comillas

Grupo: GP17A
Integrantes:
    - Daniel Carrasco Jurado
    - Alejandro Corredera Bote

Descripción:
Librería con herramientas y clases auxiliares necesarias para la representación de un callejero en un grafo.

Carga direcciones y prepara grafos dirigidos para distintos criterios de coste.
"""

import networkx as nx
import pandas as pd
from pathlib import Path
from math import isfinite
import grafo_pesado
import re

from typing import Tuple

BASE_DIR = Path(__file__).resolve().parent
STREET_FILE_NAME = BASE_DIR / "direcciones.csv"

PLACE_NAME = "Madrid, Spain"
MAP_FILE_NAME = BASE_DIR / "madrid.graphml"

MAX_SPEEDS = {
    "living_street": "20",
    "residential": "30",
    "primary_link": "40",
    "unclassified": "40",
    "secondary_link": "40",
    "trunk_link": "40",
    "secondary": "50",
    "tertiary": "50",
    "primary": "50",
    "trunk": "50",
    "tertiary_link": "50",
    "busway": "50",
    "motorway_link": "70",
    "motorway": "100",
}


class ServiceNotAvailableError(Exception):
    "Excepción que indica que la navegación no está disponible en este momento"

    pass


class AddressNotFoundError(Exception):
    "Excepción que indica que una dirección buscada no existe en la base de datos"

    pass


############## Parte 2 ##############


def carga_callejero(archivo=None) -> pd.DataFrame:
    """
    Función que carga el callejero de Madrid, lo procesa y devuelve
    un DataFrame con los datos procesados

    Args: None

    Returns:
        DataFrame: dataframe con los datos del callejero procesados.

    Raises:
        FileNotFoundError: si el fichero csv con las direcciones no existe
    """

    # Definir una función auxiliar
    def _coords_a_dec(coords: str) -> float:
        """
        Función que recibe una coordenada de la forma < 3°40'23.56'' N > y la convierte a un
        float. Tomando las direcciones S y W como negativas

        Args:
            coords (str): la coordenada a transformar

        Returns:
            float: El número transformado

        Raises:
            ValueError: si la coordenada se encuentra en un formato incorrecto
        """
        patron = r"(\d+)°(\d+)'(\d+(?:\.\d+)?)''\s*([NSEW])"
        m = re.fullmatch(patron, str(coords).strip(), flags=re.IGNORECASE)
        if not m:
            raise ValueError(f"Coordenada no válida: {coords}")
        grados, minutos, segundos = map(float, m.groups()[:3])
        direccion = m.group(4).upper()
        limite = 90 if direccion in "NS" else 180
        decimal = grados + minutos / 60 + segundos / 3600
        # El CSV contiene segundos redondeados a 60; la suma los normaliza.
        if minutos >= 60 or segundos > 60 or decimal > limite:
            raise ValueError(f"Coordenada fuera de rango: {coords}")
        return -decimal if direccion in "SW" else decimal

    print("Cargando callejero...")

    cols = ["VIA_CLASE", "VIA_PAR", "VIA_NOMBRE", "NUMERO", "LATITUD", "LONGITUD"]
    # Dejar que cada error conserve su causa: archivo ausente, CSV inválido, etc.
    df = pd.read_csv(archivo or STREET_FILE_NAME, sep=";", encoding="latin-1", usecols=cols)
    df["LATITUD"] = df["LATITUD"].apply(_coords_a_dec)
    df["LONGITUD"] = df["LONGITUD"].apply(_coords_a_dec)
    df["DIRECCION_COMPLETA"] = (
        df["VIA_CLASE"].fillna("") + " " + df["VIA_PAR"].fillna("") + " "
        + df["VIA_NOMBRE"].fillna("")
    ).str.replace(r"\s+", " ", regex=True).str.strip().str.upper()
    print("Callejero cargado correctamente\n")
    return df


def busca_direccion(direccion: str, callejero: pd.DataFrame) -> Tuple[float, float]:
    """
    Función que busca una dirección, dada en el formato calle, numero
    en el DataFrame callejero de Madrid y devuelve el par (latitud, longitud) en grados de la
    ubicación geográfica de dicha dirección

    Args:
        direccion (str): Nombre completo de la calle con número, en formato "Calle, num"
        callejero (DataFrame): DataFrame con la información de las calles

    Returns:
        Tuple[float,float]: Par de float (latitud,longitud) de la dirección buscada, expresados en grados

    Raises:
        AddressNotFoundError: Si la dirección no existe en la base de datos

    Example:
        busca_direccion("Calle de Alberto Aguilera, 23", data)=(40.42998055555555,-3.7112583333333333)
        busca_direccion("Calle de Alberto Aguilera, 25", data)=(40.43013055555555,-3.7126916666666667)
    """
    try:
        # Parsear la dirección introducida y gestionar posibles errores
        direccion = direccion.split(",")
        if len(direccion) != 2:
            raise AddressNotFoundError(
                "Dirección introducida incorrectamente. (Formato: Calle de Alberto Aguilera, 1)"
            )
        try:
            num = int(direccion[1].strip())
        except ValueError:
            raise AddressNotFoundError(f"No se encontró el número: {direccion[1]}")

        via_completa = " ".join(direccion[0].upper().split())

        # Filtrar dataframe para buscar coincidencias
        resultado = callejero[
            (callejero["DIRECCION_COMPLETA"] == via_completa)
            & (callejero["NUMERO"] == num)
        ]

        if resultado.empty:
            raise AddressNotFoundError(f"No se encontró {via_completa}, {num}.")
        lon = resultado["LONGITUD"].iloc[0]
        lat = resultado["LATITUD"].iloc[0]

        return lat, lon

    # Capturar excepciones
    except AddressNotFoundError as e:
        raise AddressNotFoundError(f"Error buscando dirección: {str(e)}")


############## Parte 4 ##############


def carga_grafo() -> nx.MultiDiGraph:
    """
    Función que recupera el quiver de calles de Madrid de OpenStreetMap.

    Args: None

    Returns:
        nx.MultiDiGraph: Quiver de las calles de Madrid.

    Raises:
        ServiceNotAvailableError: Si no es posible recuperar el grafo de OpenStreetMap.
    """
    import osmnx as ox

    try:
        if MAP_FILE_NAME.exists():
            return ox.load_graphml(MAP_FILE_NAME)
        G = ox.graph_from_place(PLACE_NAME, network_type="drive")
        ox.save_graphml(G, MAP_FILE_NAME)
        return G
    except Exception as error:
        raise ServiceNotAvailableError(
            f"No se pudo cargar el grafo de Madrid: {error}"
        ) from error


def procesa_grafo(multidigrafo: nx.MultiDiGraph, peso=grafo_pesado.ruta_corta) -> nx.DiGraph:
    """Normaliza una copia y escoge la mejor arista paralela según el coste.

    Las velocidades se estiman por tipo de vía y se convierten a m/s. Cada
    modo conserva la arista de menor coste entre el mismo par de nodos.
    Se preservan los sentidos de circulación y no se modifica el original.
    """
    if not multidigrafo.is_directed():
        raise ValueError("La red de calles debe ser dirigida.")
    print("Procesando grafo...")
    G = nx.DiGraph()
    G.graph.update(multidigrafo.graph)
    G.add_nodes_from((n, dict(datos)) for n, datos in multidigrafo.nodes(data=True))
    candidato = nx.DiGraph()
    for u, v, original in multidigrafo.edges(data=True):
        if u == v:
            continue
        dato = dict(original)
        tipos = dato.get("highway", "unclassified")
        if isinstance(tipos, list):
            tipos = next((t for t in tipos if t != "unclassified"), "unclassified")
        dato["highway"] = tipos
        dato["maxspeed"] = float(MAX_SPEEDS.get(tipos, 50)) / 3.6
        nombre = dato.get("name")
        dato["name"] = (nombre[0] if nombre else None) if isinstance(nombre, list) else nombre
        longitud = dato.get("length")
        if isinstance(longitud, list):
            longitud = longitud[0] if longitud else None
        try:
            longitud = float(longitud)
        except (TypeError, ValueError) as error:
            raise ValueError(f"Longitud ausente o inválida en {u!r} -> {v!r}.") from error
        if not isfinite(longitud) or longitud < 0:
            raise ValueError(f"Longitud inválida en {u!r} -> {v!r}.")
        dato["length"] = longitud
        candidato.clear()
        candidato.add_edge(u, v, **dato)
        coste = peso(candidato, u, v)
        if not isfinite(coste) or coste < 0:
            raise ValueError("El coste de circulación debe ser finito y no negativo.")
        if not G.has_edge(u, v) or coste < peso(G, u, v):
            if G.has_edge(u, v):
                G.remove_edge(u, v)
            G.add_edge(u, v, **dato)
    print("Grafo cargado correctamente\n")
    return G


########## Funciones Extra ##########
def calcular_posibles_direcciones(df):
    print("Cargando posibles direcciones...")
    opciones_direcciones = [
        f"{row['DIRECCION_COMPLETA'].title()}, {int(row['NUMERO'])}"
        for _, row in df.iterrows()
    ]
    print("Todo listo.\n")
    return opciones_direcciones


def mostrar_mapa(mapa: nx.DiGraph, camino: nx.DiGraph) -> None:
    """
    Visualiza un grafo de mapa y resalta un camino específico sobre él.

    Esta función genera una visualización donde se muestra el grafo completo del mapa
    en color azul y superpone un camino específico resaltado en color rojo.

    Args:
        mapa (nx.DiGraph): Grafo dirigido que representa el mapa completo con todos los nodos y aristas.
            Debe contener atributos de posición 'x' e 'y' en cada nodo para la geolocalización.

        camino (nx.DiGraph): Subgrafo dirigido que representa la ruta específica a resaltar sobre el mapa.
            Debe ser un subconjunto del grafo `mapa` y compartir la misma estructura de nodos.

    Returns: None (La función muestra la visualización directamente usando matplotlib y no retorna valores.)
    """

    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 10))
    # Construir diccionario de posiciones a partir de las coordenadas de los nodos
    pos = {}
    for node, data in mapa.nodes(data=True):
        pos[node] = (data["x"], data["y"])

    # Dibujar el mapa base completo (todas las calles)
    nx.draw_networkx(
        mapa,
        pos=pos,
        with_labels=False,
        node_size=0,  # Ocultar nodos para mejor visualización de calles
        arrows=False,  # No mostrar dirección en las aristas
        width=0.3,  # Líneas delgadas para el mapa base
        edge_color="b",  # Color azul para el mapa base
    )

    # Superponer el camino resaltado encima del mapa base
    nx.draw_networkx_edges(
        camino,
        pos=pos,
        arrows=False,
        width=1,  # Línea más gruesa para destacar el camino
        edge_color="red",  # Color rojo para resaltar la ruta
    )

    # Mostrar el gráfico
    plt.axis("equal")
    plt.show()
    plt.close()
