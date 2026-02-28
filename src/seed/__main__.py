import os

from .seeders import (
    seed_csv,
    seed_excel,
    seed_json,
    seed_duckdb,
    seed_minio,
    seed_mongo,
    seed_parquet,
    seed_sql,
    seed_xml,
)

OUTPUT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


def main():
    os.chdir(OUTPUT_DIR)

    for d in ["csv", "tsv", "json", "xml", "parquet", "excel", "sqlite", "duckdb"]:
        os.makedirs(f"data/{d}", exist_ok=True)

    db_user = os.environ.get("DB_USER", "testuser")
    db_password = os.environ.get("DB_PASSWORD", "testpass")
    db_name = os.environ.get("DB_NAME", "testdb")

    # Databases
    seed_sql(
        f"mysql+mysqlconnector://{db_user}:{db_password}@127.0.0.1:3306/{db_name}",
        "MySQL",
    )
    seed_sql(
        f"mysql+mysqlconnector://{db_user}:{db_password}@127.0.0.1:3307/{db_name}",
        "MariaDB",
    )
    seed_sql(
        f"postgresql+psycopg2://{db_user}:{db_password}@127.0.0.1:5432/{db_name}",
        "PostgreSQL",
    )
    seed_sql("sqlite:///data/sqlite/test_data.db", "SQLite")
    seed_mongo(db_user, db_password, db_name)

    # Flat files
    seed_csv(",", "csv")
    seed_csv("\t", "tsv")
    seed_json()
    seed_xml()
    seed_parquet()
    seed_duckdb()
    seed_excel()

    # Object storage
    minio_user = os.environ.get("MINIO_USER", "minioadmin")
    minio_password = os.environ.get("MINIO_PASSWORD", "minioadmin")
    minio_bucket = os.environ.get("MINIO_BUCKET", "testbucket")
    seed_minio(minio_user, minio_password, minio_bucket)

    print("Done!")


if __name__ == "__main__":
    main()
