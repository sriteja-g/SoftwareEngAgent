from src.agents.analyzer import AnalyzerAgent
from src.agents.fixer import FixerAgent
from src.orchestration.orchestrator import SoftwareEngineeringAgent
from src.orchestration.types import Task, TaskType


def test_analyzer_detects_python_structure(tmp_path):
    target = tmp_path / "sample.py"
    target.write_text("class Example:\n    def run(self):\n        return 1\n", encoding="utf-8")
    result = AnalyzerAgent().execute(Task(TaskType.ANALYZE, str(target), "Analyze"))
    assert result["ast_analysis"]["classes"] == ["Example"]
    assert result["ast_analysis"]["functions"] == ["run"]


def test_analyzer_handles_syntax_errors():
    assert "error" in AnalyzerAgent().analyze_ast("def broken(\n")


def test_fixer_validates_division_by_zero_fix():
    fixed = FixerAgent().generate_fix("def divide(a, b):\n    return a / b\n", [], "Fix the division by zero bug")
    assert "if b == 0" in fixed
    assert FixerAgent().validator.check_syntax(fixed)


def test_end_to_end_analyze():
    result = SoftwareEngineeringAgent().process_request("Analyze this file", __file__)
    assert result["results"][0]["ast_analysis"]["functions"]
