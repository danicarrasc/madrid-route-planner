# Planificador de rutas en Madrid

Proyecto académico de Matemática Discreta, Grado en Ingeniería Matemática e
Inteligencia Artificial (ICAI, Universidad Pontificia Comillas, 2025-2026).
Autores: **Daniel Carrasco Jurado y Alejandro Corredera Bote**, a partir de las
interfaces y materiales proporcionados por la asignatura.

Implementación de Dijkstra, Prim y Kruskal en Python, con una aplicación sobre
el grafo de calles de Madrid. El objetivo es explorar cómo la representación
de los datos y la función de coste determinan la solución.

## Funcionalidades

- Dijkstra con cola de prioridad y reconstrucción del camino mínimo.
- Prim y Kruskal para árboles o bosques abarcadores mínimos; son utilidades
  independientes y no intervienen en la navegación.
- Búsqueda de direcciones con autocompletado, instrucciones de giro y mapa.
- Rutas por distancia, tiempo de circulación o tiempo con esperas.
- Gestión de destinos inalcanzables, direcciones inexistentes y datos inválidos.

## Demostración rápida sin descargas de datos

```powershell
python -m pip install -r requirements-core.txt
python demo.py
```

La demostración compara los tres criterios sobre una red sintética pequeña.
No necesita el callejero, conexión a OpenStreetMap ni una ventana gráfica.

## Instalación y ejecución

Usar **Python 3.11 o 3.12** con las dependencias indicadas. Desde esta carpeta,
en PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe gps.py
```

Para navegar por Madrid, sigue primero [las instrucciones de datos](DATA.md).
Los archivos de datos no se incluyen en este repositorio.

El programa busca `direcciones.csv` y `madrid.graphml` junto a los módulos,
independientemente del directorio de ejecución. El CSV requiere columnas
`VIA_CLASE`, `VIA_PAR`, `VIA_NOMBRE`, `NUMERO`, `LATITUD` y `LONGITUD`,
separador `;`, codificación Latin-1 y coordenadas en grados, minutos y segundos.
Si falta el grafo, OSMnx intenta descargarlo de OpenStreetMap y guardarlo.
El CSV no se descarga automáticamente.

Introducir una dirección como `Calle de Alberto Aguilera, 23`, seleccionar
un destino y elegir el criterio. Enter en una dirección finaliza la aplicación.

## Modelo matemático

La red es un grafo dirigido. Las aristas representan tramos transitables y los
nodos aproximan intersecciones y extremos de vías. Se conservan los sentidos de
circulación y se escoge la mejor arista paralela para el criterio activo.

| Modo | Coste por arista |
|---|---|
| Distancia | Longitud en metros |
| Tiempo | Longitud / velocidad, en segundos |
| Tiempo con esperas | Longitud / velocidad + 24 segundos |

La espera media de **24 segundos** (`0.8 × 30`) por intersección es una
simplificación deliberada: no utiliza semáforos reales ni tráfico en directo.
El coste aditivo cobra al llegar a cada nodo. Cobrar también en el destino
añade la misma constante a todas las rutas entre los mismos extremos y no
altera el óptimo. El resumen excluye esa espera final y separa el tiempo de
circulación de las esperas en los nodos interiores.

Las velocidades se estiman por categoría de vía; no son límites legales
verificados. Las direcciones se aproximan al nodo más cercano y los giros
se estiman a partir de coordenadas de nodos. No se modelan restricciones
de giro ni todos los detalles geométricos. Es una demostración de algoritmos,
no un navegador para conducción real.

## Organización

| Archivo | Responsabilidad |
|---|---|
| `grafo_pesado.py` | Algoritmos y funciones de coste |
| `callejero.py` | Direcciones, normalización y visualización |
| `gps.py` | Interacción e instrucciones de navegación |
| `demo.py` | Comparación reproducible de los tres criterios |
| `test_grafo.py` | Regresiones y comparación con NetworkX |

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -p "test_*.py" -v
```

Las pruebas usan grafos pequeños con semillas fijas y datos sintéticos; no
descargan mapas ni abren ventanas. Comparan caminos y bosques con NetworkX y
comprueban unidades, esperas, sentidos, aristas paralelas y errores.

## Datos y atribución

Red viaria: © colaboradores de [OpenStreetMap](https://www.openstreetmap.org/copyright).
Las fuentes y pasos para obtener los datos están en [DATA.md](DATA.md).
La memoria académica original no se incluye: este README documenta la versión
actual del código y sus supuestos.

## Validación

La preparación local supera las 15 pruebas de `unittest`, ejecutadas con Python
3.12, NetworkX 3.5 y pandas 3.0.1. También se contrastaron los tres criterios con
NetworkX en una ruta del mapa de Madrid de 31.362 nodos y 61.690 aristas originales.
La instalación completa desde cero y la interfaz gráfica no se han validado en
esta preparación. El workflow de GitHub ejecutará las pruebas al publicar.
