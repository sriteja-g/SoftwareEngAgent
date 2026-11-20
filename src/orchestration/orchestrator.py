import json
import os
from typing import Any, Dict, List

from .types import Task, TaskType


class SoftwareEngineeringAgent:
    """Coordinate analysis, fixes, testing, and episode memory."""

    def __init__(self):
        client = None
        if os.getenv("OPENAI_API_KEY"):
            from openai import OpenAI
            client = OpenAI()
        from src.agents.analyzer import AnalyzerAgent
        from src.agents.fixer import FixerAgent
        from src.agents.tester import TesterAgent
        from src.memory.agent_memory import AgentMemory
        self.client = client
        self.analyzer = AnalyzerAgent(client)
        self.fixer = FixerAgent(client)
        self.tester = TesterAgent(client)
        self.memory = AgentMemory()

    def process_request(self, request: str, target_path: str) -> Dict[str, Any]:
        intent = self.parse_intent(request)
        plan = self.create_plan(intent, target_path)
        results = self.execute_plan(plan)
        self.memory.store_episode(request, plan, results)
        return results

    def parse_intent(self, request: str) -> Dict[str, str]:
        if self.client:
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "system", "content": "Return JSON with task_type and requirements. task_type must be analyze, fix, test, refactor, or review."}, {"role": "user", "content": request}],
                temperature=0.2,
            )
            return json.loads(response.choices[0].message.content)
        lowered = request.lower()
        task_type = next((value for value in ("fix", "test", "refactor", "review", "analyze") if value in lowered), "analyze")
        return {"task_type": task_type, "requirements": request}

    def create_plan(self, intent: Dict[str, str], target_path: str) -> List[Task]:
        task_type = TaskType(intent["task_type"])
        if task_type in (TaskType.FIX, TaskType.REFACTOR):
            return [Task(TaskType.ANALYZE, target_path, "Analyze code"), Task(task_type, target_path, intent.get("requirements", "")), Task(TaskType.TEST, target_path, "Validate change")]
        return [Task(task_type, target_path, intent.get("requirements", ""))]

    def execute_plan(self, plan: List[Task]) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        context: Dict[str, Any] = {}
        for task in plan:
            task.context = context
            if task.type == TaskType.ANALYZE:
                result = self.analyzer.execute(task)
            elif task.type in (TaskType.FIX, TaskType.REFACTOR):
                result = self.fixer.execute(task)
            elif task.type == TaskType.TEST:
                result = self.tester.execute(task)
            else:
                result = {"error": f"Unsupported task type: {task.type.value}"}
            results.append(result)
            context.update(result)
        return {"tasks": len(plan), "results": results}
