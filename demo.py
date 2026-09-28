"""Compara los criterios en una red sintética sin datos externos ni interfaz."""
import networkx as nx
import grafo_pesado as grafos


def main():
    red = nx.DiGraph()
    # La ruta corta es lenta; la rápida atraviesa más intersecciones.
    tramos = [
        ('Origen', 'Calle local', 100, 2),
        ('Calle local', 'Destino', 100, 2),
        ('Origen', 'Cruce 1', 100, 10),
        ('Cruce 1', 'Cruce 2', 100, 10),
        ('Cruce 2', 'Destino', 100, 10),
        ('Origen', 'Destino', 400, 10),
    ]
    for origen, destino, longitud, velocidad in tramos:
        red.add_edge(origen, destino, length=longitud, maxspeed=velocidad)

    print('Comparación de rutas en una red sintética\n')
    for nombre, coste in [
        ('Menor distancia', grafos.ruta_corta),
        ('Menor tiempo de circulación', grafos.ruta_rapida),
        ('Menor tiempo con esperas', grafos.ruta_optima),
    ]:
        ruta = grafos.camino_minimo(red, coste, 'Origen', 'Destino')
        aristas = list(zip(ruta, ruta[1:]))
        distancia = sum(grafos.ruta_corta(red, u, v) for u, v in aristas)
        circulacion = sum(grafos.ruta_rapida(red, u, v) for u, v in aristas)
        espera = max(0, len(ruta) - 2) * grafos.ESPERA_MEDIA_INTERSECCION_S
        print(nombre + ': ' + ' -> '.join(ruta))
        print(f'  {distancia:.0f} m | circulación: {circulacion:.0f} s | '
              f'espera modelada: {espera:.0f} s | total con espera: {circulacion + espera:.0f} s\n')


if __name__ == '__main__':
    main()
