"""Static seed data for 5 artists and 10 artworks (2 per artist)."""

ARTIST_FIELDS = ["id", "name", "birth_year", "nationality"]
ARTWORK_FIELDS = ["id", "artist_id", "title", "year", "medium"]

ARTISTS_RAW = [
    {"id": 1, "name": "Vincent van Gogh", "birth_year": 1853, "nationality": "Dutch"},
    {"id": 2, "name": "Frida Kahlo", "birth_year": 1907, "nationality": "Mexican"},
    {"id": 3, "name": "Pablo Picasso", "birth_year": 1881, "nationality": "Spanish"},
    {"id": 4, "name": "Yayoi Kusama", "birth_year": 1929, "nationality": "Japanese"},
    {
        "id": 5,
        "name": "Jean-Michel Basquiat",
        "birth_year": 1960,
        "nationality": "American",
    },
]

ARTWORKS_RAW = [
    {
        "id": 1,
        "artist_id": 1,
        "title": "The Starry Night",
        "year": 1889,
        "medium": "Oil on canvas",
    },
    {
        "id": 2,
        "artist_id": 1,
        "title": "Sunflowers",
        "year": 1888,
        "medium": "Oil on canvas",
    },
    {
        "id": 3,
        "artist_id": 2,
        "title": "The Two Fridas",
        "year": 1939,
        "medium": "Oil on canvas",
    },
    {
        "id": 4,
        "artist_id": 2,
        "title": "Self-Portrait with Thorn Necklace",
        "year": 1940,
        "medium": "Oil on masonite",
    },
    {
        "id": 5,
        "artist_id": 3,
        "title": "Guernica",
        "year": 1937,
        "medium": "Oil on canvas",
    },
    {
        "id": 6,
        "artist_id": 3,
        "title": "Les Demoiselles d'Avignon",
        "year": 1907,
        "medium": "Oil on canvas",
    },
    {
        "id": 7,
        "artist_id": 4,
        "title": "Infinity Mirrored Room",
        "year": 1965,
        "medium": "Mixed media installation",
    },
    {"id": 8, "artist_id": 4, "title": "Pumpkin", "year": 1994, "medium": "Sculpture"},
    {
        "id": 9,
        "artist_id": 5,
        "title": "Untitled (Skull)",
        "year": 1981,
        "medium": "Acrylic and oilstick on canvas",
    },
    {
        "id": 10,
        "artist_id": 5,
        "title": "Hollywood Africans",
        "year": 1983,
        "medium": "Acrylic and oilstick on canvas",
    },
]
