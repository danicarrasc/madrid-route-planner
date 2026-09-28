"""
grafo_pesado.py

Matemática Discreta - IMAT
ICAI, Universidad Pontificia Comillas

Grupo: GP17A
Integrantes:
    - Daniel Carrasco Jurado
    - Alejandro Corredera Bote

Descripción:
Librería para el análisis de grafos pesados.
"""

from typing import List, Tuple, Dict, Callable, Union
import networkx as nx
from math import isfinite

import heapq  # Librería para la creación de colas de prioridad

INFTY = float("inf")
ESPERA_MEDIA_INTERSECCION_S = 0.8 * 30


def _validar_grafo(G, peso, *, dijkstra=False):
    """Los algoritmos trabajan con grafos simples y pesos reales finitos."""
    if G.is_multigraph():
        raise nx.NetworkXNotImplemented("Reduzca primero las aristas paralelas.")
    if not dijkstra and G.is_directed():
        raise nx.NetworkXNotImplemented("Prim y Kruskal requieren un grafo no dirigido.")
    for u, v in G.edges:
        valor = peso(G, u, v)
        if not isfinite(valor) or (dijkstra and valor < 0):
            raise ValueError("Los pesos deben ser finitos y, para Dijkstra, no negativos.")

"""
En las siguientes funciones, las funciones de peso son funciones que reciben un grafo o digrafo y dos vértices y devuelven un real (su peso)
Por ejemplo, si las aristas del grafo contienen en sus datos un campo llamado 'valor', una posible función de peso sería:

def mi_peso(G:nx.Graph,u:object, v:object):
    return G[u][v]['valor']

y, en tal caso, para calcular Dijkstra con dicho parámetro haríamos

camino=dijkstra(G,mi_peso,origen, destino)


"""


def dijkstra(
    G: Union[nx.Graph, nx.DiGraph],
    peso: Union[
        Callable[[nx.Graph, object, object], float],
        Callable[[nx.DiGraph, object, object], float],
    ],
    origen: object,
) -> Dict[object, object]:
    """
    Calcula un Árbol de Caminos Mínimos para el grafo pesado partiendo
    del vértice "origen" usando el algoritmo de Dijkstra. Calcula únicamente
    el árbol de la componente conexa que contiene a "origen".

    Args:
        origen (object): vértice del grafo de origen
    Returns:
        Dict[object,object]: Devuelve un diccionario que indica, para cada vértice alcanzable
            desde "origen", qué vértice es su padre en el árbol de caminos mínimos.
            La raíz y los nodos inalcanzables tienen padre None.
    Raises:
        TypeError: Si origen no es "hashable".
        nx.NodeNotFound: Si el origen no pertenece al grafo.
        ValueError: Si hay pesos negativos o no finitos.
    Example:
        Si G.dijksra(1)={2:1, 3:2, 4:1} entonces 1 es padre de 2 y de 4 y 2 es padre de 3.
        En particular, un camino mínimo desde 1 hasta 3 sería 1->2->3.
    """
    if origen not in G:
        raise nx.NodeNotFound(f"El origen {origen!r} no pertenece al grafo.")
    _validar_grafo(G, peso, dijkstra=True)
    # creamos los diccionarios
    padre = {}
    visitado = {}
    d = {}

    # Configuración inicial para cada vértice del grafo
    for nodo in G:
        padre[nodo] = None  # Inicialmente sin padre asignado
        visitado[nodo] = False  # Marcar como no visitado
        d[nodo] = INFTY  # Distancia inicial infinita

    # Establecer la distancia del origen a 0
    d[origen] = 0

    # Inicializar la cola de prioridad con el vértice origen
    Q = []
    contador = 0  # Para manejar empates en la prioridad
    heapq.heappush(Q, (0, contador, origen))

    # Procesar mientras haya vértices en la cola
    while Q:
        # Extraer el vértice con la menor distancia acumulada
        _, _, v = heapq.heappop(Q)

        # Procesar solo si no ha sido visitado
        if not visitado[v]:
            visitado[v] = True  # Marcar como visitado

            # Examinar todos los vértices adyacentes al actual
            for x in G[v]:
                # Obtener el peso de la arista entre v y x
                w = peso(G, v, x)

                # Realizar relajación si se encuentra un camino más corto
                if d[x] > d[v] + w:
                    d[x] = d[v] + w  # Actualizar la distancia mínima
                    padre[x] = v  # Registrar el padre en el camino más corto
                    contador += 1
                    # Insertar en la cola con la nueva distancia
                    heapq.heappush(Q, (d[x], contador, x))

    return padre  # Devuelve el diccionario de predecesores


def camino_minimo(
    G: Union[nx.Graph, nx.DiGraph],
    peso: Union[
        Callable[[nx.Graph, object, object], float],
        Callable[[nx.DiGraph, object, object], float],
    ],
    origen: object,
    destino: object,
) -> List[object]:
    """
    Calcula el camino mínimo desde el vértice origen hasta el vértice
    destino utilizando el algoritmo de Dijkstra.

    Args:
        G (nx.Graph o nx.Digraph): grafo a grado dirigido
        peso (función): función que recibe un grafo o grafo dirigido y dos vértices del mismo y devuelve el peso de la arista que los conecta
        origen (object): vértice del grafo de origen
        destino (object): vértice del grafo de destino
    Returns:
        List[object]: Devuelve una lista con los vértices del grafo por los que pasa
            el camino más corto entre el origen y el destino. El primer elemento de
            la lista es origen y el último destino.
    Example:
        Si dijksra(G,peso,1,4)=[1,5,2,4] entonces el camino más corto en G entre 1 y 4 es 1->5->2->4.
    Raises:
        TypeError: Si origen o destino no son "hashable".
        nx.NodeNotFound: Si falta alguno de los extremos.
        nx.NetworkXNoPath: Si el destino es inalcanzable.
    """
    if destino not in G:
        raise nx.NodeNotFound(f"El destino {destino!r} no pertenece al grafo.")
    # Obtener el árbol mediante dijkstra
    diccionario_padres = dijkstra(G, peso, origen)
    if destino != origen and diccionario_padres[destino] is None:
        raise nx.NetworkXNoPath(f"No existe una ruta de {origen!r} a {destino!r}.")

    # Inicializar la lista conteniendo únicamente el destino
    camino = [destino]

    # Bucle para analizar los padres de cada nodo hasta llegar al origen
    nodo = destino
    while origen != nodo:
        # Cambiar el nodo por el padre y meterlo en el camino, antes de su hijo
        nodo = diccionario_padres[nodo]
        camino.append(nodo)

    camino.reverse()
    return camino


def prim(
    G: nx.Graph, peso: Callable[[nx.Graph, object, object], float]
) -> Dict[object, object]:
    """
    Calcula un Árbol Abarcador Mínimo para el grafo pesado
    usando el algoritmo de Prim.

    Args: None
    Returns:
        G (nx.Graph): grafo
        peso (función): función que recibe un grafo y dos vértices del grafo y devuelve el peso de la arista que los conecta
        Dict[object,object]: Devuelve un diccionario que indica, para cada vértice del
            grafo, qué vértice es su padre en el árbol abarcador mínimo.
    Raises: None
    Example:
        Si prim(G,peso)={1: None, 2:1, 3:2, 4:1} entonces en un árbol abarcador mínimo tenemos que:
            1 es una raíz (no tiene padre)
            1 es padre de 2 y de 4
            2 es padre de 3
    """
    _validar_grafo(G, peso)
    # Inicialización de estructuras de datos
    vertices = list(G.nodes)
    padre = {}  # Almacena el padre de cada nodo en el MST
    coste_minimo = {}  # Almacena el costo mínimo para conectar cada nodo al MST
    en_q = set(vertices)  # Conjunto de nodos aún no incluidos en el MST
    heap = []  # Cola de prioridad (min-heap) para seleccionar el próximo nodo
    contador = 0  # Contador para garantizar orden estable en el heap

    # Inicializar todos los nodos con costo infinito y sin padre
    for v in vertices:
        padre[v] = None
        coste_minimo[v] = float("inf")
        # Usamos tupla (costo, contador, nodo) para evitar comparaciones entre tipos diferentes
        heapq.heappush(heap, (coste_minimo[v], contador, v))
        contador += 1

    # Procesar nodos hasta que la cola esté vacía
    while heap:
        # Extraer el nodo con el costo mínimo actual
        coste, _, v = heapq.heappop(heap)

        # Verificar si esta entrada del heap está actualizada
        if coste != coste_minimo[v]:
            continue  # Entrada obsoleta, ignorar

        # Si el nodo ya fue procesado, saltar
        if v not in en_q:
            continue

        # Marcar nodo como incluido en el MST
        en_q.remove(v)

        # Examinar todos los vecinos del nodo actual que aún no están en el MST
        for x in G.neighbors(v):
            if x not in en_q:
                continue

            # Calcular peso de la arista entre v y x
            w_vx = peso(G, v, x)

            # Si encontramos una conexión más barata al vecino, actualizar
            if w_vx < coste_minimo[x]:
                coste_minimo[x] = w_vx
                padre[x] = v
                # Agregar nueva entrada al heap (no podemos actualizar existentes directamente)
                heapq.heappush(heap, (coste_minimo[x], contador, x))
                contador += 1

    return padre


def kruskal(
    G: nx.Graph, peso: Callable[[nx.Graph, object, object], float]
) -> List[Tuple[object, object]]:
    """Calcula un Árbol Abarcador Mínimo para el grafo
    usando el algoritmo de Kruskal.

    Args:
        G (nx.Graph): grafo
        peso (función): función que recibe un grafo y dos vértices del grafo y devuelve el peso de la arista que los conecta
    Returns:
        List[Tuple[object,object]]: Devuelve una lista [(s1,t1),(s2,t2),...,(sn,tn)]
            de los pares de vértices del grafo que forman las aristas
            del arbol abarcador mínimo.
    Raises: None
    Example:
        En el ejemplo anterior en que prim(G,peso)={1:None, 2:1, 3:2, 4:1} podríamos tener, por ejemplo,
        kruskal(G,peso)=[(1,2),(1,4),(3,2)]
    """
    _validar_grafo(G, peso)
    aristas_aam = []
    # Crear lista de aristas ordenada por peso
    aristas = list(G.edges())
    L = sorted(aristas, key=lambda arista: peso(G, arista[0], arista[1]))

    # Inicializar componentes: cada nodo en su propia componente
    C = {}
    for v in G.nodes():
        C[v] = {v}

    # Procesar aristas en orden de menor a mayor peso
    for a in L:
        u, v = a
        if C[u] != C[v]:
            aristas_aam.append((u, v))
            # Unir las componentes de u y v
            componente_u = C[u]
            componente_v = C[v]
            nueva_componente = componente_u.union(componente_v)
            for nodo in nueva_componente:
                C[nodo] = nueva_componente

    return aristas_aam


# Funciones de Peso y un diccionario que las almacena
def ruta_corta(G, u, v):
    """Longitud en metros; respeta el sentido de circulación."""
    longitud = G[u][v]["length"]
    if not isfinite(longitud) or longitud < 0:
        raise ValueError("La longitud debe ser finita y no negativa.")
    return longitud


def ruta_rapida(G, u, v):
    """Tiempo de circulación en segundos, con velocidad expresada en m/s."""
    velocidad = G[u][v]["maxspeed"]
    if not isfinite(velocidad) or velocidad <= 0:
        raise ValueError("La velocidad debe ser finita y positiva.")
    return ruta_corta(G, u, v) / velocidad


def ruta_optima(G, u, v):
    """Tiempo más espera media por llegada a un nodo (modelo de intersecciones).

    Se cobra también en el destino: es una constante común a todas las rutas
    entre los mismos extremos y no cambia qué camino minimiza el coste.
    El resumen de viaje excluye esa espera final.
    """
    return ruta_rapida(G, u, v) + ESPERA_MEDIA_INTERSECCION_S


MODOS = {1: ruta_corta, 2: ruta_rapida, 3: ruta_optima}
