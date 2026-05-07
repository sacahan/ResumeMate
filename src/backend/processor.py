"""Backward-compatible processor export.

Retains the old ResumeMateProcessor name while routing requests through Dify.
"""

from __future__ import annotations

from .dify import DifyProcessor
from .models import Question, SystemResponse


class ResumeMateProcessor:
    """Compatibility wrapper for the legacy processor name and API."""

    def __init__(self):
        self._processor = DifyProcessor()

    async def process_question(self, question: Question) -> SystemResponse:
        """Preserve the legacy API that returned only SystemResponse."""
        response, _ = await self._processor.process_question(question)
        return response


__all__ = ["ResumeMateProcessor"]
