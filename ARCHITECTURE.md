# PropWise AI application layout

The runtime now follows a Flask MVC/service layout while retaining every
existing browser URL, API URL, template, static asset, ML artifact and dataset
path.

```
app/
├── factory.py          # application creation and extension wiring
├── extensions.py       # SQLAlchemy, Flask-Login, Bcrypt, CORS
├── runtime.py          # lazy ML engine and dataset lifecycle
├── models/             # ORM schema (same tables and columns as before)
├── controllers/
│   ├── web/            # HTML/browser route controllers
│   └── *_controller.py # JSON API controllers
├── services/           # valuation, analytics, auth and data operations
├── views/              # Jinja view layer (unchanged template paths)
└── static/             # browser assets (unchanged URLs)
```

Data safety guarantees:

- The default SQLite target remains `app/propwise.db`.
- `users`, `predictions`, `activities`, and `audit_logs` retain their original
  names, columns, relationships, and data.
- Root-level `data/` and `models/` artifacts remain in their existing paths.
- Existing public imports such as `from app import app, db, User` and all
  established route URLs remain supported.

`app/legacy_monolith.py` is a source-only migration archive and is not imported
by the runtime. It can be removed after a release window once downstream
integrations have adopted the modular entry points.
