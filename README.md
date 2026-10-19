# Demographic Pipeline API

A lightweight REST API service providing standardized Eurostat demographic time-series data for Czech and Swedish regions. It serves cleaned datasets from Eurostat prepared for my Bachelor's research at the Czech University of Life Sciences Prague.

The service loads CSV files into a normalized SQLite database and exposes the data through documented FastAPI endpoints. Queries can be filtered by region, year, indicator, and age category.

## Why this project

This project turns several inconsistent demographic files into one queryable data service. It demonstrates practical backend work around data loading, relational modeling, validation, and API design.

## Features

- Loads fertility, migration, mortality, and aging data from CSV files
- Maps Czech and Swedish regions to country entities
- Provides filtering, pagination, metadata, summaries, and health checks
- Prevents duplicate records with a database uniqueness constraint
- Includes Docker setup and automatic database seeding

## Tech stack

| Area | Technology |
| --- | --- |
| Language | Python 3.12 |
| API framework | FastAPI |
| ORM | SQLAlchemy 2 |
| Database | SQLite |
| Server | Uvicorn |
| Packaging and deployment | Docker, Docker Compose |
| Data format | CSV |

## Architecture

```text
CSV files
   |
   v
app.seed -> app.data_loader -> SQLAlchemy models -> SQLite
                                                   |
                                                   v
                                      FastAPI REST endpoints
```

The loader validates CSV columns, converts numeric values, resolves geographic entities, and writes normalized records through SQLAlchemy. The API reads the same model through database sessions.

## Quick start with Docker

### Prerequisites

- Docker Desktop with Docker Compose

### Run the API

```bash
git clone https://github.com/<your-username>/demographic-pipeline.git
cd demographic-pipeline
docker compose up --build
```

The API will be available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

The SQLite database is stored in a named Docker volume, so it persists when the container is restarted.

### Stop the API

```bash
docker compose down
```

To remove the persisted database as well:

```bash
docker compose down -v
```

## Run locally without Docker

### Prerequisites

- Python 3.12 or newer
- A virtual environment is recommended

### Install dependencies

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Seed the database and start the API

```bash
python -m app.seed
uvicorn app.main:app --reload
```

The local setup uses `sqlite:///demographics.db` by default. To use another database URL, set the `DATABASE_URL` environment variable before starting the application.

## API examples

### Check service health

```bash
curl http://localhost:8000/health
```

Example response:

```json
{
  "status": "ok",
  "database": "ok"
}
```

### Query demographic records

```bash
curl "http://localhost:8000/regions/1/demographics?year=2015&indicator_type=aging&age_category=Seniors%2065%2B&limit=50"
```

The response includes the matching records, the total number of records before pagination, and the filters used for the query.

## Endpoint overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Check API and database availability |
| `GET` | `/countries` | List supported countries |
| `GET` | `/regions` | List regions with optional country filtering and pagination |
| `GET` | `/indicators` | List indicators and record counts |
| `GET` | `/years` | List available years |
| `GET` | `/regions/{region_id}/summary` | Return available years, indicators, and record count |
| `GET` | `/regions/{region_id}/demographics` | Query demographic records with filters and pagination |

Full request and response schemas are available in the generated documentation at `/docs`.

## Data model

The database contains three main entities:

- `Country`: a unique two-letter country code and country name
- `Region`: a unique region name linked to a country
- `DemographicRecord`: an indicator value linked to a region, year, and age category

A demographic record is unique by the combination of:

```text
region_id + year + indicator_type + age_category
```

This constraint makes database seeding safe to repeat and prevents accidental duplicate observations.

## Data ingestion

The seed process reads the following files from `data/`:

| File | Indicator | Region column | Value column |
| --- | --- | --- | --- |
| `fert.csv` | fertility | `region_std` | `OBS_VALUE` |
| `migration.csv` | migration | `geo` | `OBS_VALUE` |
| `mort.csv` | mortality | `region_std` | `T:Total` |
| `aging.csv` | aging | `region_std` | `T:Total` |

The loader checks required columns, converts years and values to numeric types, skips malformed numeric rows with logging, and rolls back the complete transaction if seeding fails.

## Project structure

```text
.
├── app/
│   ├── data_loader.py  # CSV parsing and record creation
│   ├── database.py     # SQLAlchemy engine, sessions, and initialization
│   ├── main.py         # FastAPI application and endpoints
│   ├── models.py       # Database models and constraints
│   └── seed.py         # Dataset configuration and database seeding
├── data/               # Source demographic CSV files
├── docker-compose.yml  # Local container orchestration
├── Dockerfile          # Application image definition
└── requirements.txt    # Python dependencies
```

## Future improvements

- Add unit and integration tests with pytest
- Add PostgreSQL support

## AI assistance

AI tools were used to generate this README based on the project, create the Dockerfile, assist with debugging, and format the code.
