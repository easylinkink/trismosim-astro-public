"""Referencia independiente con Swiss Ephemeris (pyswisseph): Lennon, 1940-10-09 17:30 UT, Liverpool."""
import swisseph as swe

SIGNOS = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']
jd = swe.julday(1940, 10, 9, 17.5)
lat, lon = 53.4, -2.9833


def fmt(nombre, lng):
    s = int(lng // 30)
    g = lng - s * 30
    d = int(g)
    m = round((g - d) * 60)
    if m == 60:
        d, m = d + 1, 0
    return f'{nombre:<10} {d:>2}°{m:02d}\' {SIGNOS[s]}'


cuerpos = [('Sun', swe.SUN), ('Moon', swe.MOON), ('Mercury', swe.MERCURY), ('Venus', swe.VENUS), ('Mars', swe.MARS),
           ('Jupiter', swe.JUPITER), ('Saturn', swe.SATURN), ('Uranus', swe.URANUS), ('Neptune', swe.NEPTUNE),
           ('Pluto', swe.PLUTO), ('TrueNode', swe.TRUE_NODE)]
print('swisseph', swe.version, '(efemérides Moshier, sin archivos)')
for nombre, cid in cuerpos:
    xx, _ = swe.calc_ut(jd, cid, swe.FLG_MOSEPH | swe.FLG_SPEED)
    print(fmt(nombre, xx[0]), 'R' if xx[3] < 0 else '')
cuspides, ascmc = swe.houses(jd, lat, lon, b'P')
print(fmt('Ascendant', ascmc[0]))
print(fmt('MC', ascmc[1]))
