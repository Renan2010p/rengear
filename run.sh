#!/usr/bin/env bash
# Launch RENGEAR from a checkout.
set -e
cd "$(dirname "$0")"
exec python main.py "$@"
