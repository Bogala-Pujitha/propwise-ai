"""Development entry point: ``python -m app``."""

from app import app, ensure_default_admin, init_engine, initialize_database


def main():
    initialize_database()
    if ensure_default_admin():
        print("Admin user created: admin / admin123")
    init_engine()
    print("PropWise AI starting on http://localhost:5000")
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    main()
