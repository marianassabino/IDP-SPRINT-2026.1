from datetime import datetime, timezone
from uuid import UUID, uuid4

from domain.projects.repositories import ColumnConfigRepository
from domain.reports.entities import ExecutionStatus, ReportExecution
from domain.reports.exceptions import ReportNotFound
from domain.reports.repositories import ExecutionRepository, ReportRepository
from domain.shared.processing_queue import ProcessingQueue

from application.reports.dtos import ExecutionOutput


class ReprocessReportUseCase:
    def __init__(
        self,
        report_repo: ReportRepository,
        execution_repo: ExecutionRepository,
        column_config_repo: ColumnConfigRepository,
        queue: ProcessingQueue,
    ) -> None:
        self._report_repo = report_repo
        self._execution_repo = execution_repo
        self._column_config_repo = column_config_repo
        self._queue = queue

    async def execute(self, report_id: UUID, project_id: UUID) -> ExecutionOutput:
        report = await self._report_repo.get_by_id(report_id, project_id)
        if report is None:
            raise ReportNotFound(f"Report {report_id} not found.")

        configs = await self._column_config_repo.list_by_project(project_id)
        snapshot = {
            c.column_name: {
                "enabled": c.enabled,
                "normalizations": c.normalizations,
                "classify": c.classify,
                "categories": c.categories,
            }
            for c in configs
        }

        now = datetime.now(timezone.utc)
        execution = ReportExecution(
            id=uuid4(),
            report_id=report.id,
            status=ExecutionStatus.QUEUED,
            progress_percent=0,
            current_step=None,
            started_at=None,
            finished_at=None,
            result_file_key=None,
            error_log=None,
            column_config_snapshot=snapshot,
            created_at=now,
            updated_at=now,
        )
        execution = await self._execution_repo.create(execution)
        await self._queue.enqueue_execution(execution.id)

        return ExecutionOutput(
            id=execution.id,
            report_id=execution.report_id,
            status=execution.status,
            progress_percent=execution.progress_percent,
            current_step=execution.current_step,
            started_at=execution.started_at,
            finished_at=execution.finished_at,
            result_file_key=execution.result_file_key,
            error_log=execution.error_log,
            created_at=execution.created_at,
            updated_at=execution.updated_at,
        )
