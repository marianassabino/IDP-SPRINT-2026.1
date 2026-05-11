# SPRINT IDP -- JusBrasil

## API

Backend inicial do Normalizador JusBrasil usando FastAPI + Uvicorn, com dependencias gerenciadas por `uv`.

### Rodar com Docker

1. Suba os containers:

```bash
make build
make up
```

2. Aplique as migrations:

```bash
make migrate
```

Health check:

```bash
make health
```

Comandos uteis:

```bash
make help                       # lista todos os comandos
make logs                       # acompanha logs da API
make ps                         # ve status dos containers
make test                       # roda os testes no Docker
make restart                    # reinicia a API
make rebuild                    # reconstroi e sobe do zero
make down                       # derruba a API
make migrate                    # aplica migrations pendentes
make migration MSG="add_foo"    # gera nova migration
make shell-db                   # abre psql no banco
```

### Rodar localmente

```bash
uv sync --dev
uv run uvicorn main:app --app-dir src --reload
```

### Estrutura

```text
src/
  domain/          # entidades e regras de negocio
  application/     # casos de uso
  infrastructure/  # configuracoes e adapters externos
  presentation/    # camada HTTP
```
