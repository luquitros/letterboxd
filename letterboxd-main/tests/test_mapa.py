from letterboxd.mapa import get_iso3


def test_iso3_paises_comuns():
    assert get_iso3("Brazil") == "BRA"
    assert get_iso3("Japan") == "JPN"
    assert get_iso3("France") == "FRA"
    assert get_iso3("Germany") == "DEU"


def test_iso3_overrides():
    assert get_iso3("South Korea") == "KOR"
    assert get_iso3("Russia") == "RUS"
    assert get_iso3("United States of America") == "USA"
    assert get_iso3("Hong Kong") == "HKG"
    assert get_iso3("Taiwan") == "TWN"


def test_iso3_pais_invalido():
    assert get_iso3("Narnia") is None
    assert get_iso3("") is None


def test_iso3_united_kingdom():
    assert get_iso3("United Kingdom") == "GBR"
