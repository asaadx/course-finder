#!/bin/sh
# Seed the database on first start only, so enrollments in the volume survive restarts.
set -e

if [ ! -f "$DATABASE" ]; then
  python3 seed.py
fi

exec "$@"
