# Slash Commands — Construção do CRUD JusBrasil

Conjunto de comandos para executar o `PLANO_CRUD_CONSOLIDADO.md` passo a passo no Claude Code.

---

## Estrutura no repositório

```text
.claude/
  commands/
    crud-setup.md
    step1-domain.md
    step2-application.md
    step3-infrastructure.md
    step4-presentation.md
    step5-tests.md
    columnconfig-special.md
    report-special.md
    reportexecution-infra.md
    dictionary-apply.md
docs/
  PLANO_CRUD_CONSOLIDADO.md   # referência única de princípios e specs
```

O plano consolidado é o "norte". Os comandos abaixo apontam para seções específicas dele em vez de repetir conteúdo. Você cria um arquivo `.md` para cada comando no diretório `.claude/commands/` com o conteúdo entre os separadores `---`.

---

## 0 · `/crud-setup`

```markdown
---
description: Setup inicial antes de qualquer entidade — interfaces compartilhadas e decisões pendentes
---

Antes de criar qualquer entidade, execute o setup inicial do CRUD.

LEIA: `docs/PLANO_CRUD_CONSOLIDADO.md`, seções 2, 4 e 12.

PERGUNTE ao usuário (uma única vez, agrupadas):
1. Storage em dev: `local` (disco) ou `minio` (docker-compose)?
2. Storage de progresso da execução: `postgres` ou `redis`?
3. Confirma RQ + Redis como fila, ou prefere outra?

Anote as respostas em `docs/CRUD_DECISIONS.md`.

CRIE:
- `src/domain/shared/file_storage.py` — `ABC FileStorage` com `save`, `load_stream`, `delete`, `generate_presigned_url`.
- `src/domain/shared/processing_queue.py` — `ABC ProcessingQueue` com `enqueue_execution(execution_id)`.
- `src/infrastructure/persistence/base.py` — confirme que `Base` e `TimestampMixin` existem; se não, crie.

NÃO implemente as classes concretas (S3/MinIO, RQ) agora. Apenas as interfaces.

AO TERMINAR: liste arquivos criados, mostre o `CRUD_DECISIONS.md`, e PARE.
```

---

## 1 · `/step1-domain <entidade>`

```markdown
---
description: Step 1 — Camada de domínio (entities, exceptions, repositories) para uma entidade
argument-hint: <entidade>
---

Implemente o Step 1 (Domínio) para a entidade: $ARGUMENTS

LEIA antes de codar:
1. `docs/PLANO_CRUD_CONSOLIDADO.md`, seções 2 (decisões), 5 (Step 1) e 6.X (especificação da entidade $ARGUMENTS).

CRIE em `src/domain/<modulo>/`:
- `entities.py` — `@dataclass` com os campos exatos listados em 6.X. Sem imports externos.
- `exceptions.py` — exceções listadas em 6.X. Herda de `Exception` (ou `ValueError` quando for validação semântica).
- `repositories.py` — `ABC` com métodos async: `create`, `get_by_id(id, user_id)`, `list_by_user(user_id, offset, limit) -> tuple[list[Entity], int]`, `update`, `delete(id, user_id)`.

REGRAS:
- Nenhum import de FastAPI, SQLAlchemy, Pydantic ou libs externas.
- Sem comentários que explicam *o que* o código faz; apenas *por que* quando não óbvio.
- Não adicione features, abstrações ou validações além das listadas em 6.X.

AO TERMINAR:
- Liste os arquivos criados com uma linha cada descrevendo o conteúdo.
- PARE. Não avance para o Step 2.
```

---

## 2 · `/step2-application <entidade>`

```markdown
---
description: Step 2 — Camada de aplicação (DTOs e use cases CRUD padrão) para uma entidade
argument-hint: <entidade>
---

Implemente o Step 2 (Aplicação) para a entidade: $ARGUMENTS

PRÉ-REQUISITO: Step 1 desta entidade já concluído.

LEIA: `docs/PLANO_CRUD_CONSOLIDADO.md`, seções 5 (Step 2) e 6.X (verificar desvios).

⚠ SE a seção 6.X listar desvios na coluna "Update/Delete" ou indicar use cases não-padrão (ex.: Report, ColumnConfig), PARE e avise o usuário para rodar o comando especializado correspondente em vez deste.

CRIE em `src/application/<modulo>/`:
- `dtos.py` — `@dataclass` para `Create<Entidade>Input`, `Update<Entidade>Input`, `<Entidade>Output`, `List<Entidade>Input`, `PaginatedOutput`.
- `create_<modulo>.py` — `Create<Entidade>UseCase`.
- `get_<modulo>.py` — `Get<Entidade>UseCase` (lança `NotFound`).
- `list_<modulo>.py` — `List<Entidade>UseCase` (cap em 100, calcula offset).
- `update_<modulo>.py` — `Update<Entidade>UseCase` (partial update, atualiza `updated_at`).
- `delete_<modulo>.py` — `Delete<Entidade>UseCase` (lança `NotFound`).

REGRAS:
- Sem imports de FastAPI ou SQLAlchemy.
- Use cases dependem apenas das interfaces do domínio.
- Valide regras de negócio descritas em 6.X (nome vazio, duplicado, etc.).

AO TERMINAR:
- Liste os arquivos criados.
- PARE. Não avance para o Step 3.
```

---

## 3 · `/step3-infrastructure <entidade>`

```markdown
---
description: Step 3 — Modelo SQLAlchemy, repositório concreto e migração Alembic
argument-hint: <entidade>
---

Implemente o Step 3 (Infraestrutura) para a entidade: $ARGUMENTS

PRÉ-REQUISITO: Steps 1 e 2 concluídos.

LEIA: `docs/PLANO_CRUD_CONSOLIDADO.md`, seções 5 (Step 3), 6.X e 8 (schema SQL de referência).

CRIE:
- `src/infrastructure/persistence/models/<modulo>.py` — modelo SQLAlchemy herdando de `Base` + `TimestampMixin`. FK com `ondelete="CASCADE"`. Tipos exatamente como em 6.X. Índices na FK e em `created_at`. Constraints únicas conforme 6.X. Método privado `_to_entity()`.
- `src/infrastructure/persistence/repositories/<modulo>_repository.py` — implementa a interface do domínio com `AsyncSession`. `list_by_user` usa `func.count().over()` para retornar `(items, total)` em uma query.

GERE a migração:
- Execute `alembic revision --autogenerate -m "add_<modulo>_table"`.
- Revise o arquivo gerado: confirme que `upgrade()` e `downgrade()` batem com o schema da seção 8.
- NÃO aplique a migração. Apenas mostre o caminho do arquivo gerado e o diff dele.

REGRAS:
- Não importar nada de `application` ou `presentation`.
- Mapeamento entidade ↔ modelo encapsulado em `_to_entity()` e em método inverso no `create`/`update`.

AO TERMINAR:
- Liste arquivos criados + caminho da migração.
- Comando para aplicar: `alembic upgrade head`.
- PARE.
```

---

## 4 · `/step4-presentation <entidade>`

```markdown
---
description: Step 4 — Schemas Pydantic, dependências e rotas FastAPI
argument-hint: <entidade>
---

Implemente o Step 4 (Apresentação) para a entidade: $ARGUMENTS

PRÉ-REQUISITO: Step 3 concluído e migração aplicada.

LEIA: `docs/PLANO_CRUD_CONSOLIDADO.md`, seções 5 (Step 4) e 6.X (verificar endpoints).

⚠ SE 6.X listar desvios em endpoints (Report, ColumnConfig, Dictionary apply), implemente apenas o que é CRUD padrão aqui e avise o usuário sobre o comando especializado para os demais.

CRIE:
- `src/presentation/http/schemas/<modulo>.py` — `Create<Entidade>Request`, `Update<Entidade>Request` (campos opcionais), `<Entidade>Response` (com `model_config = ConfigDict(from_attributes=True)`), `Paginated<Entidade>Response`.
- `src/presentation/http/dependencies/<modulo>.py` — uma factory por caso de uso, recebendo `AsyncSession = Depends(get_db)`.
- `src/presentation/http/routes/<modulo>.py` — `POST /`, `GET /` (com `page`/`page_size` query), `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`. Todas com `Depends(get_current_user)`. Mapeie: `NotFound → 404`, `AlreadyExists → 409`, `ValueError → 422`.

REGISTRE o router em `src/presentation/http/app.py`.

REGRAS:
- Schemas Pydantic não atravessam para `application`.
- A rota só traduz HTTP ↔ DTO e DTO ↔ HTTP. Lógica fica no use case.

AO TERMINAR:
- Liste arquivos criados.
- Mostre o cURL de exemplo para `POST` e `GET /`.
- PARE.
```

---

## 5 · `/step5-tests <entidade>`

```markdown
---
description: Step 5 — Testes unitários (com fakes) e de integração (com Postgres real)
argument-hint: <entidade>
---

Implemente o Step 5 (Testes) para a entidade: $ARGUMENTS

PRÉ-REQUISITO: Step 4 concluído.

LEIA: `docs/PLANO_CRUD_CONSOLIDADO.md`, seções 5 (Step 5) e 6.X.

CRIE:
- `tests/unit/application/test_<modulo>.py`:
  - `InMemory<Entidade>Repository` definido no próprio arquivo (dict como storage).
  - Casos: create OK, create duplicado, get OK, get inexistente, list paginada, update OK, update inexistente, delete OK, delete inexistente.

- `tests/integration/test_<modulo>_api.py`:
  - Fixture `AsyncClient` (httpx) + Postgres real (testcontainers ou banco dedicado).
  - Fluxo completo: autenticar → criar → listar → buscar → atualizar → deletar.
  - **Isolamento**: criar com usuário A, confirmar que usuário B vê 404.

REGRAS:
- Não usar mocks de SQLAlchemy nos testes unitários — use o fake repository.
- Integração só com banco real.

AO TERMINAR:
- Rode `pytest tests/unit/application/test_<modulo>.py -v` e `pytest tests/integration/test_<modulo>_api.py -v`.
- Cole o resumo do pytest.
- PARE.
```

---

## 6 · `/columnconfig-special`

```markdown
---
description: Use cases e endpoints especializados de ColumnConfig (detect + PUT em lote + PATCH)
---

Implemente os desvios de `ColumnConfig` descritos na seção 6.2 do plano.

PRÉ-REQUISITO: Steps 1, 3 de `ColumnConfig` concluídos. NÃO rode o Step 2 nem Step 4 padrão para esta entidade.

LEIA: `docs/PLANO_CRUD_CONSOLIDADO.md`, seções 6.2 e 7 (fluxo "Detecção de colunas").

CRIE em `src/application/projects/`:
- `configure_columns.py` — `ConfigureColumnsUseCase`: substitui todas as configs de um projeto pelo conjunto enviado (idempotente).
- `update_column_config.py` — `UpdateColumnConfigUseCase`: edição pontual de uma coluna.
- `detect_columns.py` — `DetectColumnsUseCase`: lê header e amostras (até 100 linhas, 5 valores distintos por coluna), retorna estrutura sem persistir.

CRIE em `src/infrastructure/spreadsheet/`:
- `column_detector.py` — implementação concreta com `pandas` ou `openpyxl`/`csv` para CSV e XLSX.

CRIE em `src/presentation/http/routes/column_configs.py`:
- `POST /projects/{project_id}/columns/detect` — multipart upload temporário, não persiste.
- `PUT /projects/{project_id}/columns` — substitui o conjunto.
- `PATCH /projects/{project_id}/columns/{column_id}` — edição pontual.

CRIE também os schemas Pydantic correspondentes em `schemas/column_configs.py`.

TESTES: adicione casos em `tests/unit/application/test_column_configs.py` para os 3 use cases novos + cenário de coluna com amostras nulas em detect.

AO TERMINAR: liste arquivos, mostre cURL do `detect` e do `PUT`, PARE.
```

---

## 7 · `/report-special`

```markdown
---
description: Use cases e endpoints especializados de Report (upload, feedback, reprocess, download, status)
---

Implemente os desvios de `Report` descritos na seção 6.3 do plano.

PRÉ-REQUISITO: 
- Steps 1 e 3 de `Report` concluídos (com modelo e repositório).
- `ReportExecution` Step 3 concluído (rodar `/reportexecution-infra` antes).
- NÃO rode os Steps 2 e 4 padrão para `Report`.

LEIA: `docs/PLANO_CRUD_CONSOLIDADO.md`, seções 6.3, 6.4 e 7 (fluxos de upload, download, reprocessamento).

CRIE em `src/application/reports/`:
- `upload_report.py` — `UploadReportUseCase`: valida tamanho, valida colunas contra config, salva arquivo via `FileStorage`, cria `Report` + `ReportExecution(status=QUEUED)` com snapshot da config, publica job via `ProcessingQueue`.
- `list_reports.py` — `ListReportsUseCase`: lista com status da última execução.
- `get_report.py` — `GetReportUseCase`: report + todas as executions.
- `get_execution_status.py` — `GetExecutionStatusUseCase`: para polling.
- `download_result.py` — `DownloadResultUseCase`: valida `status==READY`, retorna presigned URL ou stream conforme formato pedido.
- `submit_feedback.py` — `SubmitFeedbackUseCase`: aprova ou rejeita com motivo, atualiza `approval_status`.
- `reprocess_report.py` — `ReprocessReportUseCase`: cria nova execution reutilizando `original_file_key`.

EXCEÇÕES: `ColumnsMismatch`, `ReportNotReady`, `InvalidApprovalTransition` em `src/domain/reports/exceptions.py`.

CRIE em `src/presentation/http/routes/reports.py`:
- `POST /projects/{id}/reports` — multipart upload.
- `GET /projects/{id}/reports` — paginado.
- `GET /reports/{id}`.
- `GET /reports/{id}/executions/{exec_id}/status`.
- `GET /reports/{id}/executions/{exec_id}/download?format=csv|xlsx`.
- `POST /reports/{id}/reprocess`.
- `PATCH /reports/{id}/feedback`.

REGRAS:
- Streaming em uploads (`aiofiles`); jamais `await file.read()` inteiro.
- Não acoplar boto3/storage concreto no use case — sempre pela interface.

TESTES: cobertura mínima dos cenários da seção 6.3 + ColumnsMismatch.

AO TERMINAR: liste arquivos, mostre cURL de upload com `-F`, PARE.
```

---

## 8 · `/reportexecution-infra`

```markdown
---
description: Apenas Step 3 de ReportExecution (não é CRUD — só modelo e repositório)
---

Crie apenas a infraestrutura de `ReportExecution`. Não há use cases próprios nem rotas próprias para esta entidade.

LEIA: `docs/PLANO_CRUD_CONSOLIDADO.md`, seções 6.4 e 8.

CRIE:
- `src/domain/reports/entities.py` — adicione `ReportExecution` à existente (não recrie o arquivo).
- `src/domain/reports/repositories.py` — adicione `ABC ReportExecutionRepository` com `create`, `get_by_id`, `list_by_report`, `update_status`, `update_progress`, `set_result`.
- `src/infrastructure/persistence/models/report_execution.py` — modelo SQLAlchemy com check constraint em `status` conforme seção 8.
- `src/infrastructure/persistence/repositories/execution_repository.py`.

GERE migração: `alembic revision --autogenerate -m "add_report_executions_table"`.

NÃO crie use cases, schemas Pydantic ou rotas. Esses são responsabilidade do `/report-special`.

AO TERMINAR: liste arquivos, mostre caminho da migração, PARE.
```

---

## 9 · `/dictionary-apply`

```markdown
---
description: Use case e endpoint para aplicar entrada do dicionário em uma ColumnConfig
---

Implemente a aplicação de entradas do dicionário global em colunas de projeto.

PRÉ-REQUISITO: CRUD padrão de `GlobalDictionaryEntry` (steps 1–5) e `ColumnConfig` concluídos.

LEIA: `docs/PLANO_CRUD_CONSOLIDADO.md`, seções 6.5 e 7 (fluxo "Aplicar entrada do dicionário").

CRIE:
- `src/application/dictionary/apply_entry_to_column.py` — `ApplyEntryToColumnUseCase`:
  - Carrega entrada (validando user_id).
  - Carrega ColumnConfig (validando que pertence ao mesmo user).
  - Faz merge conforme `kind`:
    - `NORMALIZATION_PRESET` → sobrescreve `normalizations`.
    - `CATEGORY_LIST` → sobrescreve `categories` e seta `classify=true`.
    - `CLASSIFICATION_INSTRUCTION` → guarda em metadata.
  - Persiste ColumnConfig.

CRIE rota em `src/presentation/http/routes/dictionary.py`:
- `POST /projects/{project_id}/columns/{column_id}/apply-entry/{entry_id}` → 200 com `<ColumnConfig>Response`.

EXCEÇÕES tratadas: `DictionaryEntryNotFound → 404`, `ColumnConfigNotFound → 404`, `IncompatibleEntryKind → 422`.

TESTES: unitário cobrindo os 3 kinds + caso de entry de outro usuário (404).

AO TERMINAR: liste arquivos, PARE.
```

---

## Sequência de execução por entidade

Rode `/crud-setup` uma vez. Depois siga a ordem da seção 3 do plano:

| Ordem | Entidade | Comandos a rodar (na sequência) |
|---|---|---|
| 1 | Project | `/step1-domain project` → `/step2-application project` → `/step3-infrastructure project` → `/step4-presentation project` → `/step5-tests project` |
| 2 | GlobalDictionaryEntry | mesmos 5 comandos genéricos com `globaldictionaryentry` |
| 3 | ColumnConfig | `/step1-domain columnconfig` → `/step3-infrastructure columnconfig` → `/columnconfig-special` → `/step5-tests columnconfig` |
| 4 | Report (parte 1) | `/step1-domain report` → `/step3-infrastructure report` → `/reportexecution-infra` |
| 5 | Report (parte 2) | `/report-special` → `/step5-tests report` |
| 6 | Dictionary apply | `/dictionary-apply` |

---

## Como o Claude Code deve se comportar entre comandos

Cada comando termina com **PARE** explícito. Isso é proposital: depois de cada step você revisa o resultado (arquivos, diff, output de testes) antes de avançar. Se o resultado estiver bom, rode o próximo comando da sequência.

Se algum step falhar em testes, **não** rode o próximo. Corrija o atual e re-execute o `/stepN-...` (ele pode sobrescrever; idempotente para arquivos definidos no plano).

---

## Mantendo o plano vivo

Quando uma decisão técnica mudar durante a implementação:

1. Atualize `docs/PLANO_CRUD_CONSOLIDADO.md` na seção afetada.
2. Adicione 1 linha em `docs/CRUD_DECISIONS.md` registrando o que mudou e por quê.
3. Re-rode apenas os steps das entidades afetadas pela mudança.

O plano é a fonte de verdade; os comandos só executam o que ele descreve.
