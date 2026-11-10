# SPDX-License-Identifier: AGPL-3.0-only
# trismosim-astro — motor de cálculo astrológico de Trismosim.
# Copyright (C) 2026 Trismosim
"""Cálculo de cartas con Kerykeion 6 + libephemeris (efemérides NASA JPL DE440).

Solo calcula: no contiene textos de interpretación.
"""
from __future__ import annotations

import os
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

# Precisión de efemérides para todos los cuerpos (Quirón y asteroides incluidos).
# Ver README: el modo por defecto de Kerykeion aproxima los asteroides.
os.environ.setdefault('KERYKEION_LEB_MODE', 'skyfield')
os.environ.setdefault('LIBEPHEMERIS_AUTO_SPK', '1')

from kerykeion import AspectsFactory, AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer, KerykeionException  # noqa: E402
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS  # noqa: E402

VERSION = '0.1.0'

# libephemeris mantiene estado global: los cálculos se serializan.
_lock = threading.Lock()

SIGNOS = {
    'Ari': 'Aries', 'Tau': 'Tauro', 'Gem': 'Géminis', 'Can': 'Cáncer', 'Leo': 'Leo', 'Vir': 'Virgo',
    'Lib': 'Libra', 'Sco': 'Escorpio', 'Sag': 'Sagitario', 'Cap': 'Capricornio', 'Aqu': 'Acuario', 'Pis': 'Piscis',
}
PUNTOS = {
    'Sun': 'Sol', 'Moon': 'Luna', 'Mercury': 'Mercurio', 'Venus': 'Venus', 'Mars': 'Marte',
    'Jupiter': 'Júpiter', 'Saturn': 'Saturno', 'Uranus': 'Urano', 'Neptune': 'Neptuno', 'Pluto': 'Plutón',
    'True_North_Lunar_Node': 'Nodo Norte', 'True_South_Lunar_Node': 'Nodo Sur',
    'Mean_North_Lunar_Node': 'Nodo Norte medio', 'Mean_South_Lunar_Node': 'Nodo Sur medio',
    'Chiron': 'Quirón', 'Mean_Lilith': 'Lilith', 'True_Lilith': 'Lilith verdadera',
    'Ceres': 'Ceres', 'Pallas': 'Palas', 'Juno': 'Juno', 'Vesta': 'Vesta',
    'Ascendant': 'Ascendente', 'Medium_Coeli': 'Medio Cielo', 'Descendant': 'Descendente', 'Imum_Coeli': 'Fondo del Cielo',
}
ASPECTOS = {
    'conjunction': 'conjunción', 'opposition': 'oposición', 'trine': 'trígono', 'square': 'cuadratura',
    'sextile': 'sextil', 'quincunx': 'quincuncio', 'semi-sextile': 'semisextil', 'semi-square': 'semicuadratura',
    'sesquiquadrate': 'sesquicuadratura', 'quintile': 'quintil', 'biquintile': 'biquintil',
}
CASAS = ['First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth', 'Seventh', 'Eighth', 'Ninth', 'Tenth', 'Eleventh', 'Twelfth']
ELEMENTOS = {'Fire': 'fuego', 'Earth': 'tierra', 'Air': 'aire', 'Water': 'agua'}
MODALIDADES = {'Cardinal': 'cardinal', 'Fixed': 'fija', 'Mutable': 'mutable'}

ANGULOS = ['Ascendant', 'Medium_Coeli', 'Descendant', 'Imum_Coeli']
ASTEROIDES = ['Ceres', 'Pallas', 'Juno', 'Vesta']
BASE = [p for p in DEFAULT_ACTIVE_POINTS if p not in ASTEROIDES]
if 'Chiron' not in BASE:
    BASE.append('Chiron')
SISTEMAS_CASAS = {'placidus': 'P', 'koch': 'K', 'iguales': 'A', 'signos_completos': 'W', 'regiomontano': 'R', 'campanus': 'C', 'porfirio': 'O'}


class ErrorDatos(ValueError):
    """Datos de nacimiento no válidos."""


def grados_texto(posicion: float) -> str:
    g = int(posicion)
    m = int(round((posicion - g) * 60))
    if m == 60:
        g, m = g + 1, 0
    return f"{g}°{m:02d}'"


def _numero_casa(nombre: str | None) -> int | None:
    if not nombre:
        return None
    clave = nombre.replace('_House', '')
    return CASAS.index(clave) + 1 if clave in CASAS else None


def _avisos_hora_local(fecha: str, hora: str, zona: str) -> list[str]:
    """Detecta horas inexistentes o ambiguas por cambios de horario (verano/invierno)."""
    tz = ZoneInfo(zona)
    local = datetime.fromisoformat(f'{fecha}T{hora}')
    a, b = local.replace(tzinfo=tz, fold=0), local.replace(tzinfo=tz, fold=1)
    if a.utcoffset() != b.utcoffset():
        return ['La hora local es ambigua o inexistente por un cambio de horario (verano/invierno) en esa fecha y lugar: se ha calculado con el horario estándar (invierno). Conviene confirmar la hora.']
    return []


def crear_sujeto(datos: dict, *, asteroides: bool = False):
    """datos: nombre, fecha (AAAA-MM-DD), hora (HH:MM) o None, lat, lng, zona (IANA), sistema_casas, zodiaco, ayanamsa."""
    try:
        zona = datos['zona']
        ZoneInfo(zona)
        f = datetime.fromisoformat(datos['fecha'])
    except Exception as e:  # noqa: BLE001
        raise ErrorDatos(f'Fecha o zona horaria no válidas: {e}') from e
    if not (1550 <= f.year <= 2650):
        raise ErrorDatos('La fecha debe estar entre 1550 y 2650 (cobertura de las efemérides DE440).')
    hora_conocida = bool(datos.get('hora'))
    hora = datos.get('hora') or '12:00'
    hh, mm = (int(x) for x in hora.split(':')[:2])
    sistema = SISTEMAS_CASAS.get(datos.get('sistema_casas', 'placidus'))
    if sistema is None:
        raise ErrorDatos(f'Sistema de casas no soportado. Opciones: {", ".join(SISTEMAS_CASAS)}')
    zodiaco = datos.get('zodiaco', 'tropical')
    extra = {}
    if zodiaco == 'sideral':
        extra = {'zodiac_type': 'Sidereal', 'sidereal_mode': datos.get('ayanamsa', 'LAHIRI').upper()}
    elif zodiaco != 'tropical':
        raise ErrorDatos("zodiaco debe ser 'tropical' o 'sideral'.")

    puntos = BASE + (ASTEROIDES if asteroides else [])
    if not hora_conocida:
        puntos = [p for p in puntos if p not in ANGULOS]
    avisos = _avisos_hora_local(datos['fecha'], f'{hh:02d}:{mm:02d}', zona)
    args = dict(lng=float(datos['lng']), lat=float(datos['lat']), tz_str=zona, online=False,
                houses_system_identifier=sistema, active_points=puntos, suppress_geonames_warning=True, **extra)
    if avisos:
        # Hora ambigua o inexistente: se toma la lectura de horario estándar (invierno) y se avisa
        args['is_dst'] = False
    try:
        sujeto = AstrologicalSubjectFactory.from_birth_data(
            datos.get('nombre') or 'Consulta', f.year, f.month, f.day, hh, mm, **args)
    except KerykeionException as e:
        raise ErrorDatos(f'No se pudo calcular la carta con esos datos: {e}') from e
    if not hora_conocida:
        avisos.append('Hora de nacimiento desconocida: carta calculada a las 12:00 sin casas ni ángulos; la Luna puede variar hasta ±7°.')
    return sujeto, puntos, hora_conocida, avisos


def _punto(p, con_casa: bool) -> dict:
    return {
        'id': p.name,
        'nombre': PUNTOS.get(p.name, p.name),
        'signo': SIGNOS.get(p.sign, p.sign),
        'grado': round(p.position, 4),
        'grado_texto': grados_texto(p.position),
        'longitud': round(p.abs_pos, 4),
        'casa': _numero_casa(p.house) if con_casa else None,
        'retrogrado': bool(p.retrograde),
        'elemento': ELEMENTOS.get(p.element, p.element),
        'modalidad': MODALIDADES.get(p.quality, p.quality),
        'precision': p.precision_class,
    }


def _aspecto(a) -> dict:
    return {
        'punto1': a.p1_name, 'punto1_nombre': PUNTOS.get(a.p1_name, a.p1_name),
        'punto2': a.p2_name, 'punto2_nombre': PUNTOS.get(a.p2_name, a.p2_name),
        'tipo': a.aspect, 'tipo_nombre': ASPECTOS.get(a.aspect, a.aspect),
        'angulo': a.aspect_degrees, 'orbe': round(a.orbit, 2),
        'movimiento': {'Applying': 'aplicativo', 'Separating': 'separativo'}.get(a.aspect_movement, a.aspect_movement),
    }


def _puntos_de(sujeto, puntos: list[str], con_casa: bool) -> list[dict]:
    salida = []
    for nombre in puntos:
        p = getattr(sujeto, nombre.lower(), None)
        if p is not None:
            salida.append(_punto(p, con_casa))
    return salida


def carta_natal(datos: dict, *, asteroides: bool = False) -> dict:
    with _lock:
        sujeto, puntos, hora_conocida, avisos = crear_sujeto(datos, asteroides=asteroides)
        aspectos = AspectsFactory.single_chart_aspects(sujeto, active_points=puntos)
        lista = _puntos_de(sujeto, puntos, hora_conocida)
        casas = None
        if hora_conocida:
            casas = []
            for i, c in enumerate(CASAS, start=1):
                h = getattr(sujeto, f'{c.lower()}_house')
                casas.append({'numero': i, 'signo': SIGNOS.get(h.sign, h.sign), 'grado': round(h.position, 4),
                              'grado_texto': grados_texto(h.position), 'longitud': round(h.abs_pos, 4)})
    no_efemeride = [p['nombre'] for p in lista if p['precision'] not in ('ephemeris', None)]
    if no_efemeride:
        avisos.append(f'Calculados sin efemérides de precisión: {", ".join(no_efemeride)}.')
    planetas = [p for p in lista if p['id'] not in ANGULOS and 'Node' not in p['id'] and 'Lilith' not in p['id']]
    reparto = {'elementos': {}, 'modalidades': {}}
    for p in planetas:
        reparto['elementos'][p['elemento']] = reparto['elementos'].get(p['elemento'], 0) + 1
        reparto['modalidades'][p['modalidad']] = reparto['modalidades'].get(p['modalidad'], 0) + 1
    return {
        'sujeto': {
            'nombre': sujeto.name, 'fecha_hora_local': sujeto.iso_formatted_local_datetime,
            'fecha_hora_utc': sujeto.iso_formatted_utc_datetime, 'zona': sujeto.tz_str,
            'lat': sujeto.lat, 'lng': sujeto.lng, 'hora_conocida': hora_conocida,
        },
        'configuracion': {'zodiaco': datos.get('zodiaco', 'tropical'), 'sistema_casas': sujeto.houses_system_name,
                          'asteroides': asteroides, 'efemerides': 'NASA JPL DE440 (libephemeris)'},
        'puntos': lista,
        'casas': casas,
        'aspectos': [_aspecto(a) for a in aspectos.aspects],
        'reparto': reparto,
        'avisos': avisos,
    }


def sinastria(datos1: dict, datos2: dict) -> dict:
    with _lock:
        s1, p1, h1, av1 = crear_sujeto(datos1)
        s2, p2, h2, av2 = crear_sujeto(datos2)
        puntos = [p for p in p1 if p in p2]
        aspectos = AspectsFactory.dual_chart_aspects(s1, s2, active_points=puntos)
    return {
        'persona1': s1.name, 'persona2': s2.name,
        'aspectos': [_aspecto(a) for a in aspectos.aspects],
        'avisos': [f'{s1.name}: {a}' for a in av1] + [f'{s2.name}: {a}' for a in av2],
    }


def rueda_svg(datos: dict, *, asteroides: bool = False, tema: str = 'classic') -> str:
    with _lock:
        sujeto, puntos, _, _ = crear_sujeto(datos, asteroides=asteroides)
        chart = ChartDataFactory.create_natal_chart_data(sujeto, active_points=puntos)
        dibujo = ChartDrawer(chart, theme=tema, chart_language='ES')
        return dibujo.generate_svg_string(minify=True)
