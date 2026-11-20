# Autonomous Software Engineering Agent

Python-based autonomous software engineering agent for analyzing source code, generating fixes, creating tests, and coordinating software engineering workflows.

This README documents the project's implementation specifications, supported workflows, interfaces, and operational requirements.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set `OPENAI_API_KEY` for LLM-backed behavior. Local AST analysis, validation, and tests work without an API key.

```powershell
python -m src.cli analyze path\to\file.py
python -m src.cli fix path\to\file.py --description "Add error handling"
python -m src.cli test path\to\file.py
python -m pytest
```

## Project Structure

```text
.
├── Dockerfile
├── README.md
├── requirements.txt
├── src/
│   ├── api.py                         # FastAPI service
│   ├── cli.py                         # Command-line interface
│   ├── agents/
│   │   ├── analyzer.py                # AST, Pylint, and LLM analysis
│   │   ├── fixer.py                   # Fix generation and validation
│   │   └── tester.py                  # Test generation and execution
│   ├── memory/agent_memory.py         # ChromaDB and fallback memory
│   ├── orchestration/
│   │   ├── orchestrator.py            # Main workflow coordinator
│   │   └── types.py                   # Task definitions
│   └── tools/code_tools.py            # Parsing and Docker execution tools
└── tests/test_agent.py                # Unit and smoke tests
```

## Architecture

Requests enter through the CLI, FastAPI, or direct Python usage. `SoftwareEngineeringAgent` parses the request, creates a plan, executes each task, and stores the episode in memory.

```text
User request -> SoftwareEngineeringAgent -> intent parsing -> plan creation
									  -> analyzer/fixer/tester -> memory
```

Fix and refactor requests use an `analyze -> change -> test` plan. Analyze and test requests execute one task. Results from each task are shared with the next task through the task context.

## Implementation Specifications

- **Input:** A natural-language request and a target Python file path.
- **Planning:** Requests are classified as analyze, fix, test, refactor, or review tasks.
- **Analysis:** Python AST inspection and optional Pylint and OpenAI analysis.
- **Fix generation:** Proposed code is generated, syntax-checked, and checked for basic unsafe operations.
- **Testing:** Generated pytest code is executed in a temporary file.
- **Memory:** Completed task episodes can be stored in ChromaDB or temporary in-process memory.
- **Interfaces:** The agent is available through a CLI, Python API, and FastAPI service.
- **Deployment:** A Dockerfile packages the FastAPI service.
- **Safety:** Proposed fixes are displayed as diffs and are not applied automatically.

## Components

### Orchestrator

`src/orchestration/orchestrator.py` owns planning and execution. Supported task types are `analyze`, `fix`, `test`, `refactor`, and `review`.

### Analyzer agent

`src/agents/analyzer.py` reads a Python file and returns AST structure, Pylint messages when available, optional LLM analysis, and normalized static issues.

### Fixer agent

`src/agents/fixer.py` generates proposed replacement code. It validates Python syntax and rejects basic unsafe patterns such as `eval`, `exec`, `__import__`, and `os.system`. The CLI displays a diff; source files are not overwritten automatically.

### Tester agent

`src/agents/tester.py` generates pytest code and runs it in a temporary file. Without an API key it uses a local compilation test as a fallback. The reported coverage value is an estimate.

### Memory and tools

`src/memory/agent_memory.py` uses ChromaDB when installed and otherwise keeps an in-process episode history. `src/tools/code_tools.py` provides parsing, linting, and an optional network-disabled Docker executor.

## Configuration

Set these variables to enable LLM-backed behavior:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
$env:OPENAI_MODEL = "gpt-4o-mini"
```

`OPENAI_MODEL` is optional and defaults to `gpt-4o-mini`. Never commit API keys to the repository.

## Python Usage

```python
from src.orchestration.orchestrator import SoftwareEngineeringAgent

agent = SoftwareEngineeringAgent()
result = agent.process_request(
	"Analyze this file for bugs and security issues",
	"src/agents/fixer.py",
)
print(result["results"][0]["ast_analysis"])
```

## HTTP API

Start the service with:

```powershell
uvicorn src.api:app --reload
```

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Check service health |
| `POST` | `/analyze` | Analyze a file |
| `POST` | `/fix` | Generate and validate a fix |

Example request:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/analyze `
	-ContentType "application/json" `
	-Body '{"file_path":"src/agents/fixer.py"}'
```

## Testing

```powershell
python -m pytest -q
python -m compileall -q src tests
```

The tests cover AST structure detection, syntax-error handling, deterministic division-by-zero fix generation, and an end-to-end analysis request.

## Docker

```powershell
docker build -t autonomous-se-agent .
docker run --rm -p 8000:8000 -e OPENAI_API_KEY=$env:OPENAI_API_KEY autonomous-se-agent
```

The image installs dependencies, copies `src/`, and starts the FastAPI service on port `8000`.

## Safety and Limitations

- The fixer proposes code and does not edit files automatically.
- The safety validator is a small pattern-based check, not a complete sandbox.
- `SafeExecutor` requires a running Docker daemon.
- ChromaDB fallback memory is process-local and is lost when the process exits.
- Fallback tests check compilation and do not provide real behavioral coverage.
- Production deployments should add authentication, authorization, path restrictions, and request validation before exposing the API to untrusted users.

