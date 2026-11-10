# SPDX-License-Identifier: AGPL-3.0-only
# trismosim-astro — motor de cálculo astrológico de Trismosim.
# Copyright (C) 2026 Trismosim
"""API HTTP interna del motor astrológico (solo accesible desde la red Docker de Trismosim)."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator

from . import motor

CODIGO_FUENTE = os.environ.get('ASTRO_CODIGO_FUENTE', 'https://github.com/trismosim/trismosim-astro')
log = logging.getLogger('trismosim-astro')


class Nacimiento(BaseModel):
    nombre: Optional[str] = Field(None, max_length=80)
    fecha: str = Field(..., description='AAAA-MM-DD', pattern=r'^\d{4}-\d{2}-\d{2}$')
    hora: Optional[str] = Field(None, description='HH:MM (hora local). Vacío si se desconoce', pattern=r'^\d{2}:\d{2}$')
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    zona: str = Field(..., description='Zona horaria IANA, p. ej. Europe/Madrid')
    sistema_casas: Literal['placidus', 'koch', 'iguales', 'signos_completos', 'regiomontano', 'campanus', 'porfirio'] = 'placidus'
    zodiaco: Literal['tropical', 'sideral'] = 'tropical'
    ayanamsa: Optional[str] = Field(None, description='Solo sideral: LAHIRI, FAGAN_BRADLEY, RAMAN…')

    @field_validator('hora')
    @classmethod
    def hora_valida(cls, v):
        if v:
            hh, mm = (int(x) for x in v.split(':'))
            if not (0 <= hh < 24 and 0 <= mm < 60):
                raise ValueError('hora fuera de rango')
        return v


class PeticionNatal(BaseModel):
    nacimiento: Nacimiento
    asteroides: bool = Field(False, description='Incluir Ceres, Palas, Juno y Vesta (SuperNatal)')


class PeticionRueda(PeticionNatal):
    tema: Literal['classic', 'dark', 'black-and-white'] = 'classic'


class PeticionSinastria(BaseModel):
    persona1: Nacimiento
    persona2: Nacimiento


@asynccontextmanager
async def ciclo_vida(app: FastAPI):
    # Precalentar: la primera carta carga ~300 MB de efemérides
    try:
        motor.carta_natal({'fecha': '2000-01-01', 'hora': '12:00', 'lat': 0, 'lng': 0, 'zona': 'UTC'}, asteroides=True)
        log.info('Efemérides cargadas')
    except Exception:  # noqa: BLE001
        log.exception('Fallo al precalentar el motor')
    yield


app = FastAPI(title='trismosim-astro', version=motor.VERSION, lifespan=ciclo_vida,
              description='Motor de cálculo astrológico de Trismosim. Licencia AGPL-3.0.')


@app.middleware('http')
async def aviso_licencia(request, call_next):
    respuesta = await call_next(request)
    respuesta.headers['X-Source-Code'] = CODIGO_FUENTE
    respuesta.headers['X-License'] = 'AGPL-3.0-only'
    return respuesta


def _ejecutar(funcion, *args, **kwargs):
    try:
        return funcion(*args, **kwargs)
    except motor.ErrorDatos as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.get('/salud')
def salud():
    return {'estado': 'ok', 'version': motor.VERSION}


@app.get('/v1/info')
def info():
    return {'motor': 'trismosim-astro', 'version': motor.VERSION, 'licencia': 'AGPL-3.0-only',
            'codigo_fuente': CODIGO_FUENTE, 'efemerides': 'NASA JPL DE440 (libephemeris)',
            'sistemas_casas': list(motor.SISTEMAS_CASAS)}


@app.post('/v1/carta-natal')
def carta_natal(p: PeticionNatal):
    return _ejecutar(motor.carta_natal, p.nacimiento.model_dump(), asteroides=p.asteroides)


@app.post('/v1/carta-natal/svg')
def carta_natal_svg(p: PeticionRueda):
    svg = _ejecutar(motor.rueda_svg, p.nacimiento.model_dump(), asteroides=p.asteroides, tema=p.tema)
    return Response(content=svg, media_type='image/svg+xml')


@app.post('/v1/sinastria')
def sinastria(p: PeticionSinastria):
    return _ejecutar(motor.sinastria, p.persona1.model_dump(), p.persona2.model_dump())
