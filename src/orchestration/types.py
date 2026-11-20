from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class TaskType(Enum):
    ANALYZE = "analyze"
    FIX = "fix"
    TEST = "test"
    REFACTOR = "refactor"
    REVIEW = "review"


@dataclass
class Task:
    type: TaskType
    target: str
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
