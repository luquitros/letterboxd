# Changelog

Todas as mudancas relevantes deste projeto serao documentadas aqui.

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
