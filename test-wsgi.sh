venv/bin/uwsgi --socket 0.0.0.0:8080 --protocol=http -w wsgi --callable app
