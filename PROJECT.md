## Directory Structure
```
/backend
├── app/
│   ├── __init__.py
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── movies.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── config.py
│   ├── crud/
│   │   ├── __init__.py
│   │   └── crud_movie.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── movie.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── movie.py
│   └── main.py
├── scripts/
│       ├── __init__.py
│       └── ingest_metadata.py
├── .env
├── .env.example
└── requirements.txt
```