import shutil
import uuid
from pathlib import Path

import pytest

WATCHED_CSV = """Date,Name,Year,Letterboxd URI
2023-01-10,The Godfather,1972,https://boxd.it/abc
2023-03-15,Akira,1988,https://boxd.it/def
2023-07-23,Perfect Blue,1997,https://boxd.it/ghi
2024-02-01,Dune,2021,https://boxd.it/jkl
2024-05-10,Alien,1979,https://boxd.it/mno
"""

RATINGS_CSV = """Date,Name,Year,Letterboxd URI,Rating
2023-01-10,The Godfather,1972,https://boxd.it/abc,5
2023-03-15,Akira,1988,https://boxd.it/def,4.5
2023-07-23,Perfect Blue,1997,https://boxd.it/ghi,5
2024-02-01,Dune,2021,https://boxd.it/jkl,3.5
"""

CACHE_CSV = """Name,Year,Countries
The Godfather,1972,United States of America
Akira,1988,Japan
"""


@pytest.fixture
def workspace_tmp_path() -> Path:
    base_dir = Path.cwd() / ".test-workspace"
    base_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = base_dir / f"case-{uuid.uuid4().hex}"
    tmp_dir.mkdir()
    try:
        yield tmp_dir
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def watched_csv(workspace_tmp_path: Path) -> Path:
    path = workspace_tmp_path / "watched.csv"
    path.write_text(WATCHED_CSV, encoding="utf-8")
    return path


@pytest.fixture
def ratings_csv(workspace_tmp_path: Path) -> Path:
    path = workspace_tmp_path / "ratings.csv"
    path.write_text(RATINGS_CSV, encoding="utf-8")
    return path


@pytest.fixture
def cache_csv(workspace_tmp_path: Path) -> Path:
    path = workspace_tmp_path / "cache.csv"
    path.write_text(CACHE_CSV, encoding="utf-8")
    return path
