"""
gps.py

Matemática Discreta - IMAT
ICAI, Universidad Pontificia Comillas

Grupo: GP17A
Integrantes:
    - Daniel Carrasco Jurado
    - Alejandro Corredera Bote

Descripción:
Programa principal que calcula una ruta entre 2 localizaciones
"""

import callejero, grafo_pesado
import networkx as nx
from math import atan2, degrees

from typing import Tuple, Callable, List


def obtener_parametros_ruta(df, G, opciones_direcciones) -> Tuple[int | None, int | None, Callable | None]:
    """
    Función que mediante inputs del usuario, devuelve el ID del nodo de origen y el destino del viaje, y
    la función de peso que el usuario haya elegido usar en función de que tipo de ruta escoja

    Args: None

    Returns:
        int (origen): ID del nodo de origen
        int (destino): ID del nodo de destino
        function: Función de peso

    Raises: None
    """

    import osmnx as ox
    from prompt_toolkit import prompt
    from prompt_toolkit.completion import WordCompleter

    def _pedir_direccion(opciones_direcciones: List, destino=False) -> int | None:
        """
        Pide una dirección al usuario usando autocompletado en tiempo real
        y devuelve el ID del nodo más cercano.
        """
        # Ajustar el mensaje con el que se pedirá la dirección
        mensaje = "destino" if destino else "origen"

        # Crear el autocompletador
        completer = WordCompleter(
            opciones_direcciones,
            ignore_case=True,
            match_middle=True,  # Permite autocompletar escribiendo parte de la palabra
            sentence=True,
        )

        # Pedir una dirección hasta que se introduzca una válida
        while True:
            try:
                direccion = prompt(
                    f"Introduce una dirección de {mensaje} (enter para salir): ",
                    completer=completer,
                )

                if not direccion:
                    return

                lat, lon = callejero.busca_direccion(direccion, df)
                return ox.nearest_nodes(G, lon, lat)

            except (callejero.AddressNotFoundError, ValueError) as e:
                print(f"Error: {e}")
                print("Inténtalo de nuevo.\n")

    def _pedir_modo_ruta() -> int:
        """
        Funcion que se encarga de preguntarle al usuario que tipo de ruta desea escoger y devuelve
        una función de peso acorde.

        Args: None

        Returns: function: La función de peso en cuestión

        Raises: None
        """
        # Printear el menú de opciones
        print("\n" + "=" * 60)
        print("        Selección de modo de cálculo de ruta")
        print("=" * 60)
        print("  1) Ruta más corta (minimiza la distancia)")
        print("  2) Ruta más rápida (minimiza el tiempo)")
        print("  3) Ruta con espera media por intersección (24 s)")
        print("-" * 60)

        # Bucle infinito hasta que el usuario elija una opción válida
        while True:
            modo = input("Elige una opción (1, 2 o 3): ").strip()

            if modo in {"1", "2", "3"}:
                print(f"\nHas seleccionado el modo {modo}\n")
                return int(modo)
            else:
                print("Entrada inválida. Por favor, selecciona 1, 2 o 3.\n")

    # Obtener los ID de los nodos de origen y destino, pero finalizar la ejecución si se devuelven vacios
    origen = _pedir_direccion(opciones_direcciones)
    if origen is None:
        return None, None, None

    destino = _pedir_direccion(opciones_direcciones, True)
    if destino is None:
        return None, None, None

    # Obtener el tipo de ruta y una función de peso acorde
    modo = _pedir_modo_ruta()
    funcion_peso = grafo_pesado.MODOS[modo]

    return origen, destino, funcion_peso


def generar_instrucciones_navegacion(
    G: nx.DiGraph, ruta: List[int], espera_media_s: float = 0.0
) -> List[dict]:
    """
    Genera instrucciones detalladas de navegación para una ruta en un grafo.
    Convierte una secuencia de nodos en instrucciones comprensibles para el usuario.
    """
    # Definir funciones auxiliares

    def _obtener_datos_arista(G: nx.DiGraph, u: int, v: int) -> dict:
        """
        Recupera una arista respetando el sentido del grafo dirigido.
        """
        if not G.has_edge(u, v):
            raise nx.NetworkXNoPath(f"La ruta contiene una arista inexistente: {u!r} -> {v!r}.")
        return G[u][v]


    def _calcular_tipo_giro(
        G: nx.DiGraph, ruta: List[int], indice_interseccion: int
    ) -> str:
        """
        Determina el tipo de giro analizando la geometría del camino.
        Usa coordenadas de nodos consecutivos para calcular ángulos entre segmentos.
        """
        # Verificar que existan nodos suficientes para calcular el giro
        if indice_interseccion < 1 or indice_interseccion >= len(ruta) - 1:
            return "continuar"

        nodo_anterior = ruta[indice_interseccion - 1]
        nodo_interseccion = ruta[indice_interseccion]
        nodo_siguiente = ruta[indice_interseccion + 1]

        # Obtener coordenadas para cálculo vectorial
        coord_anterior = (G.nodes[nodo_anterior]["x"], G.nodes[nodo_anterior]["y"])
        coord_interseccion = (
            G.nodes[nodo_interseccion]["x"],
            G.nodes[nodo_interseccion]["y"],
        )
        coord_siguiente = (G.nodes[nodo_siguiente]["x"], G.nodes[nodo_siguiente]["y"])

        # Calcular vectores de dirección entre nodos
        vec_entrada = (
            coord_interseccion[0] - coord_anterior[0],
            coord_interseccion[1] - coord_anterior[1],
        )
        vec_salida = (
            coord_siguiente[0] - coord_interseccion[0],
            coord_siguiente[1] - coord_interseccion[1],
        )

        # Calcular ángulo entre vectores para determinar tipo de giro
        angulo = _calcular_angulo(vec_entrada, vec_salida)

        # Ajustar ángulo para corrección de dirección
        angulo = -angulo

        # Clasificar el giro según el ángulo calculado
        if abs(angulo) > 150:
            return "para realizar un cambio de sentido"
        elif angulo < -120:
            return "pronunciadamente a la izquierda"
        elif angulo < -60:
            return "a la izquierda"
        elif angulo < -30:
            return "ligeramente hacia la izquierda"
        elif angulo > 120:
            return "pronunciadamente a la derecha"
        elif angulo > 60:
            return "a la derecha"
        elif angulo > 30:
            return "ligeramente hacia la derecha"
        else:
            return "continuar"

    def _calcular_angulo(vec1: tuple, vec2: tuple) -> float:
        """
        Calcula el ángulo en grados entre dos vectores en el plano.
        Usa producto punto y producto cruz para determinar la orientación relativa.
        """
        # Verificar que los vectores no sean nulos
        if vec1 == (0, 0) or vec2 == (0, 0):
            return 0.0

        # Calcular productos vectoriales
        cruz = vec1[0] * vec2[1] - vec1[1] * vec2[0]
        punto = vec1[0] * vec2[0] + vec1[1] * vec2[1]

        # Calcular ángulo usando función arcotangente
        try:
            angulo_rad = atan2(cruz, punto)
            angulo_grados = degrees(angulo_rad)
        except (ValueError, TypeError):
            return 0.0

        return angulo_grados

    from math import isfinite

    if not isfinite(espera_media_s) or espera_media_s < 0:
        raise ValueError("La espera media debe ser finita y no negativa.")
    if not ruta:
        return []
    if any(nodo not in G for nodo in ruta):
        raise nx.NodeNotFound("La ruta contiene nodos ajenos al grafo.")
    if len(ruta) == 1:
        return [
            {"tipo": "destino", "calle": None, "distancia": 0,
             "mensaje": "Origen y destino coinciden; ya has llegado"},
            {"tipo": "resumen", "distancia_total": 0, "tiempo_total": 0,
             "tiempo_circulacion_s": 0, "tiempo_espera_s": 0,
             "mensaje": "Recorrido total: 0 metros, tiempo estimado: 0.0 minutos"},
        ]

    primera = _obtener_datos_arista(G, ruta[0], ruta[1])
    instrucciones = [{"tipo": "inicio", "calle": primera.get("name")}]
    calle_actual = primera.get("name")
    tipo_actual = primera.get("highway")
    distancia_acumulada = distancia_total = tiempo_circulacion_s = 0.0

    for i, (u, v) in enumerate(zip(ruta, ruta[1:])):
        datos = _obtener_datos_arista(G, u, v)
        nombre = datos.get("name")
        giro = _calcular_tipo_giro(G, ruta, i)
        # Agrupar tramos de la misma calle, salvo que haya una maniobra.
        if i > 0 and (nombre != calle_actual or giro != "continuar"):
            instrucciones.append({
                "tipo": "navegacion", "calle_actual": calle_actual,
                "distancia": round(distancia_acumulada), "siguiente_calle": nombre,
                "giro": giro, "es_autopista": tipo_actual == "motorway",
            })
            distancia_acumulada = 0.0
        longitud = grafo_pesado.ruta_corta(G, u, v)
        distancia_total += longitud
        distancia_acumulada += longitud
        tiempo_circulacion_s += grafo_pesado.ruta_rapida(G, u, v)
        calle_actual, tipo_actual = nombre, datos.get("highway")

    instrucciones.append({
        "tipo": "destino", "calle": calle_actual,
        "distancia": round(distancia_acumulada), "mensaje": "Has llegado a tu destino",
    })
    # Los nodos interiores representan las intersecciones atravesadas.
    tiempo_espera_s = max(0, len(ruta) - 2) * espera_media_s
    tiempo_min = (tiempo_circulacion_s + tiempo_espera_s) / 60
    instrucciones.append({
        "tipo": "resumen", "distancia_total": distancia_total,
        "tiempo_total": tiempo_min, "tiempo_circulacion_s": tiempo_circulacion_s,
        "tiempo_espera_s": tiempo_espera_s,
        "mensaje": (f"Recorrido total: {distancia_total:.0f} metros, "
                    f"tiempo estimado: {tiempo_min:.1f} minutos "
                    f"(espera modelada: {tiempo_espera_s:.0f} s)"),
    })
    return instrucciones


def formatear_instrucciones(instrucciones: List[dict]) -> List[str]:
    """
    Convierte las instrucciones estructuradas en texto legible para el usuario.
    Adapta el mensaje según el contexto (autopista, distancias cortas, etc.)
    """
    texto_instrucciones = []

    for i, instruccion in enumerate(instrucciones, start=1):
        if instruccion["tipo"] == "inicio":
            # Mensaje simple para inicio del recorrido
            calle = instruccion["calle"]
            mensaje = (
                f"{i}. Inicie el recorrido en {calle}"
                if calle
                else f"{i}. Inicie el recorrido"
            )
            texto_instrucciones.append(mensaje)

        elif instruccion["tipo"] == "navegacion":
            # Preparar datos para la instrucción de navegación
            calle_actual = instruccion["calle_actual"]
            siguiente_calle = instruccion["siguiente_calle"]
            distancia = instruccion["distancia"]
            giro = instruccion["giro"]
            es_autopista = instruccion["es_autopista"]

            # Construir mensaje según el contexto
            if calle_actual and siguiente_calle:
                # Instrucción estándar
                if es_autopista:
                    texto = (
                        f"{i}. Continúe por {calle_actual} durante {distancia} metros, "
                        f"luego tome la salida"
                    )
                else:
                    if giro == "continuar":
                        texto = (
                            f"{i}. Continúe por {calle_actual} durante {distancia} metros, "
                            f"luego tome {siguiente_calle}"
                        )
                    else:
                        texto = (
                            f"{i}. Continúe por {calle_actual} durante {distancia} metros, "
                            f"luego gire {giro} por {siguiente_calle}"
                        )

            elif not calle_actual and siguiente_calle:
                # Instrucción para calles sin nombre
                if es_autopista:
                    texto = (
                        f"{i}. Continúe durante {distancia} metros, "
                        f"luego tome la salida"
                    )
                else:
                    if giro == "continuar":
                        texto = (
                            f"{i}. Continúe durante {distancia} metros, "
                            f"luego tome {siguiente_calle}"
                        )
                    else:
                        texto = (
                            f"{i}. Continúe  durante {distancia} metros, "
                            f"luego gire {giro} por {siguiente_calle}"
                        )

            elif calle_actual and not siguiente_calle:
                # Instrucción cuando la siguiente calle no tiene nombre
                if es_autopista:
                    texto = (
                        f"{i}. Continúe por {calle_actual} durante {distancia} metros, "
                        f"luego tome la salida"
                    )
                else:
                    if giro == "continuar":
                        texto = (
                            f"{i}. Continúe por {calle_actual} durante {distancia} metros, "
                            f"luego siga recto"
                        )
                    else:
                        texto = (
                            f"{i}. Continúe por {calle_actual} durante {distancia} metros, "
                            f"luego gire {giro}"
                        )

            else:
                # Instrucción cuando ni esta calle ni la siguiente tienen tombre
                if es_autopista:
                    texto = (
                        f"{i}. Continúe durante {distancia} metros, "
                        f"luego tome la salida"
                    )
                else:
                    if giro == "continuar":
                        texto = (
                            f"{i}. Continúe durante {distancia} metros, "
                            f"luego siga recto"
                        )
                    else:
                        texto = (
                            f"{i}. Continúe durante {distancia} metros, "
                            f"luego gire {giro}"
                        )

            texto_instrucciones.append(texto)

        elif instruccion["tipo"] == "destino":
            # Mensaje de llegada al destino
            calle = instruccion["calle"]
            distancia = instruccion["distancia"]

            ubicacion = f" en {calle}" if calle else ""
            recorrido = f" después de {distancia} metros" if distancia > 0 else ""
            texto = f"{i}. {instruccion['mensaje']}{ubicacion}{recorrido}"
            texto_instrucciones.append(texto)

        elif instruccion["tipo"] == "resumen":
            # Resumen final del recorrido
            texto_instrucciones.append("-" * 60)
            texto_instrucciones.append(instruccion["mensaje"])

    return texto_instrucciones


def main():
    """Ejecuta el navegador; los datos se pasan explícitamente, sin globales."""
    try:
        df = callejero.carga_callejero()
        multidigrafo = callejero.carga_grafo()
        grafos = {grafo_pesado.ruta_corta: callejero.procesa_grafo(multidigrafo)}
        opciones = callejero.calcular_posibles_direcciones(df)
        while True:
            origen, destino, peso = obtener_parametros_ruta(
                df, grafos[grafo_pesado.ruta_corta], opciones
            )
            if origen is None or destino is None or peso is None:
                break
            if peso not in grafos:
                grafos[peso] = callejero.procesa_grafo(multidigrafo, peso)
            G = grafos[peso]
            try:
                ruta = grafo_pesado.camino_minimo(G, peso, origen, destino)
            except nx.NetworkXNoPath:
                print("No hay una ruta transitable entre esas direcciones. Prueba otra pareja.")
                continue
            espera = (grafo_pesado.ESPERA_MEDIA_INTERSECCION_S
                      if peso is grafo_pesado.ruta_optima else 0.0)
            instrucciones = generar_instrucciones_navegacion(G, ruta, espera)
            print("\nINSTRUCCIONES DE NAVEGACIÓN\n" + "=" * 60)
            for texto in formatear_instrucciones(instrucciones):
                print(texto)
            if len(ruta) > 1:
                camino = G.edge_subgraph(list(zip(ruta, ruta[1:]))).copy()
                callejero.mostrar_mapa(G, camino)
    except (FileNotFoundError, callejero.ServiceNotAvailableError, ValueError) as error:
        print(f"No se pudo completar la navegación: {error}")
    except (KeyboardInterrupt, EOFError):
        pass
    print("Finalizando ejecución.")


if __name__ == "__main__":
    main()
