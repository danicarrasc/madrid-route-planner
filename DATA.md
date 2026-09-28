# Datos para la navegación por Madrid

Los datos externos se mantienen fuera del historial Git. La demo y las pruebas
usan grafos sintéticos y funcionan sin estos archivos.

## Direcciones

1. Abrir el [callejero oficial del Ayuntamiento de Madrid](https://datos.madrid.es/dataset/213605-0-callejero-oficial-madrid/downloads).
2. Descargar **Relación de direcciones vigentes, con coordenadas** en CSV.
3. Guardarlo como `direcciones.csv` junto a `gps.py`.

El lector espera separador `;`, Latin-1 y estas columnas: `VIA_CLASE`, `VIA_PAR`,
`VIA_NOMBRE`, `NUMERO`, `LATITUD`, `LONGITUD`. Las coordenadas deben expresarse
como `40°30'0'' N`. Si el portal cambia el formato, habrá que adaptar la carga.
La estructura publicada coincide con la del CSV usado en la práctica, pero no
se ha verificado que la descarga vigente sea idéntica a aquella copia.

Fuente: Ayuntamiento de Madrid, conjunto «Callejero oficial del Ayuntamiento
de Madrid». Consulta sus condiciones de reutilización en el portal. Si ya se
dispone del CSV original de la práctica, puede copiarse aquí para uso local.

## Red viaria

Al ejecutar `gps.py`, OSMnx carga `madrid.graphml` si existe. Si falta,
descarga la red de conducción de Madrid desde OpenStreetMap y la guarda;
esta operación requiere conexión y puede tardar. También se puede copiar el
GraphML original de la práctica para reproducir aquella red sin descargarla.

© colaboradores de OpenStreetMap. Datos bajo ODbL:
[atribución y condiciones](https://www.openstreetmap.org/copyright).
Las futuras descargas pueden producir rutas distintas por cambios en la red.
