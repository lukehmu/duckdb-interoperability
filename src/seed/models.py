from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Artist(Base):
    __tablename__ = "artists"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    birth_year = Column(Integer)
    nationality = Column(String(50))


class Artwork(Base):
    __tablename__ = "artworks"
    id = Column(Integer, primary_key=True)
    artist_id = Column(Integer, ForeignKey("artists.id"))
    title = Column(String(200))
    year = Column(Integer)
    medium = Column(String(100))
