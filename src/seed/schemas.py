from pydantic import BaseModel, Field


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
