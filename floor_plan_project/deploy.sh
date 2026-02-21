#!/bin/bash

# Configuration
PROJECT_DIR="/home/ubuntu/djaongo_floor_plan" # Update with your project path
VENV_PATH="$PROJECT_DIR/venv"
LOG_FILE="$PROJECT_DIR/deploy.log"

echo "[$(date)] Starting deployment..." | tee -a $LOG_FILE

# Navigate to project directory
cd $PROJECT_DIR || { echo "Failed to enter directory $PROJECT_DIR"; exit 1; }

# Pull latest changes
git pull origin main | tee -a $LOG_FILE

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Install dependencies
pip install -r floor_plan_project/requirements.txt | tee -a $LOG_FILE

# Run migrations
python floor_plan_project/manage.py migrate | tee -a $LOG_FILE

# Collect static files
python floor_plan_project/manage.py collectstatic --noinput | tee -a $LOG_FILE

# Restart Gunicorn service
sudo systemctl restart gunicorn | tee -a $LOG_FILE
sudo systemctl restart nginx | tee -a $LOG_FILE

echo "[$(date)] Deployment finished successfully!" | tee -a $LOG_FILE
