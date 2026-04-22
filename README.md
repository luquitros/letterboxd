# letterboxd

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![HTML5](https://img.shields.io/badge/HTML5-templates-orange.svg)](src/letterboxd/templates/)
[![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC.svg)](tests/)
[![Lint](https://img.shields.io/badge/lint-ruff-46a758.svg)](https://docs.astral.sh/ruff/)
[![Type Checked](https://img.shields.io/badge/type%20checked-mypy-2a6db2.svg)](https://mypy-lang.org/)

Gera um dashboard pessoal do Letterboxd com mapa de paises de producao e estatisticas em `docs/`.

## Configuracao

1. Crie um arquivo `.env` na raiz do projeto.
2. Copie o conteudo de `.env.example`.
3. Preencha sua chave da TMDB:

```env
TMDB_API_KEY=sua_chave_aqui
```

Opcionalmente, voce tambem pode sobrescrever diretorios padrao:

```env
LETTERBOXD_DATA_DIR=data
LETTERBOXD_DOCS_DIR=docs
```

## Instalacao

Instale as dependencias e o pacote em modo editavel:

```powershell
python -m pip install -r requirements.txt -e .
```

## Uso

Coloque seus arquivos exportados do Letterboxd em `data/`, especialmente `watched.csv`.

Estrutura minima esperada:

```text
data/
  watched.csv
  ratings.csv  # opcional
```

Execucao recomendada apos instalar com `-e .`:

```powershell
letterboxd
```

Alternativa equivalente como modulo:

```powershell
python -m letterboxd
```

Compatibilidade antiga:

```powershell
python src/main.py
```

Modos uteis:

```powershell
letterboxd --no-open
letterboxd --stats-only
letterboxd --map-only
letterboxd --refresh-cache
letterboxd --clear-cache
letterboxd-build-data
letterboxd-build-data --clear-cache
letterboxd-build-site --open
```

O script vai:

- gerar artefatos de dados em `docs/stats.json` e `docs/mapa_cinema.html`
- renderizar `docs/index.html`, `docs/dashboard.html` e `docs/wrapped_generator.html` a partir desses artefatos
- abrir o dashboard no navegador usando um servidor local simples

## Estrutura Python

A logica principal agora vive no pacote `letterboxd` dentro de `src/letterboxd/`.

Arquitetura atual:

- `letterboxd.pipeline` cuida da camada de dados: CSVs, cache, TMDB, `stats.json` e mapa
- `letterboxd.models` concentra domain dataclasses como filmes e entradas de cache
- `letterboxd.site_renderer` cuida apenas da renderizacao das paginas em `docs/`
- `letterboxd.build_data` expoe um comando dedicado para atualizar so os artefatos de dados
- `letterboxd.build_site` expoe um comando dedicado para renderizar o site a partir dos artefatos existentes
- `letterboxd.main` faz a orquestracao completa da CLI, combinando dados + renderizacao + abertura do navegador

- `letterboxd` usa o entry point `letterboxd.main:main`
- `letterboxd-build-data` usa `letterboxd.build_data:main`
- `letterboxd-build-site` usa `letterboxd.build_site:main`
- `python -m letterboxd` continua funcionando via `src/letterboxd/__main__.py`
- `src/main.py` e `src/stats_only.py` ficaram como wrappers finos para compatibilidade
- templates HTML vivem em `src/letterboxd/templates/`

## Qualidade

Lint local:

```powershell
python -m ruff check src tests
```

Type checking dos modulos principais:

```powershell
python -m mypy
```

Cobertura de testes:

```powershell
python -m pytest -v
```

Para ver cobertura explicitamente:

```powershell
python -m pytest -v --cov=letterboxd --cov-report=term-missing
```

O projeto agora usa cobertura via `pytest-cov` no CI e ela tambem fica disponivel localmente depois de atualizar as dependencias. O CI tambem inclui scan de segredos com `gitleaks` antes dos testes.

## Testes

A suite foi separada por dominio em `tests/`:

- `tests/test_cache.py`
- `tests/test_cli.py`
- `tests/test_config.py`
- `tests/test_mapa.py`
- `tests/test_pipeline.py`
- `tests/test_site_renderer.py`
- `tests/test_stats.py`
- `tests/test_tmdb.py`

Para rodar tudo:

```powershell
python -m pytest -v
```

## Problemas comuns

- `TMDB_API_KEY nao configurada`
  Crie um arquivo `.env` na raiz com `TMDB_API_KEY=sua_chave_aqui`.

- `Arquivo nao encontrado: ...watched.csv`
  Exporte o `watched.csv` do Letterboxd e coloque-o em `data/`.

- `ratings.csv nao encontrado`
  Nao e erro. O projeto continua, apenas sem estatisticas de avaliacao.

- `Arquivo nao encontrado: ...stats.json` ao rodar `letterboxd-build-site`
  Execute `letterboxd-build-data` primeiro para gerar os artefatos antes da renderizacao.

## Changelog

As mudancas principais do projeto ficam registradas em [CHANGELOG.md](CHANGELOG.md).

## Licenca

Distribuido sob a licenca MIT. Veja [LICENSE](LICENSE).

