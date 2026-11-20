from typing import Dict
from fastapi import FastAPI
from pydantic import BaseModel

from src.orchestration.orchestrator import SoftwareEngineeringAgent

app = FastAPI(title="Autonomous SE Agent API")


class AnalyzeRequest(BaseModel):
    file_path: str
    options: Dict = {}


class FixRequest(BaseModel):
    file_path: str
    description: str


@app.post("/analyze")
async def analyze_code(request: AnalyzeRequest):
    return SoftwareEngineeringAgent().process_request(f"Analyze {request.file_path}", request.file_path)


@app.post("/fix")
async def fix_code(request: FixRequest):
    return SoftwareEngineeringAgent().process_request(f"Fix: {request.description}", request.file_path)


@app.get("/health")
async def health():
    return {"status": "healthy"}
