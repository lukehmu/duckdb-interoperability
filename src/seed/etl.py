"""Polars ETL pipeline (``uv run polars``).

For each source: reads artists + artworks via DuckDB, joins into a flat
Polars DataFrame, validates with Pandera, writes to parquet, then compares
all outputs to verify every source produces identical data.
"""

import os
import sys

import duckdb
import polars as pl

from . import PROJECT_ROOT
from .schemas import JoinedSchema
from .sources import SOURCES


# Canonical column order — also drops extra columns (e.g. MongoDB's _id)
COLUMNS = [
    "id",
    "artist_id",
    "title",
    "year",
    "medium",
    "name",
    "birth_year",
    "nationality",
]


def main():
    os.chdir(PROJECT_ROOT)
    os.makedirs("data/polars", exist_ok=True)

    passed = 0
    failed = 0

    for name, source in SOURCES.items():
        con = duckdb.connect()
        try:
            setup = source.get("setup", "")
            if setup:
                con.execute(setup)

            artists_lf = pl.from_arrow(con.execute(source["artists"]).arrow()).lazy()
            artworks_lf = pl.from_arrow(con.execute(source["artworks"]).arrow()).lazy()

            joined_lf = artworks_lf.join(artists_lf, left_on="artist_id", right_on="id")

            joined_df = joined_lf.collect().select(COLUMNS)

            JoinedSchema.validate(joined_df)

            out_path = f"data/polars/{name.lower()}.parquet"
            joined_df.write_parquet(out_path)

            passed += 1
            print(f"  PASS  {name}: {len(joined_df)} rows -> {out_path}")
        except Exception as e:
            failed += 1
            print(f"  FAIL  {name}: {e}")
        finally:
            con.close()

    print()
    print("================================")
    print(f"  Results: {passed} passed, {failed} failed")
    print("================================")

    # Compare all parquet files to each other
    files = sorted(f for f in os.listdir("data/polars") if f.endswith(".parquet"))
    if len(files) >= 2:
        print()
        reference_name = files[0]
        reference = pl.read_parquet(f"data/polars/{reference_name}").sort("id")
        mismatches = 0

        for f in files[1:]:
            other = pl.read_parquet(f"data/polars/{f}").sort("id")
            if reference.equals(other):
                print(f"  MATCH  {reference_name} == {f}")
            else:
                mismatches += 1
                failed += 1
                print(f"  DIFF   {reference_name} != {f}")

        print()
        print("================================")
        if mismatches == 0:
            print(f"  All {len(files)} files are identical")
        else:
            print(f"  {mismatches} file(s) differ from {reference_name}")
        print("================================")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
