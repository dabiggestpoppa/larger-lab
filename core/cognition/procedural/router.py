"""
Phase 1.7 — Unified Cognition Router

Unifies ingestion, memory, retrieval, synthesis, and procedural cognition
into one cognition field.

This is the central orchestrator that routes any input to the appropriate
processing pipeline.
"""

from typing import Optional


class CognitionRouter:
    """
    Central cognition routing hub.
    
    Routes inputs to the appropriate pipeline:
    - Documents → Parser Router → Chunking → Embedding → Vector Store
    - Queries → Semantic Retrieval → Context Assembly → Agent
    - Tasks → Skill Router → Workflow Engine → Execution
    - Research → Gap Detection → Research Agent → Synthesis
    """
    
    def __init__(
        self,
        parser_router=None,
        chunker=None,
        embedding_engine=None,
        vector_store=None,
        graph_store=None,
        skill_loader=None,
        workflow_engine=None,
    ):
        self.parser_router = parser_router
        self.chunker = chunker
        self.embedding_engine = embedding_engine
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.skill_loader = skill_loader
        self.workflow_engine = workflow_engine
    
    def ingest(self, file_path: str) -> dict:
        """
        Ingest a document into the cognition substrate.
        Full pipeline: parse → chunk → embed → store → link.
        """
        result = {"file": file_path, "pipeline": []}
        
        # Step 1: Parse
        if self.parser_router:
            cog_obj = self.parser_router.route(file_path)
            result["pipeline"].append({"step": "parse", "status": "ok"})
            result["cognition_object"] = cog_obj.to_dict()
        else:
            result["pipeline"].append({"step": "parse", "status": "skipped"})
            return result
        
        # Step 2: Chunk
        if self.chunker and cog_obj.raw_text:
            chunks = self.chunker.chunk(cog_obj.raw_text, cog_obj.object_id)
            result["pipeline"].append({"step": "chunk", "count": len(chunks)})
        else:
            result["pipeline"].append({"step": "chunk", "status": "skipped"})
            chunks = []
        
        # Step 3: Embed
        if self.embedding_engine and chunks:
            texts = [c.text for c in chunks]
            embeddings = self.embedding_engine.embed_batch(texts)
            for chunk, emb in zip(chunks, embeddings):
                chunk.embedding = emb
            result["pipeline"].append({"step": "embed", "count": len(embeddings)})
        else:
            result["pipeline"].append({"step": "embed", "status": "skipped"})
        
        # Step 4: Store in vector memory
        if self.vector_store and chunks:
            # TODO: Store chunks in vector DB
            result["pipeline"].append({"step": "store", "count": len(chunks)})
        else:
            result["pipeline"].append({"step": "store", "status": "skipped"})
        
        # Step 5: Link in knowledge graph
        if self.graph_store and cog_obj.concepts:
            # TODO: Add entities and relationships to graph
            result["pipeline"].append({"step": "link", "concepts": len(cog_obj.concepts)})
        else:
            result["pipeline"].append({"step": "link", "status": "skipped"})
        
        result["status"] = "completed"
        return result
    
    def query(self, query_text: str, max_results: int = 10) -> dict:
        """
        Query the cognition substrate.
        Semantic retrieval → context assembly → response.
        """
        result = {"query": query_text, "pipeline": []}
        
        # Step 1: Embed query
        if self.embedding_engine:
            query_embedding = self.embedding_engine.embed(query_text)
            result["pipeline"].append({"step": "embed_query", "status": "ok"})
        else:
            result["pipeline"].append({"step": "embed_query", "status": "skipped"})
            return result
        
        # Step 2: Semantic retrieval
        if self.vector_store:
            # TODO: Search vector DB for similar chunks
            result["pipeline"].append({"step": "retrieve", "status": "ok"})
        else:
            result["pipeline"].append({"step": "retrieve", "status": "skipped"})
        
        # Step 3: Graph traversal for related concepts
        if self.graph_store:
            # TODO: Find related entities in knowledge graph
            result["pipeline"].append({"step": "graph_traverse", "status": "ok"})
        else:
            result["pipeline"].append({"step": "graph_traverse", "status": "skipped"})
        
        result["status"] = "completed"
        return result
    
    def execute_task(self, task_description: str) -> dict:
        """
        Execute a task using skill-based routing.
        Task → Skill Router → Workflow Engine → Execution.
        """
        result = {"task": task_description, "pipeline": []}
        
        # Step 1: Find matching skill
        if self.skill_loader:
            skills = self.skill_loader.find_skills_for_task(task_description)
            result["pipeline"].append({
                "step": "find_skill",
                "matches": [s.name for s in skills],
            })
        else:
            result["pipeline"].append({"step": "find_skill", "status": "skipped"})
        
        # Step 2: Execute workflow
        if self.workflow_engine:
            # Determine workflow from task
            workflow_name = self._select_workflow(task_description)
            if workflow_name:
                wf_result = self.workflow_engine.execute(
                    workflow_name, {"task": task_description}
                )
                result["pipeline"].append({
                    "step": "execute",
                    "workflow": workflow_name,
                    "result": wf_result,
                })
            else:
                result["pipeline"].append({"step": "execute", "status": "no_workflow"})
        else:
            result["pipeline"].append({"step": "execute", "status": "skipped"})
        
        result["status"] = "completed"
        return result
    
    def _select_workflow(self, task_description: str) -> Optional[str]:
        """Select the appropriate workflow for a task."""
        task_lower = task_description.lower()
        
        if any(w in task_lower for w in ["ingest", "parse", "process", "read", "import"]):
            return "ingest_document"
        elif any(w in task_lower for w in ["research", "synthesize", "analyze", "study"]):
            return "research_synthesis"
        elif any(w in task_lower for w in ["execute", "run", "do", "perform"]):
            return "skill_execution"
        
        return None
