#!/bin/bash
set -e

docker run --rm \
  --entrypoint bash \
  -v "$(pwd)/src":/var/task \
  -v "$(pwd)/requirements-dev.txt":/requirements-dev.txt \
  public.ecr.aws/lambda/python:3.12 \
  -c "
    python -m venv /opt/venv &&
    /opt/venv/bin/pip install hfst-altlab -r /requirements-dev.txt -q &&
    /opt/venv/bin/ruff check /var/task &&
    PYTHONPATH=/var/task /opt/venv/bin/python -m pytest /var/task/test/ -v -m 'not integration'
  "
