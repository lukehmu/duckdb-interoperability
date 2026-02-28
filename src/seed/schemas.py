"""All schemas and models in one place.

- SQLAlchemy: table definitions for PostgreSQL, MySQL, MariaDB, and SQLite.
- Pydantic: row-level validation (``uv run validate``).
- Pandera: DataFrame-level validation (``uv run polars``).
"""

import pandera.polars as pa
from pydantic import BaseModel, Field
from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase


# -- SQLAlchemy (table definitions) -------------------------------------------


class Base(DeclarativeBase):
    pass


class DBArtist(Base):
    __tablename__ = "artists"
    id = Column(BigInteger, primary_key=True)
    name = Column(String(100))
    birth_year = Column(BigInteger)
    nationality = Column(String(50))


class DBArtwork(Base):
    __tablename__ = "artworks"
    id = Column(BigInteger, primary_key=True)
    artist_id = Column(BigInteger, ForeignKey("artists.id"))
    title = Column(String(200))
    year = Column(BigInteger)
    medium = Column(String(100))


# -- Pydantic (row-level) ----------------------------------------------------


class Artist(BaseModel):
    id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=100)
    birth_year: int = Field(ge=1400, le=2025)
    nationality: str = Field(min_length=1, max_length=50)


class Artwork(BaseModel):
    id: int = Field(ge=1)
    artist_id: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=200)
    year: int = Field(ge=1400, le=2025)
    medium: str = Field(min_length=1, max_length=100)


# -- Pandera (DataFrame-level) -----------------------------------------------


class JoinedSchema(pa.DataFrameModel):
    """Pandera schema for the joined artworks + artists DataFrame."""

    id: int = pa.Field(ge=1)
    artist_id: int = pa.Field(ge=1)
    title: str = pa.Field(str_length={"min_value": 1, "max_value": 200})
    year: int = pa.Field(in_range={"min_value": 1400, "max_value": 2025})
    medium: str = pa.Field(str_length={"min_value": 1, "max_value": 100})
    name: str = pa.Field(str_length={"min_value": 1, "max_value": 100})
    birth_year: int = pa.Field(in_range={"min_value": 1400, "max_value": 2025})
    nationality: str = pa.Field(str_length={"min_value": 1, "max_value": 50})
