# DuckDB Test

A test project for querying multiple data sources with DuckDB — databases, flat files, and cloud services from a single SQL interface.

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- [DuckDB CLI](https://duckdb.org/docs/installation/) — install with `curl https://install.duckdb.org | sh`
- [Docker](https://docs.docker.com/get-docker/)

## Setup

Start the database containers:

```bash
docker compose up -d
```

Seed all databases and generate flat files:

```bash
uv run seed
```

## Data Sources

### Summary

| Source         | Type      | Read | Write | JOIN | Extension          | Notes                          |
|----------------|----------|:----:|:-----:|:----:|---------------------|--------------------------------|
| CSV            | File     | Yes  | Yes   | Yes  | Built-in            | `COPY TO (FORMAT CSV)`         |
| TSV            | File     | Yes  | Yes   | Yes  | Built-in            | `COPY TO (DELIMITER '\t')`     |
| JSON           | File     | Yes  | Yes   | Yes  | Built-in            | `COPY TO (FORMAT JSON)`        |
| Parquet        | File     | Yes  | Yes   | Yes  | Built-in            | `COPY TO (FORMAT PARQUET)`     |
| Excel          | File     | Yes  | No    | Yes  | `rusty_sheet`       | Read via `read_sheet()`        |
| SQLite         | File DB  | Yes  | Yes   | Yes  | `sqlite_scanner`    | Full ATTACH support            |
| PostgreSQL     | Docker   | Yes  | Yes   | Yes  | `postgres_scanner`  | Full ATTACH support            |
| MySQL          | Docker   | Yes  | Yes   | Yes  | `mysql_scanner`     | Full ATTACH support            |
| MariaDB        | Docker   | Yes  | Yes   | Yes  | `mysql_scanner`     | Full ATTACH support            |
| MongoDB        | Docker   | Yes  | No    | Yes  | `mongo`             | Read-only, no CREATE TABLE     |
| MinIO (S3)     | Docker   | Yes  | Yes   | Yes  | `httpfs`            | Full S3 read/write             |
| Google Sheets  | Cloud    | Yes  | Partial| Yes | `gsheets`           | Write requires existing sheet  |

**JOIN** = can be used as a source in cross-source JOINs with any other source above.

### Databases

| Database       | Port  | Type     |
|----------------|-------|----------|
| MySQL 8.4      | 3306  | MySQL    |
| MariaDB 11.8   | 3307  | MySQL    |
| PostgreSQL 16  | 5432  | Postgres |
| MongoDB 7      | 27017 | Mongo    |
| MinIO          | 9000/9001 | S3   |
| SQLite         | —     | File     |

### Flat Files

| Format  | Location                                                  |
|---------|-----------------------------------------------------------|
| CSV     | `csv/artists.csv`, `csv/artworks.csv`                     |
| TSV     | `tsv/artists.tsv`, `tsv/artworks.tsv`                     |
| JSON    | `json/artists.json`, `json/artworks.json`                 |
| Parquet | `parquet/artists.parquet`, `parquet/artworks.parquet`     |
| Excel   | `excel/artists_artworks.xlsx` (Artists & Artworks sheets) |
| SQLite  | `sqlite/test_data.db`                                     |

### Object Storage

| Service | Location                                                        |
|---------|-----------------------------------------------------------------|
| MinIO   | `s3://testbucket/artists.parquet`, `s3://testbucket/artworks.parquet` |

### Cloud

| Source        | Extension |
|---------------|-----------|
| Google Sheets | `gsheets` |

### Configuration

All credentials and connection details are in `.env`:

- `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_ROOT_PASSWORD` — database credentials
- `MINIO_USER`, `MINIO_PASSWORD`, `MINIO_BUCKET` — MinIO S3 credentials
- `GSHEET_URL` — Google Sheets URL
- `GSHEET_TOKEN` — Google OAuth token (expires after ~1 hour)

## Querying with DuckDB

### Flat files

```bash
duckdb -c "SELECT * FROM 'csv/artists.csv'"
duckdb -c "SELECT * FROM 'parquet/artworks.parquet'"
duckdb -c "SELECT * FROM 'json/artists.json'"
duckdb -c "SELECT * FROM read_csv('tsv/artists.tsv', delim='\t')"
```

```sql
-- Excel (community extension)
LOAD rusty_sheet;
SELECT * FROM read_sheet('excel/artists_artworks.xlsx', sheet='Artists');
```

### Databases

```sql
-- SQLite
SELECT * FROM sqlite_scan('sqlite/test_data.db', 'artists');

-- PostgreSQL
ATTACH 'dbname=testdb user=testuser password=testpass host=127.0.0.1 port=5432' AS pg (TYPE POSTGRES);
SELECT * FROM pg.artists;

-- MySQL
ATTACH 'host=127.0.0.1 port=3306 user=testuser password=testpass database=testdb' AS mysql_db (TYPE MYSQL);
SELECT * FROM mysql_db.artworks;

-- MariaDB
ATTACH 'host=127.0.0.1 port=3307 user=testuser password=testpass database=testdb' AS maria_db (TYPE MYSQL);
SELECT * FROM maria_db.artists;

-- MongoDB (community extension)
LOAD mongo;
ATTACH 'host=127.0.0.1 port=27017 user=testuser password=testpass authsource=admin' AS mongo_db (TYPE MONGO);
SELECT * FROM mongo_db.testdb.artists;
```

### MinIO (S3)

```sql
CREATE SECRET (TYPE S3, KEY_ID 'minioadmin', SECRET 'minioadmin',
    ENDPOINT '127.0.0.1:9000', URL_STYLE 'path', USE_SSL false);

-- Read
SELECT * FROM read_parquet('s3://testbucket/artists.parquet');

-- Write
COPY my_table TO 's3://testbucket/output.parquet' (FORMAT PARQUET);
```

### Google Sheets

```sql
LOAD gsheets;
CREATE SECRET my_gsheet (TYPE gsheet, PROVIDER access_token, TOKEN 'your_token');
SELECT * FROM read_gsheet('your_sheet_url', sheet='Artists');
```

### DuckDB Extensions

| Extension          | Type      | Read | Write | Purpose                    |
|--------------------|-----------|:----:|:-----:|----------------------------|
| [`sqlite_scanner`](https://duckdb.org/docs/extensions/sqlite)   | Core      | Yes  | Yes   | Query SQLite databases     |
| [`postgres_scanner`](https://duckdb.org/docs/extensions/postgres) | Core      | Yes  | Yes   | Query PostgreSQL databases |
| [`mysql_scanner`](https://duckdb.org/docs/extensions/mysql)    | Core      | Yes  | Yes   | Query MySQL/MariaDB        |
| [`httpfs`](https://duckdb.org/docs/extensions/httpfs)           | Core      | Yes  | S3 only| Read HTTP, read/write S3  |
| [`mongo`](https://community-extensions.duckdb.org/extensions/mongo.html)            | Community | Yes  | No    | Query MongoDB              |
| [`gsheets`](https://community-extensions.duckdb.org/extensions/gsheets.html)          | Community | Yes  | Partial| Read/write Google Sheets  |
| [`rusty_sheet`](https://community-extensions.duckdb.org/extensions/rusty_sheet.html)      | Community | Yes  | No    | Read Excel/OpenDocument    |
| [`http_request`](https://community-extensions.duckdb.org/extensions/http_request.html)     | Community | Yes  | —     | HTTP requests from SQL     |

## Testing

Run all 32 tests across every source and cross-source combination:

```bash
bash test.sh
```

The test suite covers four categories:

| Category       | Tests | What's tested                                    |
|----------------|:-----:|--------------------------------------------------|
| Flat Files     | 10    | SELECT, JOIN, aggregation, window, FILTER        |
| Databases      | 10    | SELECT, JOIN, CTE, ROLLUP, EXISTS, NTILE         |
| Object Storage | 3     | Read, JOIN, write + read back                    |
| Cross-source   | 9     | JOINs between different source types (see below) |

### Cross-source interoperability

DuckDB can JOIN data across any combination of sources in a single query. All combinations below are tested and passing:

| Left (artists)  | Right (artworks) | Source types                   |
|------------------|------------------|--------------------------------|
| CSV              | Parquet          | File + File                    |
| JSON             | SQLite           | File + File DB                 |
| SQLite           | JSON             | File DB + File                 |
| MySQL            | Parquet          | Database + File                |
| MariaDB          | TSV              | Database + File                |
| MongoDB          | CSV              | Database + File                |
| Excel            | PostgreSQL       | File + Database                |
| PostgreSQL       | MinIO (S3)       | Database + Object Storage      |
| PostgreSQL       | MySQL            | Database + Database            |

This means you can query across completely different backends — e.g. join a PostgreSQL table with a Parquet file on MinIO, or combine an Excel spreadsheet with a MySQL database — all in standard SQL.

## Development

Lint and format:

```bash
uv run ruff check src/
uv run ruff format src/
```

Type check:

```bash
uv run ty check src/
```

## Project Structure

```
src/seed/              # Python seeder module
├── __init__.py
├── __main__.py        # entry point
├── data.py            # seed data
├── models.py          # SQLAlchemy models
└── seeders.py         # seeder functions per format
test.sh                # DuckDB CLI test suite (32 tests)
docker-compose.yml     # database containers
pyproject.toml         # project config & dev tools
.env                   # credentials & config
README.md
.gitignore
```
