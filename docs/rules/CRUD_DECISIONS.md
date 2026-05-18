# CRUD Decisions

Registro das decisões técnicas tomadas durante a implementação do CRUD.

| Data | Decisão | Escolha | Motivo | Responsável |
|---|---|---|---|---|
| 2026-05-11 | Storage de arquivos | AWS S3 via `aioboto3`. `AWS_S3_ENDPOINT_URL` opcional para LocalStack em dev | Ambiente de prod já usa AWS; evita reescrita na hora do deploy | Felipe |
| 2026-05-11 | Storage de progresso das execuções | Redis (pendente) | Performance em writes frequentes de progresso | Outro colega |
| 2026-05-11 | Fila de processamento | Celery + Redis (pendente) | Mais robusto que RQ para escala futura; retry automático | Outro colega |
