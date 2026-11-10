# SPDX-License-Identifier: AGPL-3.0-only
# trismosim-astro: API interna de cálculo astrológico (Kerykeion 6 + libephemeris / JPL DE440).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    KERYKEION_LEB_MODE=skyfield LIBEPHEMERIS_AUTO_SPK=1 \
    LIBEPHEMERIS_DATA_DIR=/data/ephemeris HOME=/data

WORKDIR /srv/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 1000 --create-home --home-dir /data astro
COPY LICENSE README.md ./
COPY app ./app
COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

USER astro
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/salud', timeout=4).status == 200 else 1)"
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
