#!/usr/bin/env bash
set -euo pipefail

DUCKDB="${HOME}/.duckdb/cli/latest/duckdb"
PASS=0
FAIL=0

run_test() {
    local name="$1"
    local sql="$2"
    if output=$("$DUCKDB" -c "$sql" 2>&1); then
        echo "  PASS  $name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  $name"
        echo "        $output" | head -3
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Flat Files ==="

run_test "CSV: select" \
    "SELECT count(*) AS n FROM 'csv/artists.csv' HAVING n = 5;"

run_test "CSV: join" \
    "SELECT count(*) AS n FROM 'csv/artists.csv' a JOIN 'csv/artworks.csv' w ON a.id = w.artist_id HAVING n = 10;"

run_test "TSV: select" \
    "SELECT count(*) AS n FROM read_csv('tsv/artists.tsv', delim='\t') HAVING n = 5;"

run_test "TSV: join + aggregation" \
    "SELECT a.nationality, count(*) AS n FROM read_csv('tsv/artists.tsv', delim='\t') a JOIN read_csv('tsv/artworks.tsv', delim='\t') w ON a.id = w.artist_id GROUP BY a.nationality HAVING n = 2;"

run_test "JSON: select" \
    "SELECT count(*) AS n FROM 'json/artists.json' HAVING n = 5;"

run_test "JSON: join + window function" \
    "SELECT count(*) AS n FROM (SELECT ROW_NUMBER() OVER (PARTITION BY a.id ORDER BY w.year) AS rn FROM 'json/artists.json' a JOIN 'json/artworks.json' w ON a.id = w.artist_id) HAVING n = 10;"

run_test "Parquet: select" \
    "SELECT count(*) AS n FROM 'parquet/artists.parquet' HAVING n = 5;"

run_test "Parquet: join + FILTER aggregation" \
    "SELECT count(*) FILTER (WHERE w.medium = 'Oil on canvas') AS oil FROM 'parquet/artists.parquet' a JOIN 'parquet/artworks.parquet' w ON a.id = w.artist_id HAVING oil = 5;"

run_test "Excel: select" \
    "LOAD rusty_sheet; SELECT count(*) AS n FROM read_sheet('excel/artists_artworks.xlsx', sheet='Artists') HAVING n = 5;"

run_test "Excel: join across sheets" \
    "LOAD rusty_sheet; SELECT count(*) AS n FROM read_sheet('excel/artists_artworks.xlsx', sheet='Artists') a JOIN read_sheet('excel/artists_artworks.xlsx', sheet='Artworks') w ON a.id = w.artist_id HAVING n = 10;"

echo ""
echo "=== Databases ==="

run_test "SQLite: select" \
    "SELECT count(*) AS n FROM sqlite_scan('sqlite/test_data.db', 'artists') HAVING n = 5;"

run_test "SQLite: join + CTE" \
    "WITH t AS (SELECT a.name, MIN(w.year) AS first_work FROM sqlite_scan('sqlite/test_data.db', 'artists') a JOIN sqlite_scan('sqlite/test_data.db', 'artworks') w ON a.id = w.artist_id GROUP BY a.name) SELECT count(*) AS n FROM t HAVING n = 5;"

run_test "PostgreSQL: select" \
    "ATTACH 'dbname=testdb user=testuser password=testpass host=127.0.0.1 port=5432' AS pg (TYPE POSTGRES); SELECT count(*) AS n FROM pg.artists HAVING n = 5;"

run_test "PostgreSQL: join + ROLLUP" \
    "ATTACH 'dbname=testdb user=testuser password=testpass host=127.0.0.1 port=5432' AS pg (TYPE POSTGRES); SELECT count(*) AS n FROM (SELECT a.nationality, w.medium, count(*) FROM pg.artists a JOIN pg.artworks w ON a.id = w.artist_id GROUP BY ROLLUP(a.nationality, w.medium)) HAVING n = 13;"

run_test "MySQL: select" \
    "LOAD mysql_scanner; ATTACH 'host=127.0.0.1 port=3306 user=testuser password=testpass database=testdb' AS mysql_db (TYPE MYSQL); SELECT count(*) AS n FROM mysql_db.artists HAVING n = 5;"

run_test "MySQL: join + EXISTS subquery" \
    "LOAD mysql_scanner; ATTACH 'host=127.0.0.1 port=3306 user=testuser password=testpass database=testdb' AS mysql_db (TYPE MYSQL); SELECT count(*) AS n FROM mysql_db.artists a WHERE EXISTS (SELECT 1 FROM mysql_db.artworks w WHERE w.artist_id = a.id AND w.medium LIKE 'Oil%') HAVING n = 3;"

run_test "MariaDB: select" \
    "LOAD mysql_scanner; ATTACH 'host=127.0.0.1 port=3307 user=testuser password=testpass database=testdb' AS maria_db (TYPE MYSQL); SELECT count(*) AS n FROM maria_db.artists HAVING n = 5;"

run_test "MariaDB: join + NTILE window" \
    "LOAD mysql_scanner; ATTACH 'host=127.0.0.1 port=3307 user=testuser password=testpass database=testdb' AS maria_db (TYPE MYSQL); SELECT count(*) AS n FROM (SELECT NTILE(4) OVER (ORDER BY w.year) AS q FROM maria_db.artists a JOIN maria_db.artworks w ON a.id = w.artist_id) HAVING n = 10;"

run_test "MongoDB: select" \
    "LOAD mongo; ATTACH 'host=127.0.0.1 port=27017 user=testuser password=testpass authsource=admin' AS mongo_db (TYPE MONGO); SELECT count(*) AS n FROM mongo_db.testdb.artists HAVING n = 5;"

run_test "MongoDB: join + CROSS JOIN" \
    "LOAD mongo; ATTACH 'host=127.0.0.1 port=27017 user=testuser password=testpass authsource=admin' AS mongo_db (TYPE MONGO); SELECT count(*) AS n FROM mongo_db.testdb.artists a JOIN mongo_db.testdb.artworks w ON a.id = w.artist_id HAVING n = 10;"

echo ""
echo "=== Object Storage ==="

MINIO_SECRET="CREATE SECRET (TYPE S3, KEY_ID 'minioadmin', SECRET 'minioadmin', ENDPOINT '127.0.0.1:9000', URL_STYLE 'path', USE_SSL false);"

run_test "MinIO: read parquet" \
    "${MINIO_SECRET} SELECT count(*) AS n FROM read_parquet('s3://testbucket/artists.parquet') HAVING n = 5;"

run_test "MinIO: join" \
    "${MINIO_SECRET} SELECT count(*) AS n FROM read_parquet('s3://testbucket/artists.parquet') a JOIN read_parquet('s3://testbucket/artworks.parquet') w ON a.id = w.artist_id HAVING n = 10;"

run_test "MinIO: write + read back" \
    "${MINIO_SECRET} COPY (SELECT 42 AS answer) TO 's3://testbucket/_test_write.parquet' (FORMAT PARQUET); SELECT count(*) AS n FROM read_parquet('s3://testbucket/_test_write.parquet') WHERE answer = 42 HAVING n = 1;"

echo ""
echo "=== Cross-source ==="

run_test "CSV artists x Parquet artworks" \
    "SELECT count(*) AS n FROM 'csv/artists.csv' a JOIN 'parquet/artworks.parquet' w ON a.id = w.artist_id HAVING n = 10;"

run_test "JSON artists x SQLite artworks" \
    "SELECT count(*) AS n FROM 'json/artists.json' a JOIN sqlite_scan('sqlite/test_data.db', 'artworks') w ON a.id = w.artist_id HAVING n = 10;"

run_test "PostgreSQL artists x MinIO artworks" \
    "ATTACH 'dbname=testdb user=testuser password=testpass host=127.0.0.1 port=5432' AS pg (TYPE POSTGRES); ${MINIO_SECRET} SELECT count(*) AS n FROM pg.artists a JOIN read_parquet('s3://testbucket/artworks.parquet') w ON a.id = w.artist_id HAVING n = 10;"

run_test "MySQL artists x Parquet artworks" \
    "LOAD mysql_scanner; ATTACH 'host=127.0.0.1 port=3306 user=testuser password=testpass database=testdb' AS mysql_db (TYPE MYSQL); SELECT count(*) AS n FROM mysql_db.artists a JOIN 'parquet/artworks.parquet' w ON a.id = w.artist_id HAVING n = 10;"

run_test "MariaDB artists x TSV artworks" \
    "LOAD mysql_scanner; ATTACH 'host=127.0.0.1 port=3307 user=testuser password=testpass database=testdb' AS maria_db (TYPE MYSQL); SELECT count(*) AS n FROM maria_db.artists a JOIN read_csv('tsv/artworks.tsv', delim='\t') w ON a.id = w.artist_id HAVING n = 10;"

run_test "SQLite artists x JSON artworks" \
    "SELECT count(*) AS n FROM sqlite_scan('sqlite/test_data.db', 'artists') a JOIN 'json/artworks.json' w ON a.id = w.artist_id HAVING n = 10;"

run_test "MongoDB artists x CSV artworks" \
    "LOAD mongo; ATTACH 'host=127.0.0.1 port=27017 user=testuser password=testpass authsource=admin' AS mongo_db (TYPE MONGO); SELECT count(*) AS n FROM mongo_db.testdb.artists a JOIN 'csv/artworks.csv' w ON a.id = w.artist_id HAVING n = 10;"

run_test "Excel artists x PostgreSQL artworks" \
    "LOAD rusty_sheet; ATTACH 'dbname=testdb user=testuser password=testpass host=127.0.0.1 port=5432' AS pg (TYPE POSTGRES); SELECT count(*) AS n FROM read_sheet('excel/artists_artworks.xlsx', sheet='Artists') a JOIN pg.artworks w ON a.id = w.artist_id HAVING n = 10;"

run_test "PostgreSQL artists x MySQL artworks" \
    "LOAD mysql_scanner; ATTACH 'dbname=testdb user=testuser password=testpass host=127.0.0.1 port=5432' AS pg (TYPE POSTGRES); ATTACH 'host=127.0.0.1 port=3306 user=testuser password=testpass database=testdb' AS mysql_db (TYPE MYSQL); SELECT count(*) AS n FROM pg.artists a JOIN mysql_db.artworks w ON a.id = w.artist_id HAVING n = 10;"

echo ""
echo "================================"
echo "  Results: ${PASS} passed, ${FAIL} failed"
echo "================================"

[ "$FAIL" -eq 0 ] || exit 1
