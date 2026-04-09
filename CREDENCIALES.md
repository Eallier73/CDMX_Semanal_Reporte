# Configuración de credenciales y estado local

Este repo usa dos tipos de secretos locales:

- Variables de entorno en `.env.local`
- Un `storage_state` local para X/Twitter en `state/x_state.json`

Ambos están ignorados por Git. La plantilla versionada es `.env.example`.

## Archivos relevantes

```text
CDMX_Semanal_Reporte/
├── .env.example          ← plantilla versionada
├── .env.local            ← secretos reales, ignorado por Git
└── state/
    ├── x_state.example.json
    └── x_state.json      ← login real de X/Twitter, ignorado por Git
```

## Credenciales requeridas

### `.env.local`

Crea el archivo a partir de la plantilla:

```bash
cp .env.example .env.local
```

Contenido esperado:

```env
YOUTUBE_API_KEY=tu_youtube_api_key
APIFY_TOKEN=tu_apify_token
YT_PROXY_HTTP=
YT_PROXY_HTTPS=
CLAUDE_API_KEY=tu_claude_api_key
```

Uso por pipeline:

- `YOUTUBE_API_KEY`: pipeline `1`
- `APIFY_TOKEN`: pipelines `4` y `5`
- `CLAUDE_API_KEY`: pipelines `7` y `10`
- `YT_PROXY_HTTP` y `YT_PROXY_HTTPS`: opcionales para `1`

### `state/x_state.json`

El pipeline `2` no usa API key. Usa una sesión local de X/Twitter guardada en:

```text
state/x_state.json
```

Ese archivo debe contener un `storage_state` válido de Playwright. `state/x_state.example.json` es solo referencia estructural.

Uso por pipeline:

- `state/x_state.json`: pipeline `2`

## Dónde obtener cada credencial

### YouTube API

1. Entra a [Google Cloud Console](https://console.developers.google.com/).
2. Crea o selecciona un proyecto.
3. Habilita `YouTube Data API v3`.
4. Genera una API key.
5. Guárdala como `YOUTUBE_API_KEY`.

### Apify

1. Entra a [Apify Console](https://my.apify.com/account/integrations/api).
2. Copia tu token personal.
3. Guárdalo como `APIFY_TOKEN`.

### Claude / Anthropic

1. Entra a [Anthropic Console](https://console.anthropic.com/).
2. Genera o copia tu API key.
3. Guárdala como `CLAUDE_API_KEY`.

### X/Twitter `storage_state`

1. Inicia sesión manualmente en X/Twitter con Playwright o con el flujo que uses internamente.
2. Exporta el `storage_state`.
3. Guarda el archivo como `state/x_state.json`.

## Verificación rápida

### Verificar presencia de variables

```bash
python3 - <<'PY'
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(".env.local")
for name in ["YOUTUBE_API_KEY", "APIFY_TOKEN", "CLAUDE_API_KEY", "YT_PROXY_HTTP", "YT_PROXY_HTTPS"]:
    print(f"{name}: {'OK' if os.getenv(name) else 'VACIO'}")
print(f"state/x_state.json: {'OK' if Path('state/x_state.json').exists() else 'FALTA'}")
PY
```

### Verificar que Git no los versiona

```bash
git check-ignore -v .env.local state/x_state.json
```

## Seguridad

- No guardes secretos reales en `README.md`, `CREDENCIALES.md` ni en ejemplos commiteados.
- `.env.local` está ignorado por `.gitignore`.
- `state/x_state.json` está ignorado por `.gitignore`.
- `.env.example` debe contener solo placeholders.

## Dependencias relacionadas

Para cargar `.env.local`, el repo usa `python-dotenv`.

Instalación recomendada:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
playwright install chromium
```

## Resumen operativo

- Si vas a correr `1`: necesitas `YOUTUBE_API_KEY`
- Si vas a correr `2`: necesitas `state/x_state.json`
- Si vas a correr `4` o `5`: necesitas `APIFY_TOKEN`
- Si vas a correr `7` o `10`: necesitas `CLAUDE_API_KEY`
- Si corres `all`: necesitas todo lo anterior
