# trismosim-astro

Motor de cálculo astrológico de Trismosim. **Licencia: AGPL-3.0** (este servicio se publicará como repositorio público; la web, la tienda, los textos de interpretación y los datos de clientes no forman parte de él).

## Base técnica
- **Kerykeion 6.0.5** (AGPL-3.0) con **libephemeris 3.2.2** (AGPL-3.0): efemérides **NASA JPL DE440** (1550–2650) y archivos SPK de asteroides (1850–2150).
- Datos en `~/.libephemeris` (≈ 500 MB, nivel `medium`): `de440.bsp`, `planet_centers_medium.bsp` y `spk/` (37 cuerpos menores, entre ellos Quirón, Ceres, Palas, Juno y Vesta).

## Configuración obligatoria
| Variable | Valor | Por qué |
|---|---|---|
| `KERYKEION_LEB_MODE` | `skyfield` | Por defecto Kerykeion usa un archivo precalculado (LEB) **sin asteroides** y calcula Quirón, Ceres, Palas, Juno y Vesta con una aproximación kepleriana (errores de hasta 3′). En `skyfield` usa DE440 + SPK: precisión de efemérides en todos los cuerpos. |
| `LIBEPHEMERIS_AUTO_SPK` | `1` | Usa los archivos SPK de asteroides descargados. |

Pendiente de evaluar: instalar los paquetes LEB2 (`libephemeris download leb2-medium`, con grupo de asteroides mayores) para recuperar la velocidad del modo LEB sin perder precisión.

## Verificación (2026-11-10)
Carta de John Lennon, 9-10-1940 18:30, Liverpool. El horario de verano británico de guerra (GMT+1) se aplica correctamente: 17:30 UT.

| Punto | Kerykeion (DE440) | Swiss Ephemeris 2.10.03 (independiente) |
|---|---|---|
| Sol | 16°16′ Libra | 16°16′ Libra |
| Luna | 3°33′ Acuario | 3°33′ Acuario |
| Mercurio | 8°33′ Escorpio | 8°33′ Escorpio |
| Venus | 3°13′ Virgo | 3°13′ Virgo |
| Marte | 2°40′ Libra | 2°40′ Libra |
| Júpiter R / Saturno R / Urano R | 13°42′ / 13°13′ / 25°33′ Tauro | idénticos |
| Neptuno / Plutón | 26°02′ Virgo / 4°11′ Leo | idénticos |
| Nodo verdadero | 11°01′ Libra | 11°02′ Libra (redondeo) |
| Ascendente / MC | 19°43′ Aries / 7°04′ Capricornio | idénticos |

SuperNatal en modo de precisión completa: Quirón 0°34′ Leo, Ceres 1°27′ Escorpio, Palas 14°06′ Libra, Juno 16°05′ Leo, Vesta 12°39′ Leo.

## API (v0.1.0, solo red interna)
Todas las respuestas llevan las cabeceras `X-License: AGPL-3.0-only` y `X-Source-Code: <repositorio>`.

| Método y ruta | Uso |
|---|---|
| `GET /salud` | Comprobación de estado |
| `GET /v1/info` | Versión, licencia, enlace al código fuente, efemérides y sistemas de casas |
| `POST /v1/carta-natal` | `{nacimiento, asteroides}` → puntos (signo, grado, casa, retrógrado, elemento, modalidad, precisión), 12 casas, aspectos (tipo, orbe, aplicativo/separativo), reparto por elementos y modalidades, avisos |
| `POST /v1/carta-natal/svg` | Igual + `tema` (`classic`, `dark`, `black-and-white`) → rueda en SVG, en español |
| `POST /v1/sinastria` | `{persona1, persona2}` → aspectos entre las dos cartas |

`nacimiento`: `nombre`, `fecha` (AAAA-MM-DD), `hora` (HH:MM local o `null` si se desconoce), `lat`, `lng`, `zona` (IANA, p. ej. `America/Caracas`), `sistema_casas` (`placidus`, `koch`, `iguales`, `signos_completos`, `regiomontano`, `campanus`, `porfirio`), `zodiaco` (`tropical` o `sideral` + `ayanamsa`).

Comportamientos:
- **Hora desconocida:** se calcula a las 12:00, sin casas ni ángulos, con aviso.
- **Hora ambigua o inexistente** por cambio de horario: se calcula con horario estándar y se avisa.
- **Fechas fuera de 1550–2650 o zona no válida:** error 422.
- Si algún cuerpo no tiene precisión de efemérides, se avisa en `avisos`.
- Los cálculos se serializan con un candado (libephemeris tiene estado global). Una carta tarda unos 0,35–0,4 s y una rueda unos 0,5 s.

## Despliegue
- `Dockerfile` (python:3.12-slim, usuario sin privilegios). `entrypoint.sh` descarga las efemérides la primera vez en `LIBEPHEMERIS_DATA_DIR` (volumen).
- Staging en US2: contenedor `trismosim-staging-astro`, solo en la red `trismosim-staging-interna`, efemérides en `/srv/trismosim/ephemeris` (520 MB). Unos 116 MB de RAM.

## Pruebas
```bash
python -m venv .venv && .venv/Scripts/pip install kerykeion
KERYKEION_LEB_MODE=skyfield LIBEPHEMERIS_AUTO_SPK=1 .venv/Scripts/python pruebas/supernatal_lennon.py
```
- `pruebas/carta_lennon.py`: carta natal y horario histórico.
- `pruebas/supernatal_lennon.py`: Quirón y los 4 asteroides clásicos.
- `pruebas/test_api.py`: pruebas de la API (carta, SuperNatal, hora desconocida, cambio de horario, errores, sinastría, rueda SVG).
- `pruebas/referencia_swisseph.py`: referencia independiente con Swiss Ephemeris (requiere `pyswisseph`, que compila en Linux con la imagen `python:3.12`; no en Windows con Python 3.14).
