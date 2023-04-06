source .venv/bin/activate
pip install -r requirements.txt
killall gunicorn
gunicorn app.runner:app --bind 0.0.0.0:8080
