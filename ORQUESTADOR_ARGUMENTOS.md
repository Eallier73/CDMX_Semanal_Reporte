# Argumentos del Orquestador

Este documento resume, script por script, qué argumentos conviene pedir desde el orquestador general, qué dependencias existen entre pipelines y cuál es el orden real de ejecución cuando se seleccionan combinaciones parciales.

## Convención de nombres

- `orquestador_general.py`
- `1_extractors_youtube.py`
- `2_extractors_twitter.py`
- `3_extractors_medios.py`
- `4_extractors_facebook_posts.py`
- `5_extractors_facebook_comentarios.py`
- `6_consolidador_datos.py`
- `7_modelado_temas_claude.py`
- `8_influencia_temas.py`
- `9_temas_guiados.py`
- `10_publicaciones_institucionales_claude.py`

## 01 YouTube

- Prompt propio previo: sí, solo para decidir modo de descarga.
- Argumentos clave:
  - `--since`
  - `--before`
  - `--channels`
  - `--queries`
  - `--mode`
  - `--max-videos-query`
  - `--max-videos-channel`
  - `--output-dir`
- Credenciales:
  - `YOUTUBE_API_KEY`
  - `YT_PROXY_HTTP` opcional
  - `YT_PROXY_HTTPS` opcional
- Salidas relevantes:
  - `Youtube/{semana}/{semana}_comentarios.csv`
  - `Youtube/{semana}/{semana}_comentarios.txt`
  - `Youtube/{semana}/{semana}_scripts.csv`
  - `Youtube/{semana}/{semana}_scripts.txt`

## 02 Twitter/X

- Prompt propio previo: no.
- Argumentos clave:
  - `--since`
  - `--before`
  - `--query` repetible
  - `--output-dir`
  - `--state-path`
  - `--max-tweets`
  - `--max-replies-per-tweet`
  - `--max-reply-scrolls`
  - `--no-headless` opcional
- Requisito operativo:
  - `state/x_state.json`
- Salidas relevantes:
  - `Twitter/{semana}/{semana}_post_institucionales.csv`
  - `Twitter/{semana}/{semana}_post_institucionales.txt`
  - `Twitter/{semana}/{semana}_comentarios.csv`
  - `Twitter/{semana}/{semana}_comentarios.txt`

## 03 Medios CDMX

- Prompt propio previo: no.
- Argumentos clave:
  - `--since`
  - `--before`
  - `--medio` repetible
  - `--termino` repetible
  - `--modo-queries`
  - `--output-dir`
  - `--nombre-archivo-base`
  - `--omitir-semanas-existentes`
  - `--pausa`
  - `--pausa-entre-queries`
- Salidas relevantes:
  - `Medios/{semana}/noticias_cdmx_{semana}.csv`
  - `Medios/{semana}/noticias_cdmx_{semana}.txt`

## 04 Facebook Posts

- Prompt propio previo: sí.
- Argumentos clave:
  - `--pages`
  - `--since`
  - `--before`
  - `--max-posts`
  - `--max-pages`
  - `--max-urls`
  - `--sample-percent`
  - `--sample-seed`
  - `--batch-size`
  - `--output-dir`
- Credenciales:
  - `APIFY_TOKEN`
- Salidas relevantes:
  - `Facebook/{semana}/{semana}_posts.csv`
  - `Facebook/{semana}/{semana}_posts.txt`

## 05 Facebook Comentarios

- Prompt propio previo: sí.
- Argumentos clave:
  - `--input-csv`
  - `--max-comments`
  - `--max-urls`
  - `--sample-percent`
  - `--sample-seed`
  - `--since`
  - `--before`
  - `--batch-size`
  - `--output-dir`
- Credenciales:
  - `APIFY_TOKEN`
- Dependencia operativa:
  - Requiere el CSV generado por `4_extractors_facebook_posts.py`
- Salidas relevantes:
  - `Facebook/{semana}/{semana}_comentarios.csv`
  - `Facebook/{semana}/{semana}_comentarios.txt`

## 06 Consolidador de Datos

- Prompt propio previo: no.
- Argumentos clave:
  - `--since`
  - `--before`
  - `--base-dir`
  - `--output-dir`
- Dependencia operativa:
  - Consume los `.txt` generados por extractores de redes y medios
- Salidas relevantes:
  - `Datos/{semana}/material_institucional.txt`
  - `Datos/{semana}/material_comentarios.txt`

## 07 Modelado Temático con Claude

- Prompt propio previo: no.
- Argumentos clave:
  - `--since`
  - `--before`
  - `--input-dir`
  - `--output-dir`
  - `--model`
  - `--max-corpus-chars`
- Credenciales:
  - `CLAUDE_API_KEY`
- Dependencia operativa:
  - Requiere que exista `Datos/{semana}/material_institucional.txt`
  - Requiere que exista `Datos/{semana}/material_comentarios.txt`
- Salidas relevantes:
  - `Claude/{semana}/corpus_claude_*.txt`
  - `Claude/{semana}/analisis_tematico_claude_*.md`
  - `Claude/{semana}/analisis_tematico_claude_*.docx`
  - `Claude/{semana}/metadata_claude_*.json`

## 08 Análisis de Influencia de Temas

- Prompt propio previo: no.
- Argumentos clave:
  - `--since`
  - `--before`
  - `--input-dir`
  - `--output-dir`
  - `--stopwords-path`
- No requiere credenciales.
- Dependencia operativa:
  - Requiere que exista `Datos/{semana}/material_institucional.txt`
  - Requiere que exista `Datos/{semana}/material_comentarios.txt`
  - Se ejecuta típicamente después del pipeline 6
- Salidas relevantes:
  - `Influencia_Temas/{semana}/tecnico/influencia_temas.csv`
  - `Influencia_Temas/{semana}/tecnico/polaridad_documentos.csv`
  - `Influencia_Temas/{semana}/ejecutivo/00_resumen_ejecutivo.md`
  - `Influencia_Temas/{semana}/ejecutivo/01_kpis_polaridad_por_tema.csv`
  - `Influencia_Temas/{semana}/ejecutivo/01b_kpis_polaridad_por_subtema.csv`
  - `Influencia_Temas/{semana}/ejecutivo/02_top_hallazgos_polaridad.csv`
  - `Influencia_Temas/{semana}/ejecutivo/03_alertas_polaridad.csv`

## 09 Análisis de Temas Guiados

- Prompt propio previo: no.
- Argumentos clave:
  - `--since`
  - `--before`
  - `--input-dir`
  - `--output-dir`
  - `--exclude-words-path`
  - `--input-file` opcional
- No requiere credenciales.
- Dependencia operativa:
  - Requiere que exista `Datos/{semana}/material_institucional.txt`
  - Requiere que exista `Datos/{semana}/material_comentarios.txt`
  - Alternativamente se puede usar `--input-file` para forzar un archivo de entrada específico
- Salidas relevantes:
  - `Temas_Guiados/{semana}/clasificacion_temas_guiados_*.csv`
  - `Temas_Guiados/{semana}/distribucion_temas_guiados_*.png`
  - `Temas_Guiados/{semana}/top75_palabras_temas_guiados_*.csv`
  - `Temas_Guiados/{semana}/informe_temas_guiados_*.txt`

## 10 Análisis de Publicaciones Institucionales con Claude

- Prompt propio previo: no.
- Argumentos clave:
  - `--since`
  - `--before`
  - `--twitter-dir`
  - `--facebook-dir`
  - `--youtube-dir`
  - `--datos-dir`
  - `--output-dir`
  - `--model`
  - `--max-corpus-chars`
- Credenciales:
  - `CLAUDE_API_KEY`
- Dependencia operativa:
  - Requiere al menos uno de los CSV institucionales semanales de Twitter/X, Facebook o YouTube
  - Para el análisis comparado completo conviene que existan publicaciones de ambos casos: Gobierno CDMX y Clara Brugada
- Consume principalmente:
  - `Twitter/{semana}/{semana}_post_institucionales.csv`
  - `Facebook/{semana}/{semana}_posts.csv`
  - `Youtube/{semana}/{semana}_scripts.csv`
- Salidas relevantes:
  - `Datos/{semana}/publicaciones_institucionales_redes_*.csv`
  - `Claude/{semana}/prompt_publicaciones_institucionales_*.txt`
  - `Claude/{semana}/corpus_publicaciones_institucionales_*.txt`
  - `Claude/{semana}/analisis_publicaciones_institucionales_*.md`
  - `Claude/{semana}/analisis_publicaciones_institucionales_*.json`
  - `Claude/{semana}/tabla_temas_publicaciones_institucionales_*.csv`
  - `Claude/{semana}/porcentajes_temas_publicaciones_institucionales_*.csv`

## Lógica de selección del orquestador

El orquestador pregunta una vez el contexto temporal global y luego permite dos formas de trabajo:

- Semana ISO: el usuario captura `YYYY-Www` y el orquestador lo convierte a `since/before`.
- Rango explícito: el usuario captura `since` y `before` directamente en formato `YYYY-MM-DD`.

Importante:

- Aunque el rango explícito no corresponda a una semana completa, el resto del pipeline no cambia.
- La lógica semanal de carpetas y nombres sigue calculándose con base en la fecha `since`.

Después de capturar el contexto temporal, el orquestador permite:

- `all`: ejecuta todos los pipelines disponibles.
- Selección parcial: ejecuta solo los pipelines capturados por el usuario.

La ejecución se hace con CLI explícita y, cuando aplica, con `--no-prompt`. Las credenciales sensibles se capturan sin exponerlas en la línea de comandos.

## Dependencias y reordenamientos automáticos

Reglas implementadas por `orquestador_general.py`:

- Si se selecciona `5` sin `4`, el orquestador inserta `4` antes de `5`.
- Si se seleccionan `4` y `5` en cualquier orden, el orquestador fuerza `4` antes de `5`.
- Si se selecciona `7`, `8` o `9` sin `6`, el orquestador inserta `6` antes del pipeline dependiente.
- Si `6` ya está seleccionado pero después de `7`, `8` o `9`, el orquestador lo reordena para que corra antes.
- Si se selecciona `10` junto con `1`, `2` o `4`, el orquestador mueve `10` después de esos productores.
- Si se selecciona solo `10`, el orquestador no agrega extractores automáticamente.

Importante:

- El pipeline `10` no altera a los extractores ni sustituye al pipeline `6`.
- Existen dos flujos distintos:
  - `6 -> 7/8/9` para análisis basados en materiales `.txt`
  - `1/2/4 -> 10` para análisis comparado de publicaciones institucionales en CSV

## Ejemplos de selección

Estos ejemplos corresponden a lo que el usuario captura en el prompt `Selecciona pipelines`:

- `all`
  - Ejecuta los pipelines del 1 al 10.
- `1,2,4`
  - Ejecuta solo extractores institucionales de YouTube, Twitter/X y Facebook posts.
- `4,5`
  - Ejecuta posts y luego comentarios de Facebook.
- `5,4`
  - El orquestador reordena y ejecuta `4` antes de `5`.
- `7`
  - El orquestador inserta `6` antes de `7`.
- `8,9`
  - El orquestador inserta `6` antes de ambos.
- `1,2,4,10`
  - Ejecuta extractores institucionales y luego el análisis comparado de publicaciones institucionales.
- `10`
  - Ejecuta solo el análisis institucional usando CSV ya existentes.
