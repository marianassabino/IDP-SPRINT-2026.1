# Plano CRUD — Normalizador JusBrasil (consolidado)

Documento único que combina:
- O **inventário e as decisões específicas do projeto** (entidades, schema, fluxos não-CRUD).
- O **procedimento de 5 steps** para construir cada entidade, com regras de Clean Architecture aplicadas.

Pressupõe que o módulo de Auth (`PLANO_AUTH.md`) já está pronto. Toda rota aqui é autenticada e filtrada por `user_id` do token.

---

## 1. Entidades em escopo

| Entidade | Origem no PRD | Tipo de CRUD | Desvios do template |
|---|---|---|---|
| `Project` | HU-02 | CRUD completo | nenhum |
| `ColumnConfig` | HU-03 | CRUD aninhado em projeto | `PUT` em lote para configurar todas as colunas; endpoint extra para detecção |
| `Report` | HU-04, 05, 06, 07 | Create por upload | sem `DELETE` no MVP; `update` substituído por `submit_feedback` |
| `ReportExecution` | HU-06 | Não é CRUD | criada apenas por use case interno; só endpoints `GET` e `download` |
| `DictionaryEntry` | HU-08 | CRUD completo (dois escopos: global e por projeto) | dicionário global do usuário + dicionário por projeto; projeto tem precedência em conflitos; endpoint extra para aplicar entrada em uma coluna |

Fora deste plano: o **pipeline de processamento em si** (normalização determinística + IA). Aqui tratamos só das entidades, dos endpoints e do **disparo** da execução.

---

## 2. Decisões transversais

### Arquitetura

- Clean Architecture: `domain → application → infrastructure → presentation`. Camadas internas não importam camadas externas.
- `domain` nunca importa FastAPI, SQLAlchemy, Pydantic ou bibliotecas externas.
- `application` nunca importa FastAPI ou SQLAlchemy.
- Toda comunicação entre camadas usa DTOs (`@dataclass`) ou entidades de domínio. Nunca modelos SQLAlchemy ou schemas Pydantic atravessando camadas.
- Interfaces de repositório como `ABC` (consistente com o template; não misturar `Protocol` e `ABC` neste módulo).
- Sem comentários explicando *o que* o código faz — só *por que* quando não é óbvio.
- Não adicionar features, abstrações ou error handling além do que cada step pede.

### Persistência

- SQLAlchemy 2.x async + `asyncpg`.
- `Base` e `TimestampMixin` (`created_at`, `updated_at`) já existentes no projeto.
- FK para `users.id` com `ondelete="CASCADE"` em todas as entidades do usuário.
- `String(N)` com tamanho máximo em campos de texto curtos; `Text` em campos livres; `JSONB` em estruturas variáveis.
- `Index` na FK mais consultada e na coluna de ordenação padrão (`created_at`).
- `UniqueConstraint` onde aplicável (ex.: `(user_id, name)` em projetos).
- Listagem usa window function `func.count().over()` para retornar `(items, total)` em uma única query.

### Multi-tenancy

- Toda query de leitura/escrita do usuário parte de `WHERE user_id = current_user.id`.
- `get_by_id` e `delete` recebem `user_id` para garantir isolamento.

### Paginação

- Offset com `page` (≥1) e `page_size` (1–100, cap em 100).
- `offset = (page - 1) * page_size`.
- Resposta padrão: `items`, `total`, `page`, `page_size`, `total_pages`.

### Storage de arquivos

- Arquivos brutos e processados em **AWS S3** em todos os ambientes. Banco guarda só a chave.
- Credenciais via env vars: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_BUCKET_NAME`, `AWS_S3_REGION`. Variável opcional `AWS_S3_ENDPOINT_URL` para apontar a LocalStack em dev sem alterar código.
- Interface `FileStorage` no `domain`; implementação `S3FileStorage` em `infrastructure/storage/` usando `aioboto3`.

### Fila de processamento

- **Celery + Redis** (implementação delegada a outro colega — fora do escopo deste plano).
- Interface `ProcessingQueue` no `domain` criada como `ABC`; implementação concreta em `infrastructure/queue/` ficará pendente até que o colega responsável a entregue.
- Use cases que dependem de `ProcessingQueue` devem recebê-la por injeção e não devem ser alterados quando a implementação chegar.

### Outros

- **Soft delete**: não no MVP. Confirmar com o cliente antes de assumir o contrário.
- **State machine do report**: `QUEUED → PROCESSING → READY | ERROR`. Transições só via use case.
- **Snapshot de config na execução**: imutável depois de criada. Garante histórico consistente quando a config muda.

---

## 3. Ordem de construção

1. `Project` (sem aninhamentos) — base de tudo.
2. `GlobalDictionaryEntry` (independente; dá pra paralelizar).
3. `ColumnConfig` aninhado em projeto, incluindo detecção de colunas.
4. `Report` — create via upload + read + status (sem disparo ainda).
5. Integração com fila: disparo de `ReportExecution`.
6. Download do resultado.
7. Feedback (aprovado/rejeitado).
8. Reprocessamento.
9. Aplicar entrada do dicionário em uma coluna (HU-08 "1 clique").

Cada passo termina rodando `pytest`. Migrações Alembic geradas e aplicadas ao fim do step 3 de cada entidade.

---

## 4. Estrutura de pastas

```text
src/
  domain/
    projects/
      entities.py            # Project, ColumnConfig
      value_objects.py       # NormalizationRules
      exceptions.py
      repositories.py
    reports/
      entities.py            # Report, ReportExecution
      value_objects.py       # ReportStatus, ExecutionStatus, ApprovalStatus
      exceptions.py
      repositories.py
    dictionary/
      entities.py
      exceptions.py
      repositories.py
    shared/
      file_storage.py        # interface FileStorage
      processing_queue.py    # interface ProcessingQueue

  application/
    projects/
      dtos.py
      create_project.py
      get_project.py
      list_projects.py
      update_project.py
      delete_project.py
      configure_columns.py
      update_column_config.py
    reports/
      dtos.py
      upload_report.py
      list_reports.py
      get_report.py
      get_execution_status.py
      download_result.py
      submit_feedback.py
      reprocess_report.py
    dictionary/
      dtos.py
      create_entry.py
      list_entries.py
      get_entry.py
      update_entry.py
      delete_entry.py
      apply_entry_to_column.py

  infrastructure/
    persistence/
      models/
        project.py
        column_config.py
        report.py
        report_execution.py
        dictionary_entry.py
      repositories/
        project_repository.py
        column_config_repository.py
        report_repository.py
        execution_repository.py
        dictionary_repository.py
    storage/
      local_file_storage.py
      s3_file_storage.py
    queue/
      rq_processing_queue.py
    spreadsheet/
      column_detector.py

  presentation/
    http/
      routes/
        projects.py
        column_configs.py
        reports.py
        dictionary.py
      schemas/
        projects.py
        column_configs.py
        reports.py
        dictionary.py
      dependencies/
        projects.py
        reports.py
        dictionary.py

migrations/
tests/
  unit/
    application/
  integration/
```

---

## 5. Procedimento de 5 Steps (aplicar a cada entidade)

Use este procedimento para cada entidade. Conclua cada step antes de passar para o próximo. As **especificações concretas de cada entidade** estão na seção 6.

### Step 1 · Domínio

Crie em `src/domain/<modulo>/`:

**`entities.py`**
- `@dataclass` com `id: UUID`, `user_id: UUID` (quando aplicável), campos de negócio, `created_at: datetime`, `updated_at: datetime`.
- Sem imports externos (apenas `dataclasses`, `uuid`, `datetime`, `enum`).

**`exceptions.py`**
- Exceções específicas: `<Entidade>NotFound`, `<Entidade>NameAlreadyExists`, etc.
- Herda de `Exception` (ou `ValueError` quando for validação semântica).

**`repositories.py`**
- `ABC` com métodos `async`:
  - `create(entity) -> Entity`
  - `get_by_id(id, user_id) -> Entity | None`
  - `list_by_user(user_id, offset, limit) -> tuple[list[Entity], int]`
  - `update(entity) -> Entity`
  - `delete(id, user_id) -> None`
- Sempre `user_id` em `get_by_id` e `delete` para isolamento.

**Checkpoint**: liste os arquivos criados e siga para o Step 2.

### Step 2 · Aplicação

Crie em `src/application/<modulo>/`:

**`dtos.py`**
- `@dataclass` para: `Create<Entidade>Input`, `Update<Entidade>Input`, `<Entidade>Output`, `List<Entidade>Input` (com `page`, `page_size`), `PaginatedOutput`.

**`create_<modulo>.py`** — `Create<Entidade>UseCase`
- Valida regras de negócio (nome vazio, duplicado, etc.).
- Cria entidade com `uuid4()` e timestamps atuais.
- Persiste via interface do repositório.
- Retorna DTO de saída.

**`get_<modulo>.py`** — `Get<Entidade>UseCase`
- Busca por `id + user_id`.
- Lança `<Entidade>NotFound` se não encontrado.

**`list_<modulo>.py`** — `List<Entidade>UseCase`
- Cap de `page_size` em 100.
- `offset = (page - 1) * page_size`.
- Retorna `PaginatedOutput` com `total_pages = ceil(total / page_size)`.

**`update_<modulo>.py`** — `Update<Entidade>UseCase`
- Busca entidade (lança `NotFound` se não existe).
- Aplica apenas campos fornecidos (partial update).
- Atualiza `updated_at` na entidade.
- Persiste e retorna DTO atualizado.

**`delete_<modulo>.py`** — `Delete<Entidade>UseCase`
- Verifica existência (`NotFound` se não existe).
- Deleta via repositório.

**Checkpoint**: liste os arquivos criados e siga para o Step 3.

### Step 3 · Infraestrutura

**`src/infrastructure/persistence/models/<modulo>.py`** — Modelo SQLAlchemy
- Herda de `Base` e `TimestampMixin`.
- FK para `users.id` com `ondelete="CASCADE"` quando aplicável.
- Tipos: `String(N)` para texto curto, `Text` para livre, `JSONB` para variável, `UUID` nativo do Postgres.
- `Index` em FK mais consultada e em `created_at`.
- `UniqueConstraint` onde aplicável.
- Método privado `_to_entity()` mapeando modelo → entidade.

**`src/infrastructure/persistence/repositories/<modulo>_repository.py`** — Repositório concreto
- Implementa a interface do domínio usando `AsyncSession`.
- `list_by_user` usa `func.count().over()` para retornar total na mesma query.
- Mapeia entidade → modelo no `create`/`update`, modelo → entidade no retorno.

**Migração Alembic**
- Gerar com `alembic revision --autogenerate -m "add_<modulo>_table"`.
- Revisar o arquivo gerado: confirmar `upgrade()` e `downgrade()`.
- Não aplicar automaticamente — apenas mostrar o caminho do arquivo.

**Checkpoint**: liste os arquivos criados e siga para o Step 4.

### Step 4 · Apresentação

**`src/presentation/http/schemas/<modulo>.py`** — Schemas Pydantic
- `Create<Entidade>Request`: campos obrigatórios com `Field(..., strip_whitespace=True)` nos textos.
- `Update<Entidade>Request`: todos os campos opcionais (`| None = None`).
- `<Entidade>Response`: campos de saída com `model_config = ConfigDict(from_attributes=True)`.
- `Paginated<Entidade>Response`: `items`, `total`, `page`, `page_size`, `total_pages`.

**`src/presentation/http/dependencies/<modulo>.py`** — Injeção
- Uma factory por caso de uso. Recebe `AsyncSession = Depends(get_db)` e monta repositório + use case.

**`src/presentation/http/routes/<modulo>.py`** — Rotas FastAPI
- `POST /<recurso>` → 201
- `GET /<recurso>` com `page` e `page_size` (ge=1, le=100) → 200
- `GET /<recurso>/{id}` → 200 | 404
- `PATCH /<recurso>/{id}` → 200 | 404
- `DELETE /<recurso>/{id}` → 204 | 404
- Todas com `Depends(get_current_user)`.
- Mapear exceções para HTTP: `NotFound → 404`, `AlreadyExists → 409`, `ValueError → 422`.

Registrar o router em `src/presentation/http/app.py`.

**Checkpoint**: liste os arquivos criados e siga para o Step 5.

### Step 5 · Testes

**`tests/unit/application/test_<modulo>.py`**
- `InMemory<Entidade>Repository` definido no próprio arquivo, implementando a interface com `dict`.
- Cobertura: create OK, create duplicado, get OK, get inexistente, list paginada, update OK, update inexistente, delete OK, delete inexistente.

**`tests/integration/test_<modulo>_api.py`**
- Fixture `AsyncClient` (httpx) + Postgres real (testcontainers ou banco de teste).
- Fluxo: autenticar → criar → listar → buscar → atualizar → deletar.
- Isolamento: criar com usuário A, confirmar que B não vê.

---

## 6. Especificação por entidade

### 6.1 Project

**Campos**: `id`, `user_id`, `name (str ≤120)`, `description (text)`, `ai_context (text)`, `created_at`, `updated_at`.

**Exceções**: `ProjectNotFound`, `ProjectNameAlreadyExists`.

**Constraint extra**: `UNIQUE (user_id, name)`.

**Endpoints** (CRUD padrão do template, prefixo `/projects`).

**Sem desvios**: segue os 5 steps direto.

### 6.2 ColumnConfig

**Campos**: `id`, `project_id`, `column_name (str ≤200)`, `enabled (bool)`, `normalizations (JSONB)`, `classify (bool)`, `categories (JSONB nullable)`, `sample_values (JSONB)`.

**Exceções**: `ColumnConfigNotFound`, `ProjectNotFound` (verificação de ownership).

**Constraint extra**: `UNIQUE (project_id, column_name)`.

**Desvios do template**:
- Não tem `POST` individual. Em vez disso:
  - `POST /projects/{id}/columns/detect` — upload temporário de planilha de referência, retorna colunas detectadas com amostras (não persiste).
  - `PUT /projects/{id}/columns` — substitui o conjunto inteiro de configs do projeto (idempotente).
  - `PATCH /projects/{id}/columns/{column_id}` — edição pontual.
- Não tem `DELETE` individual (deleta junto com o projeto via cascade).
- O use case `ConfigureColumnsUseCase` substitui o `Create<Entidade>UseCase` padrão.

### 6.3 Report

**Campos**: `id`, `project_id`, `original_filename (str ≤255)`, `original_file_key (str ≤512)`, `uploaded_at`, `approval_status (enum)`, `approval_reason (text nullable)`.

**Exceções**: `ReportNotFound`, `ColumnsMismatch` (no upload), `InvalidApprovalTransition`.

**Desvios do template**:
- `POST /projects/{id}/reports` é **multipart upload**, não JSON. Use case dedicado `UploadReportUseCase` (veja seção 7).
- `Update<Entidade>UseCase` padrão **não existe**. Em seu lugar, `SubmitFeedbackUseCase` exposto como `PATCH /reports/{id}/feedback`.
- Sem `DELETE` no MVP.
- Endpoint extra: `POST /reports/{id}/reprocess` (veja seção 7).

### 6.4 ReportExecution

**Campos**: `id`, `report_id`, `status (enum)`, `progress_percent (int)`, `current_step (str nullable)`, `started_at`, `finished_at`, `result_file_key (str nullable)`, `error_log (text nullable)`, `column_config_snapshot (JSONB)`, `created_at`.

**Não é CRUD**: criada apenas por `UploadReportUseCase` e `ReprocessReportUseCase`. Atualizada apenas pelo worker.

**Endpoints**:
- `GET /reports/{id}/executions/{exec_id}/status` — polling de progresso.
- `GET /reports/{id}/executions/{exec_id}/download?format=csv|xlsx`.

Pule os steps 2 (use cases de CRUD padrão), 4 (rotas de CRUD padrão) e 5 (testes de CRUD padrão) da forma padrão; faça apenas o repositório no step 3 e os 2 endpoints no step 4.

### 6.5 DictionaryEntry

**Campos**: `id`, `user_id`, `project_id (UUID nullable)`, `kind (enum: NORMALIZATION_PRESET | CATEGORY_LIST | CLASSIFICATION_INSTRUCTION)`, `name (str ≤120)`, `payload (JSONB)`, `created_at`, `updated_at`.

- `project_id = NULL` → entrada do dicionário **global** do usuário.
- `project_id = <uuid>` → entrada do dicionário **do projeto**. Em conflito de `(kind, name)`, a entrada do projeto tem precedência sobre a global.

**Exceções**: `DictionaryEntryNotFound`, `DictionaryEntryNameAlreadyExists`.

**Constraints**:
- `UNIQUE (user_id, kind, name) WHERE project_id IS NULL` — sem duplicatas no dicionário global.
- `UNIQUE (project_id, kind, name)` — sem duplicatas no dicionário do projeto.

**Repositório** (desvio do template padrão — três formas de listar):
- `list_global(user_id, kind, offset, limit)` → entradas globais do usuário.
- `list_by_project(project_id, user_id, kind, offset, limit)` → entradas do projeto.
- `list_merged(user_id, project_id, kind)` → sem paginação; retorna as duas camadas com o projeto sobrescrevendo o global por `(kind, name)`. Usado pelo pipeline de processamento.

**Endpoints**:
- CRUD padrão do template em `/dictionary` (escopo global) e em `/projects/{project_id}/dictionary` (escopo de projeto).
- `POST /projects/{project_id}/columns/{column_id}/apply-entry/{entry_id}` — `ApplyEntryToColumnUseCase` (veja seção 7).

---

## 7. Fluxos não-CRUD

### Upload de relatório (HU-04)

```
1. Valida tamanho do arquivo (limite em env, ex.: 200 MB).
2. Lê o header do CSV/XLSX em streaming.
3. Compara colunas com a config do projeto:
   - Faltando -> 409 com lista de diferenças.
   - Extras -> 200 com aviso, frontend decide processar ou ajustar.
4. Salva arquivo bruto no storage (key = project_id/report_id/original.ext).
5. Cria Report.
6. Cria ReportExecution com status=QUEUED e snapshot da config atual.
7. Publica job na fila com execution_id.
8. Retorna report_id + execution_id imediatamente.
```

### Detecção de colunas (HU-03)

```
1. Aceita upload temporário (não persiste arquivo).
2. Lê 100 primeiras linhas em streaming.
3. Para cada coluna: nome + até 5 amostras distintas não-nulas.
4. Retorna estrutura. Frontend usa para montar tela de configuração.
5. Persistência só ocorre no PUT /projects/{id}/columns.
```

### Download (HU-06)

```
1. Verifica execution.status == READY.
2. Se formato pedido == formato salvo, presigned URL ou stream direto.
3. Se diferente, converte on-the-fly (CSV<->XLSX) com streaming.
4. Errors parciais: marca linhas problemáticas em coluna `_error`.
```

### Reprocessamento (HU-06)

```
1. Lê report existente.
2. Cria nova ReportExecution com snapshot da config atual.
3. Reusa original_file_key (não re-upa).
4. Publica job na fila.
5. Execuções antigas seguem acessíveis.
```

### Aplicar entrada do dicionário em coluna (HU-08)

```
1. Carrega DictionaryEntry pelo id (verifica ownership via user_id).
2. Carrega ColumnConfig alvo (verifica que pertence ao mesmo projeto).
3. Faz merge do payload conforme kind:
   - NORMALIZATION_PRESET -> sobrescreve normalizations.
   - CATEGORY_LIST -> sobrescreve categories e seta classify=true.
   - CLASSIFICATION_INSTRUCTION -> guarda em metadata.
4. Persiste ColumnConfig.
```

> A entrada pode vir do dicionário global ou do projeto — o use case não distingue, pois já recebe o `entry_id` resolvido.

---

## 8. Schema PostgreSQL (referência para Alembic)

```sql
CREATE TABLE projects (
    id          UUID PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(120) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    ai_context  TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, name)
);
CREATE INDEX idx_projects_user ON projects (user_id);
CREATE INDEX idx_projects_created_at ON projects (created_at);

CREATE TABLE column_configs (
    id              UUID PRIMARY KEY,
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    column_name     VARCHAR(200) NOT NULL,
    enabled         BOOLEAN NOT NULL DEFAULT true,
    normalizations  JSONB NOT NULL DEFAULT '{}'::jsonb,
    classify        BOOLEAN NOT NULL DEFAULT false,
    categories      JSONB,
    sample_values   JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (project_id, column_name)
);
CREATE INDEX idx_column_configs_project ON column_configs (project_id);

CREATE TABLE reports (
    id                  UUID PRIMARY KEY,
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    original_filename   VARCHAR(255) NOT NULL,
    original_file_key   VARCHAR(512) NOT NULL,
    uploaded_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    approval_status     VARCHAR(16) NOT NULL DEFAULT 'PENDING'
                        CHECK (approval_status IN ('PENDING','APPROVED','REJECTED')),
    approval_reason     TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_reports_project ON reports (project_id);
CREATE INDEX idx_reports_uploaded_at ON reports (uploaded_at);

CREATE TABLE report_executions (
    id                       UUID PRIMARY KEY,
    report_id                UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    status                   VARCHAR(16) NOT NULL
                             CHECK (status IN ('QUEUED','PROCESSING','READY','ERROR')),
    progress_percent         INT NOT NULL DEFAULT 0,
    current_step             VARCHAR(32),
    started_at               TIMESTAMPTZ,
    finished_at              TIMESTAMPTZ,
    result_file_key          VARCHAR(512),
    error_log                TEXT,
    column_config_snapshot   JSONB NOT NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_executions_report ON report_executions (report_id);
CREATE INDEX idx_executions_status_partial ON report_executions (status)
    WHERE status IN ('QUEUED','PROCESSING');

CREATE TABLE dictionary_entries (
    id          UUID PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id  UUID REFERENCES projects(id) ON DELETE CASCADE,  -- NULL = global
    kind        VARCHAR(32) NOT NULL
                CHECK (kind IN ('NORMALIZATION_PRESET','CATEGORY_LIST','CLASSIFICATION_INSTRUCTION')),
    name        VARCHAR(120) NOT NULL,
    payload     JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- sem duplicatas no dicionário global
CREATE UNIQUE INDEX uq_dictionary_global ON dictionary_entries (user_id, kind, name)
    WHERE project_id IS NULL;
-- sem duplicatas no dicionário de projeto
CREATE UNIQUE INDEX uq_dictionary_project ON dictionary_entries (project_id, kind, name)
    WHERE project_id IS NOT NULL;
CREATE INDEX idx_dictionary_user ON dictionary_entries (user_id);
CREATE INDEX idx_dictionary_project ON dictionary_entries (project_id)
    WHERE project_id IS NOT NULL;
```

---

## 9. Riscos e armadilhas

- **Upload grande bloqueando o event loop**: usar `aiofiles` + streaming. Nunca `await file.read()` inteiro em memória (120k linhas em XLSX = 50–150 MB).
- **Schema mismatch no upload**: o critério "ajustar a configuração" (HU-04) implica permitir voltar pra config a partir do erro. Não tratar como erro terminal.
- **Snapshot da config na execution**: sem isso, alterar config quebra histórico de execuções antigas.
- **Storage local vs S3**: criar `FileStorage` no domain; não acoplar `boto3` nos use cases.
- **Job órfão**: worker cai e execution fica `PROCESSING` para sempre. Timeout no RQ + cronjob que marca como `ERROR` após X horas.
- **Tamanho de JSONB**: `sample_values` limitado a 5 valores; cortar strings longas.
- **Cascade silenciosa**: deletar projeto cascateia reports no banco, mas não apaga arquivos no S3. Limpeza de storage no use case de delete.
- **`Protocol` vs `ABC`**: o módulo de auth usou `Protocol`; aqui é `ABC` para alinhar com o template. Não misturar dentro de uma mesma entidade.

---

## 10. Comandos de referência

```bash
# Gerar migração depois de criar/alterar modelos
alembic revision --autogenerate -m "add_<modulo>_table"

# Aplicar migrações
alembic upgrade head

# Rodar testes do módulo
pytest tests/unit/application/test_<modulo>.py -v
pytest tests/integration/test_<modulo>_api.py -v
```

---

## 11. Resumo de finalização por entidade

Ao terminar os 5 steps de uma entidade, apresentar:

1. Arquivos criados, agrupados por camada.
2. Comando para gerar e aplicar a migração.
3. Comando para rodar os testes do módulo.
4. Qualquer decisão que tenha desviado deste documento, com justificativa.

---

## 12. Decisões tomadas

| Decisão | Escolha | Responsável |
|---|---|---|
| Storage de arquivos | AWS S3 (`aioboto3`). `AWS_S3_ENDPOINT_URL` opcional para LocalStack em dev. | Felipe |
| Storage de progresso das execuções | Redis (pendente) | Outro colega |
| Fila de processamento | Celery + Redis (pendente) | Outro colega |

Começar pela seção 6.1 (`Project`) seguindo os 5 steps da seção 5.
