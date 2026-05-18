# TODO (Samuel): implementar a lógica real de normalização e classificação aqui.
#
# Este arquivo é o ponto de conexão entre o pipeline de processamento e o worker.
# A interface que deve ser implementada está em:
#   application/reports/report_processor.py → ReportProcessor (ABC)
#
# O que este processador deve fazer:
#   1. Receber o arquivo bruto (bytes) + original_filename + column_config_snapshot
#   2. Aplicar normalizações determinísticas conforme `normalizations` de cada coluna
#   3. Aplicar classificação via IA conforme `classify` + `categories` de cada coluna
#   4. Retornar ProcessingResult(content=..., filename=..., content_type=...)
#      onde content é o CSV/XLSX processado pronto para salvar no S3
#
# Estrutura do column_config_snapshot (dict):
#   {
#     "nome_coluna": {
#       "enabled": bool,
#       "normalizations": dict,   # presets de normalização a aplicar
#       "classify": bool,         # se True, rodar classificação IA nesta coluna
#       "categories": list | None # categorias possíveis para classificação
#     },
#     ...
#   }
#
# Quando pronto, substituir a injeção em:
#   presentation/http/dependencies/reports.py → get_process_report_use_case
#   infrastructure/worker/tasks.py → _make_process_use_case

from application.reports.report_processor import ProcessingResult, ReportProcessor


class NormalizationProcessor(ReportProcessor):
    async def process(
        self,
        content: bytes,
        original_filename: str,
        column_config_snapshot: dict,
    ) -> ProcessingResult:
        # TODO (Samuel): substituir este stub pela implementação real.
        # Por ora retorna o arquivo original sem modificações para que o
        # ciclo QUEUED → PROCESSING → READY funcione end-to-end.
        return ProcessingResult(
            content=content,
            filename=original_filename,
            content_type="application/octet-stream",
        )
