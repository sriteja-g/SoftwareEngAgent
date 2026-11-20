import ast
import subprocess
from typing import Any, Dict


class CodeTools:
    @staticmethod
    def parse_python(code: str) -> Dict[str, Any]:
        try:
            tree = ast.parse(code)
            return {"valid": True, "functions": [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)], "classes": [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]}
        except SyntaxError as error:
            return {"valid": False, "error": str(error)}

    @staticmethod
    def run_linter(file_path: str):
        result = subprocess.run(["pylint", file_path, "--output-format=json"], capture_output=True, text=True, check=False)
        return result.stdout


class SafeExecutor:
    def __init__(self):
        import docker
        self.client = docker.from_env()

    def execute(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        try:
            container = self.client.containers.run("python:3.11-slim", command=["python", "-c", code], detach=True, mem_limit="256m", network_disabled=True, remove=True)
            result = container.wait(timeout=timeout)
            return {"success": True, "output": container.logs().decode(), "exit_code": result["StatusCode"]}
        except Exception as error:
            return {"success": False, "error": str(error)}
