#!/usr/bin/env bash
set -e

python scripts/wait_for_db.py

if [ -d migrations ]; then
  flask db upgrade
fi

exec "$@"
