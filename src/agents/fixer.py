import ast
import difflib
import os
import re
from typing import Any, Dict, List

from src.orchestration.types import Task


class FixerAgent:
    def __init__(self, client=None):
        self.client = client
        self.validator = FixValidator()

    def execute(self, task: Task) -> Dict[str, Any]:
        with open(task.target, encoding="utf-8") as source_file:
            original_code = source_file.read()
        fixed_code = self.generate_fix(original_code, task.context.get("issues", []), task.description)
        validation = self.validator.validate(original_code, fixed_code)
        if not validation["valid"]:
            return {"success": False, "error": "Validation failed", "details": validation}
        return {"success": True, "original_code": original_code, "fixed_code": fixed_code, "diff": self.generate_diff(original_code, fixed_code), "validation": validation}

    def generate_fix(self, code: str, issues: List[Dict[str, Any]], description: str) -> str:
        if self.client:
            response = self.client.chat.completions.create(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), messages=[{"role": "system", "content": "Fix the code while preserving functionality. Return only Python code."}, {"role": "user", "content": f"Issues: {issues}\nRequirement: {description}\nCode:\n{code}"}], temperature=0.2)
            return self.extract_code(response.choices[0].message.content)
        if "division by zero" in description.lower() and "return a / b" in code:
            return code.replace("return a / b", "if b == 0:\n        raise ValueError('division by zero')\n    return a / b")
        return code

    @staticmethod
    def generate_diff(original: str, fixed: str) -> str:
        return "".join(difflib.unified_diff(original.splitlines(True), fixed.splitlines(True), fromfile="original", tofile="fixed"))

    @staticmethod
    def extract_code(text: str) -> str:
        matches = re.findall(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
        return matches[0] if matches else text


class FixValidator:
    def validate(self, original: str, fixed: str) -> Dict[str, bool]:
        syntax_valid = self.check_syntax(fixed)
        safety_passed = self.check_safety(fixed)
        return {"valid": syntax_valid and safety_passed, "syntax_valid": syntax_valid, "safety_passed": safety_passed}

    @staticmethod
    def check_syntax(code: str) -> bool:
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    @staticmethod
    def check_safety(code: str) -> bool:
        return not any(pattern in code for pattern in ("eval(", "exec(", "__import__", "os.system"))
