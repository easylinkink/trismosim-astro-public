# SPDX-License-Identifier: AGPL-3.0-only
"""Pruebas de la API del motor. Ejecutar: python -m pytest pruebas/test_api.py -q (o python pruebas/test_api.py)."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

LENNON = {'nombre': 'John Lennon', 'fecha': '1940-10-09', 'hora': '18:30', 'lat': 53.4, 'lng': -2.9833, 'zona': 'Europe/London'}
YOKO = {'nombre': 'Yoko Ono', 'fecha': '1933-02-18', 'hora': '20:30', 'lat': 35.6895, 'lng': 139.6917, 'zona': 'Asia/Tokyo'}


def p(carta, ident):
    return next(x for x in carta['puntos'] if x['id'] == ident)


def test_todo():
    with TestClient(app) as c:
        r = c.get('/salud')
        assert r.status_code == 200 and r.headers['X-License'] == 'AGPL-3.0-only'

        t = time.perf_counter()
        r = c.post('/v1/carta-natal', json={'nacimiento': LENNON})
        ms = (time.perf_counter() - t) * 1000
        assert r.status_code == 200, r.text
        carta = r.json()
        # Valores verificados contra Swiss Ephemeris (ver README)
        assert carta['sujeto']['fecha_hora_utc'].startswith('1940-10-09T17:30')
        assert (p(carta, 'Sun')['signo'], p(carta, 'Sun')['grado_texto']) == ('Libra', "16°16'")
        assert (p(carta, 'Moon')['signo'], p(carta, 'Moon')['grado_texto']) == ('Acuario', "3°33'")
        assert (p(carta, 'Ascendant')['signo'], p(carta, 'Ascendant')['grado_texto']) == ('Aries', "19°43'")
        assert p(carta, 'Saturn')['retrogrado'] and p(carta, 'Saturn')['casa'] == 1
        assert len(carta['casas']) == 12 and carta['casas'][9]['signo'] == 'Capricornio'
        assert carta['aspectos'] and not carta['avisos'], carta['avisos']
        print(f'carta natal OK ({ms:.0f} ms) · {len(carta["puntos"])} puntos · {len(carta["aspectos"])} aspectos · reparto {carta["reparto"]}')

        r = c.post('/v1/carta-natal', json={'nacimiento': LENNON, 'asteroides': True})
        sn = r.json()
        assert [p(sn, a)['signo'] for a in ['Ceres', 'Pallas', 'Juno', 'Vesta']] == ['Escorpio', 'Libra', 'Leo', 'Leo']
        assert all(x['precision'] == 'ephemeris' for x in sn['puntos'] if x['precision']), [x for x in sn['puntos'] if x['precision'] != 'ephemeris']
        print('SuperNatal OK · Quirón', p(sn, 'Chiron')['grado_texto'], p(sn, 'Chiron')['signo'], '· Ceres', p(sn, 'Ceres')['grado_texto'], p(sn, 'Ceres')['signo'])

        r = c.post('/v1/carta-natal', json={'nacimiento': {**LENNON, 'hora': None}})
        sin_hora = r.json()
        assert sin_hora['casas'] is None and all(x['casa'] is None for x in sin_hora['puntos']) and sin_hora['avisos']
        print('hora desconocida OK ·', sin_hora['avisos'][0][:60], '…')

        r = c.post('/v1/carta-natal', json={'nacimiento': {**LENNON, 'fecha': '2026-03-29', 'hora': '02:30', 'zona': 'Europe/Madrid'}})
        assert any('ambigua o inexistente' in a for a in r.json()['avisos'])
        print('hora inexistente por cambio de horario detectada OK')

        r = c.post('/v1/carta-natal', json={'nacimiento': {**LENNON, 'zona': 'Marte/Olympus'}})
        assert r.status_code == 422
        print('zona no válida → 422 OK')

        r = c.post('/v1/sinastria', json={'persona1': LENNON, 'persona2': YOKO})
        assert r.status_code == 200 and r.json()['aspectos']
        print('sinastría OK ·', len(r.json()['aspectos']), 'aspectos entre Lennon y Yoko Ono')

        r = c.post('/v1/carta-natal/svg', json={'nacimiento': LENNON, 'asteroides': True})
        assert r.status_code == 200 and r.headers['content-type'].startswith('image/svg+xml') and '<svg' in r.text[:500]
        Path(__file__).with_name('rueda_lennon.svg').write_text(r.text, encoding='utf-8')
        print(f'rueda SVG OK ({len(r.text) // 1024} KB) → pruebas/rueda_lennon.svg')


if __name__ == '__main__':
    test_todo()
    print('TODAS LAS PRUEBAS OK')
