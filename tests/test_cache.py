from letterboxd.cache import cache_miss, carregar_cache, miss_sentinel, salvar_cache


def test_carregar_cache_existente(cache_csv):
    df, cache = carregar_cache(cache_csv)
    assert len(df) == 2
    assert ("The Godfather", "1972") in cache
    assert cache[("Akira", "1988")] == "Japan"


def test_carregar_cache_inexistente(tmp_path):
    df, cache = carregar_cache(tmp_path / "nao_existe.csv")
    assert len(df) == 0
    assert cache == {}


def test_cache_miss_sentinel():
    assert cache_miss("__NOT_FOUND__") is True
    assert cache_miss("Japan") is False
    assert cache_miss("") is False


def test_miss_sentinel_valor():
    assert miss_sentinel() == "__NOT_FOUND__"


def test_salvar_cache(cache_csv, tmp_path):
    df, _ = carregar_cache(cache_csv)
    novos = [{"Name": "Alien", "Year": "1979", "Countries": "United Kingdom"}]
    out = tmp_path / "cache_out.csv"
    salvar_cache(df, novos, out)
    df2, cache = carregar_cache(out)
    assert len(df2) == 3
    assert ("Alien", "1979") in cache


def test_salvar_cache_vazio_nao_cria_arquivo(cache_csv, tmp_path):
    df, _ = carregar_cache(cache_csv)
    out = tmp_path / "nao_criado.csv"
    salvar_cache(df, [], out)
    assert not out.exists()
