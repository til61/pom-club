source .venv/bin/activate
pip install -r requirements.txt
sudo fuser -k 8080/tcp
sudo systemctl restart redis
gunicorn app.runner:app --bind 0.0.0.0:8080
