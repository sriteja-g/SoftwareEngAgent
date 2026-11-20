import ast
import json
import os
import subprocess
from typing import Any, Dict, List

from src.orchestration.types import Task


class AnalyzerAgent:
    def __init__(self, client=None):
        self.client = client

    def execute(self, task: Task) -> Dict[str, Any]:
        with open(task.target, encoding="utf-8") as source_file:
            code = source_file.read()
        static_issues = self.run_static_analysis(task.target)
        return {"file": task.target, "ast_analysis": self.analyze_ast(code), "static_issues": static_issues, "llm_analysis": self.llm_analyze(code), "issues": self.consolidate_issues(static_issues)}

    def analyze_ast(self, code: str) -> Dict[str, Any]:
        try:
            tree = ast.parse(code)
            return {"functions": [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))], "classes": [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)], "lines": len(code.splitlines())}
        except SyntaxError as error:
            return {"error": str(error)}

    def run_static_analysis(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            result = subprocess.run(["pylint", file_path, "--output-format=json"], capture_output=True, text=True, check=False)
            return json.loads(result.stdout or "[]")
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def llm_analyze(self, code: str) -> Dict[str, str]:
        if not self.client:
            return {"analysis": "LLM analysis skipped; OPENAI_API_KEY is not configured."}
        response = self.client.chat.completions.create(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), messages=[{"role": "system", "content": "Review this code for bugs, security issues, and improvements."}, {"role": "user", "content": code}], temperature=0.3)
        return {"analysis": response.choices[0].message.content}

    @staticmethod
    def consolidate_issues(static: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [{"type": issue.get("type", "unknown"), "message": issue.get("message", ""), "line": issue.get("line", 0), "severity": issue.get("severity", "info"), "source": "static"} for issue in static]
