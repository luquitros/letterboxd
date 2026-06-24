from datetime import UTC, datetime, timedelta
from pathlib import Path

from letterboxd.cache import cache_miss, carregar_cache, limpar_cache, miss_sentinel, salvar_cache


def test_carregar_cache_existente(cache_csv):
    df, cache = carregar_cache(cache_csv)
    assert len(df) == 2
    assert ("The Godfather", "1972") in cache
    assert cache[("Akira", "1988")] == "Japan"


def test_carregar_cache_inexistente(workspace_tmp_path):
    df, cache = carregar_cache(workspace_tmp_path / "nao_existe.csv")
    assert len(df) == 0
    assert cache == {}


def test_carregar_cache_invalido_retorna_vazio(workspace_tmp_path):
    cache_path = workspace_tmp_path / "cache_quebrado.csv"
    cache_path.write_text('Name,Year,Countries\n"Akira,1988,Japan\n', encoding="utf-8")

    df, cache = carregar_cache(cache_path)

    assert len(df) == 0
    assert cache == {}


def test_carregar_cache_aplica_ttl(cache_csv):
    expired = datetime.now(UTC) - timedelta(days=10)
    cache_csv.write_text(
        "Name,Year,Countries,FetchedAt\nAkira,1988,Japan," + expired.isoformat() + "\n",
        encoding="utf-8",
    )

    df, cache = carregar_cache(cache_csv, ttl_days=1, now=datetime.now(UTC))

    assert len(df) == 0
    assert cache == {}


def test_cache_miss_sentinel():
    assert cache_miss("__NOT_FOUND__") is True
    assert cache_miss("Japan") is False
    assert cache_miss("") is False


def test_miss_sentinel_valor():
    assert miss_sentinel() == "__NOT_FOUND__"


def test_salvar_cache(cache_csv, workspace_tmp_path):
    df, _ = carregar_cache(cache_csv)
    novos = [{"Name": "Alien", "Year": "1979", "Countries": "United Kingdom"}]
    out = workspace_tmp_path / "cache_out.csv"
    salvar_cache(df, novos, out)
    df2, cache = carregar_cache(out)
    assert len(df2) == 3
    assert ("Alien", "1979") in cache
    assert "FetchedAt" in df2.columns


def test_salvar_cache_deduplica_e_prioriza_registro_recente(cache_csv, workspace_tmp_path):
    df, _ = carregar_cache(cache_csv)
    novos = [
        {"Name": "Akira", "Year": "1988", "Countries": "Japan|United States of America"},
        {"Name": "Alien", "Year": "1979", "Countries": "United Kingdom"},
    ]
    out = workspace_tmp_path / "cache_dedup.csv"

    salvar_cache(df, novos, out)
    df2, cache = carregar_cache(out)

    assert len(df2) == 3
    assert cache[("Akira", "1988")] == "Japan|United States of America"


def test_salvar_cache_escrita_atomica_sem_arquivos_temporarios(cache_csv, workspace_tmp_path):
    df, _ = carregar_cache(cache_csv)
    out = workspace_tmp_path / "cache_atomico.csv"

    salvar_cache(df, [{"Name": "Alien", "Year": "1979", "Countries": "United Kingdom"}], out)

    leftovers = list(out.parent.glob(f"{out.stem}_*.tmp"))
    assert leftovers == []


def test_salvar_cache_vazio_nao_cria_arquivo(cache_csv, workspace_tmp_path):
    df, _ = carregar_cache(cache_csv)
    out = workspace_tmp_path / "nao_criado.csv"
    salvar_cache(df, [], out)
    assert not out.exists()


def test_limpar_cache(cache_csv):
    assert limpar_cache(cache_csv) is True
    assert not cache_csv.exists()
    assert limpar_cache(cache_csv) is False


def test_limpar_cache_falha_de_permissao(cache_csv, monkeypatch):
    def fake_unlink(self):
        raise OSError("sem permissao")

    monkeypatch.setattr(Path, "unlink", fake_unlink)

    assert limpar_cache(cache_csv) is False
    assert cache_csv.exists()
