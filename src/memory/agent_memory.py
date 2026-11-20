import json
from typing import Any, Dict, List

from src.orchestration.types import Task


class AgentMemory:
    def __init__(self):
        self.working_memory: List[Dict[str, Any]] = []
        self.episodes = None
        self.codebase = None
        try:
            import chromadb
            client = chromadb.Client()
            self.episodes = client.get_or_create_collection("episodes")
            self.codebase = client.get_or_create_collection("codebase")
        except (ImportError, RuntimeError):
            pass

    def store_episode(self, request: str, plan: List[Task], results: Dict[str, Any]) -> None:
        episode = {"request": request, "plan": [{"type": task.type.value, "target": task.target} for task in plan], "results": results}
        self.working_memory.append(episode)
        if self.episodes:
            self.episodes.add(documents=[json.dumps(episode)], metadatas=[{"request": request}], ids=[f"episode_{len(self.working_memory)}"])

    def recall_similar_episodes(self, request: str, limit: int = 3) -> List[Dict[str, Any]]:
        if self.episodes:
            return [json.loads(document) for document in self.episodes.query(query_texts=[request], n_results=limit)["documents"][0]]
        return self.working_memory[-limit:]

    def search_codebase(self, query: str, limit: int = 5) -> Dict[str, Any]:
        return self.codebase.query(query_texts=[query], n_results=limit) if self.codebase else {"documents": []}
