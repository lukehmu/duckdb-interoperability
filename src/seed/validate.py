import os
import sys

import duckdb
from pydantic import ValidationError

from .schemas import Artist, Artwork

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
    "XML": {
        "setup": "LOAD webbed;",
        "artists": "SELECT * FROM read_xml('data/xml/artists.xml')",
        "artworks": "SELECT * FROM read_xml('data/xml/artworks.xml')",
    },
    "MinIO": {
        "setup": "CREATE SECRET (TYPE S3, KEY_ID 'minioadmin', SECRET 'minioadmin', ENDPOINT '127.0.0.1:9000', URL_STYLE 'path', USE_SSL false);",
        "artists": "SELECT * FROM read_parquet('s3://testbucket/artists.parquet')",
        "artworks": "SELECT * FROM read_parquet('s3://testbucket/artworks.parquet')",
    },
}


def validate_rows(rows, columns, model):
    errors = []
    for row in rows:
        data = dict(zip(columns, row))
        try:
            model.model_validate(data)
        except ValidationError as e:
            errors.append((data, e))
    return errors


def main():
    output_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    os.chdir(output_dir)

    passed = 0
    failed = 0

    for name, source in SOURCES.items():
        con = duckdb.connect()
        try:
            setup = source.get("setup", "")
            if setup:
                con.execute(setup)

            for table, model in [("artists", Artist), ("artworks", Artwork)]:
                result = con.execute(source[table]).fetchall()
                columns = [desc[0] for desc in con.description]
                errors = validate_rows(result, columns, model)

                if errors:
                    failed += 1
                    print(f"  FAIL  {name}: {table}")
                    for data, err in errors[:3]:
                        print(f"        row {data}: {err.error_count()} error(s)")
                        for e in err.errors()[:2]:
                            print(f"          {e['loc']}: {e['msg']}")
                else:
                    passed += 1
                    print(f"  PASS  {name}: {table} ({len(result)} rows)")
        except Exception as e:
            failed += 2
            print(f"  FAIL  {name}: {e}")
        finally:
            con.close()

    print()
    print("================================")
    print(f"  Results: {passed} passed, {failed} failed")
    print("================================")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
