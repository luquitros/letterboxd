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

```powershell
python -m pip install -r requirements.txt
```

## Uso

Coloque seus arquivos exportados do Letterboxd em `data/`, especialmente `watched.csv`.

Estrutura minima esperada:

```text
data/
  watched.csv
  ratings.csv  # opcional
```

Depois rode:

```powershell
python src/main.py
```

Modos uteis:

```powershell
python src/main.py --no-open
python src/main.py --stats-only
python src/main.py --map-only
python src/main.py --refresh-cache
```

O script vai:

- gerar `docs/stats.json`
- gerar `docs/mapa_cinema.html`
- atualizar `docs/index.html` e `docs/dashboard.html`
- abrir o dashboard no navegador usando um servidor local simples

## Qualidade

Lint local:

```powershell
ruff check src
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
