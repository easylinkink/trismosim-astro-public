"""Prueba: carta natal de John Lennon (9-10-1940, 18:30, Liverpool).

1940 es un caso exigente: el Reino Unido mantuvo el horario de verano (GMT+1)
todo el año por la guerra, así que 18:30 hora local = 17:30 UT.
"""
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from kerykeion import AstrologicalSubjectFactory

sys.stdout.reconfigure(encoding='utf-8')

local = datetime(1940, 10, 9, 18, 30, tzinfo=ZoneInfo('Europe/London'))
print('Hora local:', local.isoformat(), '| desfase:', local.utcoffset(), '| UT:', local.astimezone(ZoneInfo('UTC')).strftime('%H:%M'))

s = AstrologicalSubjectFactory.from_birth_data(
    'John Lennon', 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str='Europe/London', city='Liverpool', nation='GB',
    online=False,
)

def fmt(p):
    d = int(p.position)
    m = round((p.position - d) * 60)
    return f'{p.name:<10} {d:>2}°{m:02d}\' {p.sign:<4} casa {str(getattr(p, "house", "")).replace("_House", ""):<8} {"R" if getattr(p, "retrograde", False) else ""}'

for name in ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto', 'chiron', 'mean_lilith', 'true_north_lunar_node']:
    p = getattr(s, name, None)
    if p is not None:
        print(fmt(p))
for name in ['ascendant', 'medium_coeli']:
    p = getattr(s, name, None)
    if p is not None:
        print(fmt(p))
print('Sistema de casas:', s.houses_system_name, '| zodiaco:', s.zodiac_type)

print('--- SuperNatal (asteroides clásicos):')
for name in ['ceres', 'pallas', 'juno', 'vesta']:
    p = getattr(s, name, None)
    print(fmt(p) if p is not None else f'{name}: no disponible en el sujeto por defecto')
