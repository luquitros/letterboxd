# letterboxd

Gera um dashboard pessoal do Letterboxd com mapa de paises de producao e estatisticas em `docs/`.

## Configuracao

1. Crie um arquivo `.env` na raiz do projeto.
2. Copie o conteudo de `.env.example`.
3. Preencha sua chave da TMDB:

```env
TMDB_API_KEY=sua_chave_aqui
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

Execucao recomendada como pacote:

```powershell
python -m letterboxd
```

Compatibilidade antiga:

```powershell
python src/main.py
```

Modos uteis:

```powershell
python -m letterboxd --no-open
python -m letterboxd --stats-only
python -m letterboxd --map-only
python -m letterboxd --refresh-cache
```

O script vai:

- gerar `docs/stats.json`
- gerar `docs/mapa_cinema.html`
- renderizar `docs/index.html`, `docs/dashboard.html` e `docs/wrapped_generator.html` a partir de templates limpos
- abrir o dashboard no navegador usando um servidor local simples

## Estrutura Python

A logica principal agora vive no pacote `letterboxd` dentro de `src/letterboxd/`.

- `python -m letterboxd` usa `src/letterboxd/__main__.py`
- `src/main.py` e `src/stats_only.py` ficaram como wrappers finos para compatibilidade
- templates HTML vivem em `src/letterboxd/templates/`

## Qualidade

Lint local:

```powershell
python -m ruff check src
```

## Testes

```powershell
python -m pytest src/test_projeto.py -v
```

## Problemas comuns

- `TMDB_API_KEY nao configurada`
  Crie um arquivo `.env` na raiz com `TMDB_API_KEY=sua_chave_aqui`.

- `Arquivo nao encontrado: ...watched.csv`
  Exporte o `watched.csv` do Letterboxd e coloque-o em `data/`.

- `ratings.csv nao encontrado`
  Nao e erro. O projeto continua, apenas sem estatisticas de avaliacao.
