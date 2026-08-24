from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar


class JobStatus(StrEnum):
    PLANNED = "planned"
    SYNTHESIZING = "synthesizing"
    ASSEMBLING = "assembling"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class EpisodeJob:
    """Explicit state for one episode generation attempt."""

    title: str
    slug: str
    chunk_count: int
    status: JobStatus = JobStatus.PLANNED

    _allowed_transitions: ClassVar[dict[JobStatus, set[JobStatus]]] = {
        JobStatus.PLANNED: {JobStatus.SYNTHESIZING, JobStatus.FAILED},
        JobStatus.SYNTHESIZING: {JobStatus.ASSEMBLING, JobStatus.FAILED},
        JobStatus.ASSEMBLING: {JobStatus.COMPLETED, JobStatus.FAILED},
        JobStatus.COMPLETED: set(),
        JobStatus.FAILED: set(),
    }

    def transition_to(self, status: JobStatus) -> None:
        if status not in self._allowed_transitions[self.status]:
            raise ValueError(f"Cannot transition job from {self.status} to {status}")
        self.status = status

    def as_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "slug": self.slug,
            "chunk_count": self.chunk_count,
            "status": self.status.value,
        }
