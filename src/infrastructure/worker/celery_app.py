# TODO (Samuel): configurar a integração Celery + Redis aqui.
#
# Passos necessários:
#   1. Adicionar dependências ao pyproject.toml:
#        "celery>=5.3,<6.0"
#        "redis>=5.0,<6.0"
#   2. Adicionar variáveis de ambiente ao .env e ao Settings (settings.py):
#        CELERY_BROKER_URL=redis://localhost:6379/0
#        CELERY_RESULT_BACKEND=redis://localhost:6379/1
#   3. Descomentar e ajustar o bloco abaixo:
#
# from celery import Celery
# from infrastructure.settings import get_settings
#
# def create_celery_app() -> Celery:
#     settings = get_settings()
#     app = Celery(
#         "normalizador",
#         broker=settings.celery_broker_url,
#         backend=settings.celery_result_backend,
#         include=["infrastructure.worker.tasks"],
#     )
#     app.conf.update(
#         task_serializer="json",
#         result_serializer="json",
#         accept_content=["json"],
#         timezone="UTC",
#         enable_utc=True,
#     )
#     return app
#
# celery_app = create_celery_app()
#
#   4. Substituir NoopProcessingQueue por CeleryProcessingQueue em
#      presentation/http/dependencies/reports.py
#
# Para subir o worker localmente (após configurar):
#   celery -A infrastructure.worker.celery_app.celery_app worker --loglevel=info
