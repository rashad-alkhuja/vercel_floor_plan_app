#!/bin/bash

# Install requirements (--break-system-packages needed for Vercel's uv-managed Python)
pip install --break-system-packages -r requirements.txt

# Run collectstatic
python manage.py collectstatic --noinput
