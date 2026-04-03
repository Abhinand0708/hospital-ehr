#!/bin/bash
echo "==> Initializing database..."
python -c "
from db_config import init_database, test_connection
try:
    if init_database():
        print('✓ Database initialized')
        test_connection()
    else:
        print('✗ Database init failed')
except Exception as e:
    print(f'DB init error: {e}')
"
echo "==> Starting gunicorn on port ${PORT:-10000}..."
exec gunicorn --bind 0.0.0.0:${PORT:-10000} --timeout 120 --workers 1 app:app
