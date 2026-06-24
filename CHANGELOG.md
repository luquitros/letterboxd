# Changelog

Todas as mudancas relevantes deste projeto serao documentadas aqui.

## [Unreleased]

### Added
- Painel "raio-x do seu cinema" no dashboard com insights automaticos: dias ativos, maior sequencia de dias seguidos, dia da semana mais cinefilo, mes recorde, decada dominante e nota media.
- Painel "dia da semana favorito" e painel "concentracao por mes", derivados das datas do heatmap.
- Busca/filtro na lista de destaques nota maxima.
- Contadores animados (count-up) nos numeros principais da landing e do dashboard.
- Animacao de entrada escalonada nos cartoes e paineis, respeitando `prefers-reduced-motion`.

## [0.1.0] - 2026-04-20

### Added
- Estrutura de pacote Python em `src/letterboxd/`.
- CLI principal com comandos `letterboxd`, `letterboxd-build-data` e `letterboxd-build-site`.
- Camada de configuracao tipada com suporte a `.env` e variaveis de ambiente.
- Templates HTML para landing, dashboard e wrapped generator.
- Suite de testes separada por dominio em `tests/`.
- Lint com Ruff, type checking com mypy e cobertura com pytest-cov no CI.
- Licenca MIT.

### Changed
- Separacao entre pipeline de dados e renderizacao do site.
- Melhor tratamento de cache, TTL e limpeza explicita de cache.
- Melhoria de UX das paginas geradas em `docs/`.

### Fixed
- Ajustes de encoding e entidades HTML em textos do dashboard.
- Correcoes de tipagem para CI com mypy.
