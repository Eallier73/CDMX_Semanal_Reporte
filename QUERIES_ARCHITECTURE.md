# Centralizacion de Queries - Mapa Visual

Guía visual de dónde se encuentran las queries y cómo se conectan los archivos para el monitoreo de CDMX.

## Arquitectura

```text
CDMX_Semanal_Reporte/
│
├── Scripts/
│   ├── orquestador_general.py  <- Importa de queries_config.py
│   ├── queries_config.py           <- Archivo central de queries
│   │   ├── YOUTUBE_*
│   │   ├── TWITTER_*
│   │   ├── MEDIOS_*
│   │   └── FACEBOOK_*
│   ├── 1_extractors_youtube.py
│   ├── 2_extractors_twitter.py
│   ├── 3_extractors_medios.py
│   ├── 4_extractors_facebook_posts.py
│   └── 5_extractors_facebook_comentarios.py
│
└── QUERIES_CONFIG_GUIDE.md
```

## Flujo

```text
Usuario modifica Scripts/queries_config.py
            ↓
Orquestador importa configuración
            ↓
Construye comandos con queries actualizadas
            ↓
Extractores descargan información
```

## Configuración CDMX actual

### YouTube

```python
YOUTUBE_CHANNELS = [
    "GobCDMX",
    "ClaraBrugadaM",
]

YOUTUBE_SEARCH_QUERIES = [
    "jefa de gobierno",
    "clara brugada",
    "cdmx",
    "ciudad de mexico",
    "gobierno de CDMX",
    "gobierno de la ciudad de mexico",
]
```

### Twitter/X

```python
TWITTER_SEARCH_QUERIES = [
    "from:ClaraBrugadaM",
    "from:GobCDMX",
    "jefa de gobierno",
    "clara brugada",
    "cdmx",
    "ciudad de mexico",
    "gobierno de CDMX",
    "gobierno de la ciudad de mexico",
]
```

### Medios

```python
MEDIOS_SITES = [
    "site:www.milenio.com",
    "site:www.jornada.com.mx",
]

MEDIOS_SEARCH_TERMS = [
    '"clara brugada"',
    '"jefa de gobierno"',
    '"gobierno de cdmx"',
    '"ciudad de mexico"',
]
```

### Facebook

```python
FACEBOOK_PAGES = [
    "GobiernoCDMX",
    "ClaraBrugadaM",
]
```
