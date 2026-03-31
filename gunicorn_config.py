import os

# Gunicorn config
bind = f"0.0.0.0:{os.environ.get('PORT') or 10000}"
workers = 1
worker_class = "sync"
timeout = 120

def on_starting(server):
    """Run database initialization before gunicorn starts serving."""
    print("==> Running database initialization...")
    try:
        from db_config import init_database, test_connection
        if init_database():
            print("✓ Database initialized successfully")
            test_connection()
        else:
            print("✗ Database initialization failed")
    except Exception as e:
        print(f"Database init error: {e}")
