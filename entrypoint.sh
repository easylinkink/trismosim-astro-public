#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-only
# Descarga las efemérides (nivel "medium", ~500 MB) la primera vez; después solo arranca.
set -e
if [ ! -f "$LIBEPHEMERIS_DATA_DIR/de440.bsp" ]; then
  echo "Descargando efemérides en $LIBEPHEMERIS_DATA_DIR (solo la primera vez)…"
  mkdir -p "$LIBEPHEMERIS_DATA_DIR"
  python -c "from libephemeris.download import download_for_tier; download_for_tier('medium')"
fi
exec "$@"
