#!/usr/bin/env sh
# Instala Python (si falta) en Termux y lanza la Forja de Historias.
#   sh termux.sh                 partida interactiva
#   sh termux.sh --aleatorio     cualquier opción de jugar.py
set -e
cd "$(dirname "$0")"
if ! command -v python >/dev/null 2>&1; then
    echo "Instalando Python..."
    pkg install -y python
fi
exec python jugar.py "$@"
