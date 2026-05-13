# TODO (Samuel): descomentar e ajustar após configurar celery_app.py.
#
# Este arquivo define a Celery task que o worker executa ao receber um execution_id da fila.
# A lógica de processamento está em ProcessReportUseCase — não alterar aqui.
#
# from uuid import UUID
# import asyncio
#
# from infrastructure.worker.celery_app import celery_app
#
#
# def _make_process_use_case():
#     """Monta o use case com todas as dependências para rodar dentro do worker."""
#     from infrastructure.persistence.database import AsyncSessionFactory
#     from infrastructure.persistence.repositories.report_repository import SqlAlchemyReportRepository
#     from infrastructure.persistence.repositories.execution_repository import SqlAlchemyExecutionRepository
#     from infrastructure.processor.normalization_processor import NormalizationProcessor
#     from infrastructure.settings import get_settings
#     from infrastructure.storage.s3_file_storage import S3FileStorage
#     from application.reports.process_report import ProcessReportUseCase
#
#     # TODO (Samuel): AsyncSessionFactory precisa ser criada em database.py
#     # Exemplo: AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)
#     session = AsyncSessionFactory()
#     settings = get_settings()
#     return (
#         ProcessReportUseCase(
#             report_repo=SqlAlchemyReportRepository(session),
#             execution_repo=SqlAlchemyExecutionRepository(session),
#             storage=S3FileStorage(settings),
#             processor=NormalizationProcessor(),
#         ),
#         session,
#     )
#
#
# @celery_app.task(name="process_report", bind=True, max_retries=3)
# def process_report_task(self, execution_id: str) -> None:
#     """
#     Recebe execution_id como string (JSON-serializável).
#     Roda o ProcessReportUseCase de forma síncrona via asyncio.run().
#     """
#     async def _run():
#         use_case, session = _make_process_use_case()
#         try:
#             await use_case.execute(UUID(execution_id))
#             await session.commit()
#         except Exception as exc:
#             await session.rollback()
#             raise self.retry(exc=exc, countdown=60) from exc
#         finally:
#             await session.close()
#
#     asyncio.run(_run())
#
#
# # CeleryProcessingQueue — substitui NoopProcessingQueue quando Celery estiver configurado.
# #
# # from uuid import UUID
# # from domain.shared.processing_queue import ProcessingQueue
# #
# # class CeleryProcessingQueue(ProcessingQueue):
# #     async def enqueue_execution(self, execution_id: UUID) -> None:
# #         process_report_task.delay(str(execution_id))
