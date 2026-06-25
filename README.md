# Educational Practice

## Quick start

1. Start the local infrastructure and API:

```powershell
docker compose up --build
```

2. Check that the backend is healthy:

```text
http://localhost:8000/health
```

3. Optional: create `backend/.env` from the example if you want to run the backend outside Docker or override defaults:

```powershell
Copy-Item backend/.env.example backend/.env
```

## Services

- Backend API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Elasticsearch: `http://localhost:9200`

## Notes

- `docker compose` now provides default backend environment variables, so a missing `backend/.env` should not prevent local startup.
- The FastAPI app creates database tables on startup in the current implementation.
- The backend reads configuration from environment variables and supports `DATABASE_URL`.
- For production, it is better to switch table creation to Alembic migrations instead of startup auto-create.
