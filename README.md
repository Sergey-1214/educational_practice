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

Open the web interface at `http://localhost:5173`. Register an account, upload PDF/DOCX files, wait for indexing, and search across the library.

3. Optional: create `backend/.env` from the example if you want to run the backend outside Docker or override defaults:

```powershell
Copy-Item backend/.env.example backend/.env
```

4. Optional: copy the root example if you want to override Docker Compose variables from a root `.env` file:

```powershell
Copy-Item .env.example .env
```

## Services

- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Elasticsearch: `http://localhost:9200`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

## Helpful commands

```powershell
docker compose down
docker compose down -v
docker compose logs -f backend
docker compose up --build
```

## Monitoring

- Metrics endpoint: `http://localhost:8000/metrics`
- Prometheus scrapes the backend automatically.
- Grafana starts with a preconfigured Prometheus datasource and a `Backend Overview` dashboard.
- Default Grafana credentials come from `.env.example`: `admin` / `admin`

## CI

- GitHub Actions validates backend linting, tests, backend image build, and `docker compose config`.
- The CI workflow starts a dedicated PostgreSQL service for backend tests, because FastAPI startup initializes database tables during the test run.
- Workflow file: `.github/workflows/backend-ci.yml`

## Demo initialization

- `init.sh` waits for the backend, registers a demo user, logs in, downloads 10 public PDF files, and uploads them through the API.
- Example usage:

```bash
chmod +x init.sh
./init.sh
```

## Notes

- `docker compose` now provides default backend environment variables, so a missing `backend/.env` should not prevent local startup.
- The FastAPI app creates database tables on startup in the current implementation.
- The backend reads configuration from environment variables and supports `DATABASE_URL`.
- For production, it is better to switch table creation to Alembic migrations instead of startup auto-create.
- GitHub Actions runs backend linting, tests, and image build for changes in `backend/**` on `master` and `dev`.
- The React/TypeScript frontend is built as a multi-stage image and served by Nginx on port `5173`.
