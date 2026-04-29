#!/bin/bash

# Install requirements
pip install -r requirements.txt

# Run collectstatic
python manage.py collectstatic --noinput
