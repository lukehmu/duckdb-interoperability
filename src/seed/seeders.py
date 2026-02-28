import csv
import json
import os
import subprocess
import xml.etree.ElementTree as ET

import pymongo
from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .data import ARTIST_FIELDS, ARTISTS_RAW, ARTWORK_FIELDS, ARTWORKS_RAW
from .models import Artist, Artwork, Base


def seed_sql(url, label):
    engine = create_engine(url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all([Artist(**d) for d in ARTISTS_RAW])
        session.add_all([Artwork(**d) for d in ARTWORKS_RAW])
        session.commit()
    engine.dispose()
    print(f"{label}: seeded {len(ARTISTS_RAW)} artists, {len(ARTWORKS_RAW)} artworks")


def seed_mongo(user, password, db_name):
    client = pymongo.MongoClient(
        f"mongodb://{user}:{password}@127.0.0.1:27017/{db_name}?authSource=admin"
    )
    db = client[db_name]
    db.artists.drop()
    db.artworks.drop()
    db.artists.insert_many([dict(d) for d in ARTISTS_RAW])
    db.artworks.insert_many([dict(d) for d in ARTWORKS_RAW])
    client.close()
    print(f"MongoDB: seeded {len(ARTISTS_RAW)} artists, {len(ARTWORKS_RAW)} artworks")


def seed_csv(delimiter, ext):
    for name, fields, data in [
        ("artists", ARTIST_FIELDS, ARTISTS_RAW),
        ("artworks", ARTWORK_FIELDS, ARTWORKS_RAW),
    ]:
        with open(f"{ext}/{name}.{ext}", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, delimiter=delimiter)
            w.writeheader()
            w.writerows(data)
    print(f"{ext.upper()}: created {ext}/artists.{ext}, {ext}/artworks.{ext}")


def seed_json():
    for name, data in [("artists", ARTISTS_RAW), ("artworks", ARTWORKS_RAW)]:
        with open(f"json/{name}.json", "w") as f:
            json.dump(data, f, indent=2)
    print("JSON: created json/artists.json, json/artworks.json")


def seed_parquet():
    duckdb = os.path.expanduser("~/.duckdb/cli/latest/duckdb")
    for name in ["artists", "artworks"]:
        subprocess.run(
            [
                duckdb,
                "-c",
                f"COPY (SELECT * FROM 'csv/{name}.csv') TO 'parquet/{name}.parquet' (FORMAT PARQUET);",
            ],
            check=True,
        )
    print("Parquet: created parquet/artists.parquet, parquet/artworks.parquet")


def seed_excel():
    wb = Workbook()
    ws1 = wb.active
    ws1.title = "Artists"
    ws1.append(ARTIST_FIELDS)
    for d in ARTISTS_RAW:
        ws1.append([d[f] for f in ARTIST_FIELDS])

    ws2 = wb.create_sheet("Artworks")
    ws2.append(ARTWORK_FIELDS)
    for d in ARTWORKS_RAW:
        ws2.append([d[f] for f in ARTWORK_FIELDS])

    wb.save("excel/artists_artworks.xlsx")
    print("Excel: created excel/artists_artworks.xlsx (Artists & Artworks sheets)")


def seed_xml():
    for name, fields, data in [
        ("artists", ARTIST_FIELDS, ARTISTS_RAW),
        ("artworks", ARTWORK_FIELDS, ARTWORKS_RAW),
    ]:
        root = ET.Element("rows")
        for row in data:
            elem = ET.SubElement(root, "row")
            for field in fields:
                child = ET.SubElement(elem, field)
                child.text = str(row[field])
        tree = ET.ElementTree(root)
        ET.indent(tree)
        tree.write(f"xml/{name}.xml", xml_declaration=True, encoding="unicode")
    print("XML: created xml/artists.xml, xml/artworks.xml")


def seed_duckdb():
    cli = os.path.expanduser("~/.duckdb/cli/latest/duckdb")
    db_path = "duckdb/test_data.duckdb"
    if os.path.exists(db_path):
        os.remove(db_path)
    subprocess.run(
        [
            cli,
            db_path,
            "-c",
            "CREATE TABLE artists AS SELECT * FROM 'csv/artists.csv';"
            " CREATE TABLE artworks AS SELECT * FROM 'csv/artworks.csv';",
        ],
        check=True,
    )
    print("DuckDB: created duckdb/test_data.duckdb")


def seed_minio(user, password, bucket):
    duckdb = os.path.expanduser("~/.duckdb/cli/latest/duckdb")
    secret_sql = (
        f"CREATE SECRET minio_secret (TYPE S3, KEY_ID '{user}', SECRET '{password}', "
        f"ENDPOINT '127.0.0.1:9000', URL_STYLE 'path', USE_SSL false);"
    )
    for name in ["artists", "artworks"]:
        subprocess.run(
            [
                duckdb,
                "-c",
                f"{secret_sql} COPY (SELECT * FROM 'parquet/{name}.parquet') TO 's3://{bucket}/{name}.parquet' (FORMAT PARQUET);",
            ],
            check=True,
        )
    print(
        f"MinIO: seeded s3://{bucket}/artists.parquet, s3://{bucket}/artworks.parquet"
    )
