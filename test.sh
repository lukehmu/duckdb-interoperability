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

# --- Source definitions ---

DUCKDB_FILE="ATTACH 'duckdb/test_data.duckdb' AS duckdb_db (TYPE DUCKDB);"
SQLITE="ATTACH 'sqlite/test_data.db' AS sqlite_db (TYPE SQLITE);"
PG="ATTACH 'dbname=testdb user=testuser password=testpass host=127.0.0.1 port=5432' AS pg (TYPE POSTGRES);"
MYSQL="LOAD mysql_scanner; ATTACH 'host=127.0.0.1 port=3306 user=testuser password=testpass database=testdb' AS mysql_db (TYPE MYSQL);"
MARIA="LOAD mysql_scanner; ATTACH 'host=127.0.0.1 port=3307 user=testuser password=testpass database=testdb' AS maria_db (TYPE MYSQL);"
MONGO="LOAD mongo; ATTACH 'host=127.0.0.1 port=27017 user=testuser password=testpass authsource=admin' AS mongo_db (TYPE MONGO);"
MINIO="CREATE SECRET (TYPE S3, KEY_ID 'minioadmin', SECRET 'minioadmin', ENDPOINT '127.0.0.1:9000', URL_STYLE 'path', USE_SSL false);"

# --- Standard queries ---
# Every source runs the same two queries:
#   1. SELECT count(*) expecting 5 artists
#   2. JOIN artists + artworks expecting 10 rows
# Uses error() to assert expected values — returns exit code 1 on mismatch.

ASSERT="CASE WHEN count(*) = %s THEN 'ok' ELSE error('expected %s, got ' || count(*)::VARCHAR) END"
# shellcheck disable=SC2059
SELECT_SQL="SELECT $(printf "$ASSERT" 5 5) FROM %s;"
# shellcheck disable=SC2059
JOIN_SQL="SELECT $(printf "$ASSERT" 10 10) FROM %s a JOIN %s w ON a.id = w.artist_id;"

echo "=== Flat Files ==="

for src in \
	"CSV|'csv/artists.csv'|'csv/artworks.csv'|" \
	"TSV|read_csv('tsv/artists.tsv', delim='\t')|read_csv('tsv/artworks.tsv', delim='\t')|" \
	"JSON|'json/artists.json'|'json/artworks.json'|" \
	"Parquet|'parquet/artists.parquet'|'parquet/artworks.parquet'|" \
	"Excel|read_sheet('excel/artists_artworks.xlsx', sheet='Artists')|read_sheet('excel/artists_artworks.xlsx', sheet='Artworks')|LOAD rusty_sheet;" \
	"XML|read_xml('xml/artists.xml')|read_xml('xml/artworks.xml')|LOAD webbed;"; do

	IFS='|' read -r name artists artworks setup <<<"$src"
	# shellcheck disable=SC2059
	run_test "$name: select" "${setup} $(printf "$SELECT_SQL" "$artists")"
	# shellcheck disable=SC2059
	run_test "$name: join" "${setup} $(printf "$JOIN_SQL" "$artists" "$artworks")"
done

echo ""
echo "=== Databases ==="

for src in \
	"DuckDB|duckdb_db.artists|duckdb_db.artworks|${DUCKDB_FILE}" \
	"SQLite|sqlite_db.artists|sqlite_db.artworks|${SQLITE}" \
	"PostgreSQL|pg.artists|pg.artworks|${PG}" \
	"MySQL|mysql_db.artists|mysql_db.artworks|${MYSQL}" \
	"MariaDB|maria_db.artists|maria_db.artworks|${MARIA}" \
	"MongoDB|mongo_db.testdb.artists|mongo_db.testdb.artworks|${MONGO}"; do

	IFS='|' read -r name artists artworks setup <<<"$src"
	# shellcheck disable=SC2059
	run_test "$name: select" "${setup} $(printf "$SELECT_SQL" "$artists")"
	# shellcheck disable=SC2059
	run_test "$name: join" "${setup} $(printf "$JOIN_SQL" "$artists" "$artworks")"
done

echo ""
echo "=== Object Storage ==="

# shellcheck disable=SC2059
run_test "MinIO: select" \
	"${MINIO} $(printf "$SELECT_SQL" "read_parquet('s3://testbucket/artists.parquet')")"

# shellcheck disable=SC2059
run_test "MinIO: join" \
	"${MINIO} $(printf "$JOIN_SQL" "read_parquet('s3://testbucket/artists.parquet')" "read_parquet('s3://testbucket/artworks.parquet')")"

run_test "MinIO: write + read back" \
	"${MINIO} COPY (SELECT 42 AS answer) TO 's3://testbucket/_test_write.parquet' (FORMAT PARQUET); SELECT CASE WHEN answer = 42 THEN 'ok' ELSE error('expected 42, got ' || answer::VARCHAR) END FROM read_parquet('s3://testbucket/_test_write.parquet');"

echo ""
echo "=== Cross-source ==="

for src in \
	"CSV x Parquet|'csv/artists.csv'|'parquet/artworks.parquet'|" \
	"JSON x SQLite|'json/artists.json'|sqlite_db.artworks|${SQLITE}" \
	"SQLite x JSON|sqlite_db.artists|'json/artworks.json'|${SQLITE}" \
	"MySQL x Parquet|mysql_db.artists|'parquet/artworks.parquet'|${MYSQL}" \
	"MariaDB x TSV|maria_db.artists|read_csv('tsv/artworks.tsv', delim='\t')|${MARIA}" \
	"MongoDB x CSV|mongo_db.testdb.artists|'csv/artworks.csv'|${MONGO}" \
	"Excel x PostgreSQL|read_sheet('excel/artists_artworks.xlsx', sheet='Artists')|pg.artworks|LOAD rusty_sheet; ${PG}" \
	"PostgreSQL x MinIO|pg.artists|read_parquet('s3://testbucket/artworks.parquet')|${PG} ${MINIO}" \
	"PostgreSQL x MySQL|pg.artists|mysql_db.artworks|${MYSQL} ${PG}" \
	"XML x MongoDB|read_xml('xml/artists.xml')|mongo_db.testdb.artworks|LOAD webbed; ${MONGO}" \
	"DuckDB x CSV|duckdb_db.artists|'csv/artworks.csv'|${DUCKDB_FILE}"; do

	IFS='|' read -r name artists artworks setup <<<"$src"
	# shellcheck disable=SC2059
	run_test "$name" "${setup} $(printf "$JOIN_SQL" "$artists" "$artworks")"
done

echo ""
echo "================================"
echo "  Results: ${PASS} passed, ${FAIL} failed"
echo "================================"

[ "$FAIL" -eq 0 ] || exit 1
