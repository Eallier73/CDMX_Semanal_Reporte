# Configuración Centralizada de Queries

Este documento explica cómo gestionar las queries y parámetros de los extractores desde un único archivo.

## Ubicación

Scripts/queries_config.py

## Configuración actual para CDMX

### YouTube

- Canales: GobCDMX, ClaraBrugadaM
- Queries:
  - jefa de gobierno
  - clara brugada
  - cdmx
  - ciudad de mexico
  - gobierno de CDMX
  - gobierno de la ciudad de mexico

### Twitter/X

- Queries institucionales:
  - from:ClaraBrugadaM
  - from:GobCDMX
- Queries de conversación/comentarios:
  - jefa de gobierno
  - clara brugada
  - cdmx
  - ciudad de mexico
  - gobierno de CDMX
  - gobierno de la ciudad de mexico

### Facebook

- Páginas:
  - GobiernoCDMX
  - ClaraBrugadaM

### Medios

- Sitios:
  - https://www.milenio.com/
  - https://www.jornada.com.mx/
- Términos:
  - "clara brugada"
  - "jefa de gobierno"
  - "gobierno de cdmx"
  - "ciudad de mexico"

## Cómo usar en los extractores

Importa desde Scripts/queries_config.py y asigna defaults desde ahí.

Ejemplo:

from queries_config import TWITTER_SEARCH_QUERIES

DEFAULT_SEARCH_QUERIES = TWITTER_SEARCH_QUERIES

## Ver configuración en JSON

python Scripts/queries_config.py

## Flujo recomendado

1. Modificar Scripts/queries_config.py
2. Guardar cambios
3. Ejecutar el orquestador
4. Validar salidas semanales
