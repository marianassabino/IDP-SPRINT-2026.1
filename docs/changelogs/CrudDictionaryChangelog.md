# Changelog — DictionaryEntry

## O que foi feito

Implementação completa do CRUD de dicionário em 5 camadas (Clean Architecture), com suporte a dois escopos: **dicionário global do usuário** e **dicionário por projeto**, onde o projeto tem precedência em conflitos.

### Domínio (`src/domain/dictionary/`)
- `DictionaryEntryKind` — enum com 3 tipos: `NORMALIZATION_PRESET`, `CATEGORY_LIST`, `CLASSIFICATION_INSTRUCTION`.
- `DictionaryEntry` — dataclass com `id`, `user_id`, `project_id` (nullable), `kind`, `name`, `payload (dict)`, timestamps.
- `DictionaryEntryNotFound`, `DictionaryEntryNameAlreadyExists` — exceções de domínio.
- `DictionaryEntryRepository` (ABC) — interface com `create`, `get_by_id`, `list_global`, `list_by_project`, `list_merged`, `update`, `delete`.

### Aplicação (`src/application/dictionary/`)
- `CreateDictionaryEntryUseCase` — cria entrada global (`project_id=None`) ou de projeto.
- `GetDictionaryEntryUseCase` — busca por `id + user_id`.
- `ListDictionaryEntriesUseCase` — delega para `list_global` ou `list_by_project` conforme `project_id` do input.
- `UpdateDictionaryEntryUseCase` — partial update de `name` e/ou `payload` (`kind` imutável).
- `DeleteDictionaryEntryUseCase` — verifica existência antes de deletar.

### Infraestrutura (`src/infrastructure/persistence/`)
- `DictionaryEntryModel` — tabela `dictionary_entries` com `project_id` nullable e dois índices únicos parciais:
  - `uq_dictionary_global` — `UNIQUE (user_id, kind, name) WHERE project_id IS NULL`
  - `uq_dictionary_project` — `UNIQUE (project_id, kind, name) WHERE project_id IS NOT NULL`
- `SqlAlchemyDictionaryEntryRepository` — implementa todos os métodos do repositório, incluindo `list_merged` que aplica a regra de precedência em memória após a query.
- Migration: `4ec107f5c802_add_dictionary_entries_table.py` — aplicada.

### Apresentação (`src/presentation/http/`)
- Dois routers: `router` (`/dictionary`) e `project_dictionary_router` (`/projects/{project_id}/dictionary`).
- 10 endpoints no total (5 por escopo).
- Exceções mapeadas: `NotFound → 404`, `AlreadyExists → 409`, `ValueError → 422`.

### Testes
- **48/48 passando** (inclui testes anteriores de Project sem regressão).
- 13 testes unitários com `InMemoryDictionaryEntryRepository` — cobre merge com precedência, isolamento de escopos, duplicatas, paginação.
- 14 testes de integração com Postgres real — cobre CRUD global, CRUD de projeto, isolamento entre usuários, coexistência de mesmo nome em escopos diferentes.

---

## Como funciona

```
Request HTTP
    └─> FastAPI route (routes/dictionary.py)
            └─> Depends(get_current_user_id)        # valida JWT do cookie
            └─> Use Case (application/dictionary/)
                    └─> DictionaryEntryRepository (domain interface)
                            └─> SqlAlchemyDictionaryEntryRepository (infrastructure)
                                    └─> AsyncSession → Postgres
```

### Dois escopos

| `project_id` | Escopo | Constraint de unicidade |
|---|---|---|
| `NULL` | Global (usuário) | `UNIQUE (user_id, kind, name) WHERE project_id IS NULL` |
| `<uuid>` | Projeto | `UNIQUE (project_id, kind, name) WHERE project_id IS NOT NULL` |

### Regra de precedência (merge)

Usado pelo pipeline de processamento via `list_merged(user_id, project_id, kind)`:

```
Global:  "MP" → "ministerio_publico"    (NORMALIZATION_PRESET, name="Preset A")
Projeto: "MP" → "ministerio-publico"    (NORMALIZATION_PRESET, name="Preset A")

Resultado do merge → entrada do PROJETO vence (mesmo kind + name)
Entradas globais sem override continuam válidas
```

---

## Endpoints disponíveis

### Dicionário Global (`/dictionary`)

| Método | Rota | Status | Descrição |
|---|---|---|---|
| POST | `/dictionary` | 201 | Cria entrada no dicionário global do usuário |
| GET | `/dictionary?kind=&page=&page_size=` | 200 | Lista entradas globais (filtro opcional por kind) |
| GET | `/dictionary/{id}` | 200 / 404 | Busca entrada por id |
| PATCH | `/dictionary/{id}` | 200 / 404 / 409 | Atualiza name e/ou payload |
| DELETE | `/dictionary/{id}` | 204 / 404 | Remove entrada |

### Dicionário de Projeto (`/projects/{project_id}/dictionary`)

| Método | Rota | Status | Descrição |
|---|---|---|---|
| POST | `/projects/{project_id}/dictionary` | 201 | Cria entrada no dicionário do projeto |
| GET | `/projects/{project_id}/dictionary?kind=&page=&page_size=` | 200 | Lista entradas do projeto (filtro opcional por kind) |
| GET | `/projects/{project_id}/dictionary/{id}` | 200 / 404 | Busca entrada por id |
| PATCH | `/projects/{project_id}/dictionary/{id}` | 200 / 404 / 409 | Atualiza name e/ou payload |
| DELETE | `/projects/{project_id}/dictionary/{id}` | 204 / 404 | Remove entrada |

### Regras de negócio

- `kind` é imutável após a criação — define a categoria semântica da entrada.
- O mesmo `name` pode existir em escopo global e de projeto simultaneamente (são registros distintos).
- Deleção do projeto cascateia as entradas do dicionário do projeto via FK `ON DELETE CASCADE`.
- Deleção do usuário cascateia todas as entradas (globais e de projeto).

---

## O que falta (ordem do plano)

| # | Entidade / Feature | Complexidade | Desvios do CRUD padrão |
|---|---|---|---|
| 1 | `ColumnConfig` | Média | `PUT` em lote + endpoint de detecção de colunas (sem `POST`/`DELETE` individuais) |
| 2 | `Report` | Alta | Upload multipart; sem `DELETE`; `SubmitFeedback` no lugar de `Update` |
| 3 | `ReportExecution` | Alta | Não é CRUD; criada internamente; só `GET status` e `GET download` |
| 4 | Fila de processamento | — | Celery+Redis (outro colega) |
| 5 | Aplicar entrada do dicionário em coluna | Baixa | `POST /projects/{id}/columns/{col_id}/apply-entry/{entry_id}` — implementado junto ao `ColumnConfig` |
| 6 | Reprocessamento | Baixa | `POST /reports/{id}/reprocess` |
| 7 | Integração com pipeline | — | `list_merged` já existe; worker precisa chamá-lo para montar contexto de normalização/classificação |
