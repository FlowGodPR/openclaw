"""
MemOS-Quinn Integration Layer
=============================

Integrates MemTensor/MemOS memory operating system with Quinn's autonomous agent architecture.

Features:
- Persistent skill memory for cross-task reuse
- Evolution engine for skill improvement
- Connection to Quinn's existing memory hierarchy
- Hybrid search (FTS5 + vector) for memory retrieval

Location: /Volumes/QUINN/context/memos_integration/
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# Add memos to path
MEMOS_PATH = Path("/Users/ghost_mini/.openclaw/workspace/memos")
sys.path.insert(0, str(MEMOS_PATH))

from memos.configs.mem_os import MOSConfig
from memos.configs.llm import LLMConfigFactory
from memos.configs.embedder import EmbedderConfigFactory
from memos.configs.chunker import ChunkerConfigFactory
from memos.configs.memory import MemoryConfigFactory
from memos.mem_os.core import MOSCore
from memos.mem_cube.general import GeneralMemCube
from memos.memories.textual.item import TextualMemoryItem, TextualMemoryMetadata


class QuinnMemOSIntegration:
    """
    Integration layer between MemOS and Quinn's autonomous agent.
    
    Provides:
    - Skill memory storage and retrieval
    - Cross-task memory reuse
    - Evolution engine for skill improvement
    - Connection to Quinn's memory hierarchy
    """
    
    def __init__(self, user_id: str = "quinn", session_id: str = "main"):
        self.user_id = user_id
        self.session_id = session_id
        self.quinn_memory_root = Path("/Volumes/QUINN/memory")
        self.memos_workspace = Path("/Users/ghost_mini/.openclaw/workspace/memos")
        
        # Initialize MemOS core with proper config structure
        self.config = self._create_config()
        self.mos_core = MOSCore(config=self.config)
        
        # Create memory cube for Quinn
        self.cube_id = f"quinn-{user_id}"
        self._setup_cube()
        
        print(f"✓ MemOS initialized for user: {user_id}")
        print(f"✓ Memory cube: {self.cube_id}")
        
    def _create_config(self) -> MOSConfig:
        """Create MemOS configuration for Quinn integration."""
        # Build LLM config factory
        llm_config = LLMConfigFactory(
            backend="ollama",
            config={
                "model_name_or_path": "qwen3.5:cloud",
                "temperature": 0.7,
                "api_base": "http://localhost:11434",
            }
        )
        
        # Build embedder config factory
        embedder_config = EmbedderConfigFactory(
            backend="sentence_transformers",
            config={
                "model_name_or_path": "all-MiniLM-L6-v2",
            }
        )
        
        # Build chunker config factory
        chunker_config = ChunkerConfigFactory(
            backend="recursive",
            config={
                "chunk_size": 512,
                "chunk_overlap": 50,
            }
        )
        
        # Build memory config factory for textual memory
        text_mem_config = MemoryConfigFactory(
            backend="general_text",
            config={
                "extractor_llm": llm_config,
                "vector_db": {
                    "backend": "faiss",
                    "config": {
                        "index_path": str(self.quinn_memory_root / "memos_faiss.index"),
                        "distance_metric": "cosine",
                        "vector_dimension": 384,
                    },
                },
                "embedder": embedder_config,
            }
        )
        
        # Build MOS config
        config = MOSConfig(
            user_id=self.user_id,
            session_id=self.session_id,
            chat_model=llm_config,
            mem_reader={
                "backend": "simple_struct",
                "config": {
                    "llm": llm_config,
                    "embedder": embedder_config,
                    "chunker": chunker_config,
                },
            },
            enable_textual_memory=True,
            enable_preference_memory=True,
            enable_mem_scheduler=False,
        )
        
        return config
    
    def _setup_cube(self) -> None:
        """Create and register memory cube for Quinn."""
        cube_dir = self.quinn_memory_root / "memos_cubes" / self.cube_id
        cube_dir.mkdir(parents=True, exist_ok=True)
        
        # Create cube config
        cube_config = GeneralMemCubeConfig(
            user_id=self.user_id,
            cube_id=self.cube_id,
            text_mem=self.config.mem_reader,  # Reuse reader config structure
            act_mem={"backend": "uninitialized", "config": {}},
            para_mem={"backend": "uninitialized", "config": {}},
            pref_mem={"backend": "uninitialized", "config": {}},
        )
        
        # Create and load cube
        self.cube = GeneralMemCube(config=cube_config)
        
        # Save cube config
        config_path = cube_dir / "config.json"
        cube_config.to_json_file(str(config_path))
        
        # Register cube with MOS core
        self.mos_core.register_mem_cube(
            mem_cube_id=self.cube_id,
            user_id=self.user_id,
            cube_dir=str(cube_dir),
        )
        
        print(f"✓ Created memory cube: {self.cube_id}")
    
    def store_skill_memory(self, task_id: str, skill_data: Dict[str, Any]) -> str:
        """
        Store skill memory from a completed task.
        
        Args:
            task_id: Unique task identifier
            skill_data: Extracted skill data (name, description, procedure, etc.)
        
        Returns:
            Memory ID for the stored skill
        """
        memory_content = json.dumps(skill_data, indent=2)
        
        memory_ids = self.mos_core.add(
            memory_content=memory_content,
            mem_cube_id=self.cube_id,
            user_id=self.user_id,
            session_id=self.session_id,
            task_id=task_id,
        )
        
        mem_id = memory_ids[0] if isinstance(memory_ids, list) else memory_ids
        print(f"✓ Stored skill memory: {skill_data.get('name', 'unnamed')} (ID: {mem_id})")
        return mem_id
    
    def retrieve_skill_memory(self, query: str, task_context: str = "") -> List[Dict[str, Any]]:
        """
        Retrieve relevant skill memories for a task.
        
        Args:
            query: Search query (task description or keywords)
            task_context: Additional context for disambiguation
        
        Returns:
            List of relevant skill memories
        """
        results = self.mos_core.search(
            query=query,
            mem_cube_id=self.cube_id,
            user_id=self.user_id,
            top_k=5,
        )
        
        skills = []
        for result in results.results if hasattr(results, 'results') else []:
            try:
                skill_data = json.loads(result.memory)
                skills.append({
                    "id": result.id,
                    "name": skill_data.get("name", "unknown"),
                    "description": skill_data.get("description", ""),
                    "procedure": skill_data.get("procedure", ""),
                    "confidence": result.score if hasattr(result, 'score') else 1.0,
                })
            except (json.JSONDecodeError, AttributeError):
                continue
        
        print(f"✓ Retrieved {len(skills)} skill memories for: {query}")
        return skills
    
    def evolve_skill(self, task_id: str, existing_skill_id: str, new_experience: Dict[str, Any]) -> str:
        """
        Evolve an existing skill with new experience from a task.
        
        Args:
            task_id: Task that generated new experience
            existing_skill_id: ID of skill to update
            new_experience: New experience/procedure/lessons learned
        
        Returns:
            New version memory ID
        """
        # Retrieve existing skill
        existing = self.mos_core.get(
            memory_id=existing_skill_id,
            mem_cube_id=self.cube_id,
        )
        
        if not existing or not existing.memory:
            raise ValueError(f"Skill memory not found: {existing_skill_id}")
        
        old_skill = json.loads(existing.memory)
        
        # Merge new experience
        evolved_skill = {
            **old_skill,
            "update": True,
            "old_memory_id": existing_skill_id,
            "experience": old_skill.get("experience", []) + new_experience.get("experience", []),
            "procedure": new_experience.get("procedure", old_skill.get("procedure")),
            "content_of_current_message": new_experience.get("summary", ""),
        }
        
        # Store evolved version
        new_id = self.store_skill_memory(task_id, evolved_skill)
        print(f"✓ Evolved skill: {old_skill.get('name')} → v{old_skill.get('version', 1) + 1}")
        
        return new_id
    
    def test_integration(self) -> Dict[str, bool]:
        """
        Run integration tests to verify MemOS-Quinn connection.
        
        Returns:
            Test results dictionary
        """
        results = {}
        
        # Test 1: Store skill memory
        test_skill = {
            "name": "Test Skill - Code Review",
            "description": "Review code for quality and best practices",
            "procedure": "1. Read code\n2. Check style\n3. Identify issues\n4. Suggest improvements",
            "experience": ["Always check error handling", "Look for edge cases"],
            "tags": ["code", "review", "quality"],
        }
        
        try:
            mem_id = self.store_skill_memory("test-task-001", test_skill)
            results["store_skill"] = bool(mem_id)
        except Exception as e:
            print(f"✗ Store test failed: {e}")
            results["store_skill"] = False
        
        # Test 2: Retrieve skill memory
        try:
            retrieved = self.retrieve_skill_memory("code review")
            results["retrieve_skill"] = len(retrieved) > 0
        except Exception as e:
            print(f"✗ Retrieve test failed: {e}")
            results["retrieve_skill"] = False
        
        # Test 3: Evolve skill
        if results["store_skill"] and results["retrieve_skill"]:
            try:
                evolved_id = self.evolve_skill(
                    "test-task-002",
                    mem_id,
                    {"experience": ["New lesson: check performance"], "summary": "Added performance check"},
                )
                results["evolve_skill"] = bool(evolved_id)
            except Exception as e:
                print(f"✗ Evolve test failed: {e}")
                results["evolve_skill"] = False
        else:
            results["evolve_skill"] = False
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get MemOS integration status."""
        return {
            "user_id": self.user_id,
            "cube_id": self.cube_id,
            "memory_root": str(self.quinn_memory_root),
            "memos_path": str(self.memos_workspace),
            "mos_initialized": self.mos_core is not None,
            "scheduler_enabled": self.mos_core.mem_scheduler_on() if self.mos_core else False,
        }


def main():
    """Test MemOS-Quinn integration."""
    print("=" * 60)
    print("MemOS-Quinn Integration Test")
    print("=" * 60)
    
    # Initialize integration
    integration = QuinnMemOSIntegration()
    
    # Run tests
    print("\nRunning integration tests...")
    results = integration.test_integration()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    for test, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test}: {status}")
    
    all_passed = all(results.values())
    print("=" * 60)
    print(f"Overall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
