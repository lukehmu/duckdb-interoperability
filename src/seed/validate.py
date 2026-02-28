"""Row-level Pydantic validation for every data source (``uv run validate``)."""

import os
import sys

import duckdb
from pydantic import ValidationError

from . import PROJECT_ROOT
from .schemas import Artist, Artwork
from .sources import SOURCES


def validate_rows(rows, columns, model):
    """Validate each row against a Pydantic model, returning (row, error) pairs."""
    errors = []
    for row in rows:
        data = dict(zip(columns, row))
        try:
            model.model_validate(data)
        except ValidationError as e:
            errors.append((data, e))
    return errors


def main():
    os.chdir(PROJECT_ROOT)

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
