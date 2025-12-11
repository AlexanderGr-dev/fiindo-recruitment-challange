# Fiindo Recruitment Challenge

A Python ETL-style project that fetches financial data from a Fiindo API, processes it
(calculations, aggregations), and persists results in a local SQLite database.  
The project emphasizes clean architecture, testability, and separation of concerns.

---

## Project Structure
```
fiindo-recruitment-challange/
├─ src/ # Application source code
│ ├─ clients/ # API client implementations
│ ├─ services/ # ETL orchestration & calculations
│ ├─ repositories/ # Database repository interfaces
│ ├─ models/ # SQLAlchemy domain models
│ ├─ schemas/ # Pydantic schemas for API response parsing
│ └─ core/ # Configuration and shared utilities
├─ tests/unit/ # Unit tests 
├─ requirements.txt # Python dependencies
├─ example.env # Example environment variables
├─ Dockerfile # Optional container configuration
└─ docker-compose.yml # Optional container orchestration
```

## Requirements
- Python 3.10 (project was developed & tested against 3.10)
- Git
- (Optional) Docker + Docker Compose

## Quick start 

1. Clone the repository

```powershell
git clone https://github.com/AlexanderGr-dev/fiindo-recruitment-challange.git
cd fiindo-recruitment-challange
```

2. Create a virtual environment and activate it

Windows PowerShell
```powershell
python -m venv .venv
& .venv\Scripts\Activate
```
Linux / macOS
```powershell
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

4. Provide environment variables

Edit .env to provide API credentials, DB path, etc.:

```powershell
cp example.env .env
```

5. Run the application

The application entry point is `src.main`. You can run it with:

```powershell
python -m src.main
```

## Tests

Run unit tests with pytest using the virtual environment Python:

```powershell
pytest
```

- Unit tests live under `tests/unit/` and mock external I/O (HTTP, DB).

## Docker 

There is a `Dockerfile` and `docker-compose.yml` for containerized runs. Basic commands:

```powershell
# Build images
docker-compose build

# Run application service
docker-compose up app

# Or run tests in the tests service (if defined)
docker-compose run --rm tests
```

Notes and common issues:
- Ensure Docker Desktop / the Docker daemon is running before using `docker-compose`.
- When running with SQLite and bind-mounted repos, avoid mounting the app directory read-only, otherwise SQLite will fail with "attempt to write a readonly database". Use a named volume or ensure read-write mounts for database files.

## Configuration

The project reads configuration via `src/core/config.py` and an `.env` file. Key settings include:

- `DATABASE_URL` — defaults to a local SQLite file in the project
- `FIINDO_API_BASE` — base URL for the Fiindo API
- `FIINDO_AUTH` — bearer access token
- `ETL_MAX_WORKERS` — concurrency degree used by ETL (ThreadPoolExecutor)

Edit `example.env` and copy to `.env` to override development defaults.

## Next Improvements (suggestions)

- Implement token-bucket rate limiter for parallel API calls
- Add integration tests for real API scenarios
- Introduce CI/CD workflow with automated tests
- Use a small SQLite named volume in Docker Compose for persistence that is writable by the container.

## Contact Information / Author
If you have any questions about the project or the architecture, please do not hesitate to contact me.

- **Name:** Alexander Griesbeck
- **E-Mail:** alex.griesbeck@gmx.de
- **LinkedIn:** www.linkedin.com/in/alexander-griesbeck-3108a91b6
