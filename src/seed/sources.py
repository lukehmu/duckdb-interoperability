"""DuckDB SQL definitions for every data source.

Each entry maps a source name to the SQL needed to query its artists and
artworks tables.  An optional ``setup`` key handles extension loading or
ATTACH statements that must run before the queries.
"""

SOURCES = {
    "CSV": {
        "artists": "SELECT * FROM 'data/csv/artists.csv'",
        "artworks": "SELECT * FROM 'data/csv/artworks.csv'",
    },
    "TSV": {
        "artists": "SELECT * FROM read_csv('data/tsv/artists.tsv', delim='\t')",
        "artworks": "SELECT * FROM read_csv('data/tsv/artworks.tsv', delim='\t')",
    },
    "JSON": {
        "artists": "SELECT * FROM 'data/json/artists.json'",
        "artworks": "SELECT * FROM 'data/json/artworks.json'",
    },
    "Parquet": {
        "artists": "SELECT * FROM 'data/parquet/artists.parquet'",
        "artworks": "SELECT * FROM 'data/parquet/artworks.parquet'",
    },
    "Excel": {
        "setup": "LOAD rusty_sheet;",
        "artists": "SELECT * FROM read_sheet('data/excel/artists_artworks.xlsx', sheet='Artists')",
        "artworks": "SELECT * FROM read_sheet('data/excel/artists_artworks.xlsx', sheet='Artworks')",
    },
    "DuckDB": {
        "setup": "ATTACH 'data/duckdb/test_data.duckdb' AS duckdb_db (TYPE DUCKDB);",
        "artists": "SELECT * FROM duckdb_db.artists",
        "artworks": "SELECT * FROM duckdb_db.artworks",
    },
    "SQLite": {
        "setup": "ATTACH 'data/sqlite/test_data.db' AS sqlite_db (TYPE SQLITE);",
        "artists": "SELECT * FROM sqlite_db.artists",
        "artworks": "SELECT * FROM sqlite_db.artworks",
    },
    "PostgreSQL": {
        "setup": "ATTACH 'dbname=testdb user=testuser password=testpass host=127.0.0.1 port=5432' AS pg (TYPE POSTGRES);",
        "artists": "SELECT * FROM pg.artists",
        "artworks": "SELECT * FROM pg.artworks",
    },
    "MySQL": {
        "setup": "LOAD mysql_scanner; ATTACH 'host=127.0.0.1 port=3306 user=testuser password=testpass database=testdb' AS mysql_db (TYPE MYSQL);",
        "artists": "SELECT * FROM mysql_db.artists",
        "artworks": "SELECT * FROM mysql_db.artworks",
    },
    "MariaDB": {
        "setup": "LOAD mysql_scanner; ATTACH 'host=127.0.0.1 port=3307 user=testuser password=testpass database=testdb' AS maria_db (TYPE MYSQL);",
        "artists": "SELECT * FROM maria_db.artists",
        "artworks": "SELECT * FROM maria_db.artworks",
    },
    "MongoDB": {
        "setup": "LOAD mongo; ATTACH 'host=127.0.0.1 port=27017 user=testuser password=testpass authsource=admin' AS mongo_db (TYPE MONGO);",
        "artists": "SELECT * FROM mongo_db.testdb.artists",
        "artworks": "SELECT * FROM mongo_db.testdb.artworks",
    },
    # read_xml infers small integers as Int32; cast to BIGINT for consistency
    "XML": {
        "setup": "LOAD webbed;",
        "artists": "SELECT id::BIGINT AS id, name, birth_year::BIGINT AS birth_year, nationality FROM read_xml('data/xml/artists.xml')",
        "artworks": "SELECT id::BIGINT AS id, artist_id::BIGINT AS artist_id, title, year::BIGINT AS year, medium FROM read_xml('data/xml/artworks.xml')",
    },
    "MinIO": {
        "setup": "CREATE SECRET (TYPE S3, KEY_ID 'minioadmin', SECRET 'minioadmin', ENDPOINT '127.0.0.1:9000', URL_STYLE 'path', USE_SSL false);",
        "artists": "SELECT * FROM read_parquet('s3://testbucket/artists.parquet')",
        "artworks": "SELECT * FROM read_parquet('s3://testbucket/artworks.parquet')",
    },
}
