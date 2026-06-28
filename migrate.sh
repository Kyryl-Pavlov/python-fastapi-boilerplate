#!/bin/bash

set -e

read -p "Migration message: " migration_message

PYTHONPATH="${PYTHONPATH:-.}" python -m alembic revision --autogenerate -m "$migration_message"

read -p "Migration created. Run upgrade? [y/N] " confirm
[[ "$confirm" == [yY] ]] && PYTHONPATH="${PYTHONPATH:-.}" python -m alembic upgrade head
