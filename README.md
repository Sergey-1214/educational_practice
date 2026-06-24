# Educational Practice

## Quick start

1. Create an env file for the backend:

```powershell
Copy-Item backend/.env.example backend/.env
```

2. Start the local infrastructure and API:

```powershell
docker compose up --build
```

3. Check that the backend is healthy:

```text
http://localhost:8000/health
```

## Services

- Backend API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Elasticsearch: `http://localhost:9200`

## Notes

- The FastAPI app creates database tables on startup in the current implementation.
- The backend reads configuration from environment variables and supports `DATABASE_URL`.
- For production, it is better to switch table creation to Alembic migrations instead of startup auto-create.
