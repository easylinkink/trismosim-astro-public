"""Prueba: SuperNatal de John Lennon (carta natal + Quirón + Ceres, Palas, Juno y Vesta)."""
import os
import sys

os.environ.setdefault('LIBEPHEMERIS_AUTO_SPK', '1')  # usar los archivos SPK de asteroides descargados
sys.stdout.reconfigure(encoding='utf-8')

from kerykeion import AstrologicalSubjectFactory  # noqa: E402
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS  # noqa: E402

PUNTOS = list(DEFAULT_ACTIVE_POINTS) + [p for p in ['Chiron', 'Ceres', 'Pallas', 'Juno', 'Vesta'] if p not in DEFAULT_ACTIVE_POINTS]

s = AstrologicalSubjectFactory.from_birth_data(
    'John Lennon', 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str='Europe/London', city='Liverpool', nation='GB',
    online=False, active_points=PUNTOS,
)

for name in ['sun', 'moon', 'ascendant', 'chiron', 'ceres', 'pallas', 'juno', 'vesta']:
    p = getattr(s, name, None)
    if p is None:
        print(f'{name}: no calculado')
        continue
    d = int(p.position)
    m = round((p.position - d) * 60)
    print(f'{p.name:<10} {d:>2}°{m:02d}\' {p.sign:<4} {str(getattr(p, "house", "")).replace("_House", ""):<9} {"R" if getattr(p, "retrograde", False) else ""}')
