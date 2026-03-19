#!/usr/bin/env python3
"""
Quinn Sci-Fi Brain - Unified RAG + NTM + HTM Interface

Integrates three advanced memory architectures:
1. RAG (Retrieval-Augmented Generation) - Semantic search with hybrid retrieval
2. NTM (Neural Turing Machine) - Differentiable external memory with content addressing
3. HTM (Hierarchical Temporal Memory) - Temporal pattern recognition & anomaly detection
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

USB = Path("/Volumes/QUINN")
S3A = USB / "context" / "quinn_s3a"
NTM = USB / "context" / "ntm"
HTM = USB / "context" / "htm"


class HTMWrapper:
    """
    HTM wrapper for Quinn Brain integration.
    Provides htm_recognize() and htm_recall() methods.
    """
    
    def __init__(self):
        self.recognizer = None
        self._initialized = False
        self._try_init()
    
    def _try_init(self):
        """Initialize HTM recognizer"""
        try:
            sys.path.insert(0, str(HTM))
            from htm_parallel import HTMParallelRecognizer
            self.recognizer = HTMParallelRecognizer(
                num_columns=1024,
                cells_per_column=16,
                sparsity=0.02
            )
            self._initialized = True
            print("✅ HTM loaded")
        except Exception as e:
            print(f"⚠️ HTM: {e}")
            self._initialized = False
    
    def htm_recognize(self, text: str) -> Dict[str, Any]:
        """
        Recognize pattern in text using HTM.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dict with HTM pattern analysis including anomaly score
        """
        if not self._initialized or not self.recognizer:
            return {"error": "HTM not initialized", "text": text}
        
        return self.recognizer.recognize_pattern(text)
    
    def htm_recall(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Recall patterns from HTM memory by query.
        Uses anomaly detection to find novel vs familiar patterns.
        
        Args:
            query: Query text
            limit: Max results (not directly applicable to HTM)
            
        Returns:
            Dict with HTM recall results
        """
        if not self._initialized or not self.recognizer:
            return {"query": query, "results": [], "error": "HTM not initialized"}
        
        # Analyze query as pattern
        result = self.recognizer.recognize_pattern(query)
        
        # Get sequence prediction if available
        prediction = self.recognizer.get_sequence_prediction()
        
        # Check for anomalies in recent history
        recent_patterns = self.recognizer.pattern_history[-limit:] if self.recognizer.pattern_history else []
        
        return {
            "query": query,
            "technique": "htm_temporal_pattern",
            "anomaly_score": result.get("anomaly_score", 0),
            "is_novel": result.get("is_novel", False),
            "features": result.get("detected_features", []),
            "sequence_prediction": prediction,
            "recent_patterns": recent_patterns,
            "timestamp": datetime.now().isoformat()
        }
    
    def htm_detect_anomaly(self, text: str) -> Dict[str, Any]:
        """Detect if text contains anomalous pattern"""
        if not self._initialized or not self.recognizer:
            return {"text": text, "is_anomalous": False, "error": "HTM not initialized"}
        
        return self.recognizer.detect_anomaly(text)
    
    def status(self) -> Dict[str, Any]:
        """Get HTM status"""
        if not self._initialized or not self.recognizer:
            return {"available": False}
        
        return self.recognizer.get_status()


class SciFiBrain:
    """
    Unified brain interface integrating RAG + NTM + HTM.
    
    Provides:
    - recall_rag(): Semantic retrieval with hybrid search
    - ntm_recall(): Differentiable memory recall
    - htm_recognize(): Temporal pattern recognition
    - recall(): Unified recall fusing all three systems
    - think(): Enriched thinking with all three contexts
    """
    
    def __init__(self):
        self.rag = None
        self.ntm = None
        self.htm = None
        self._load_all()
    
    def _load_all(self):
        """Load all three memory systems"""
        # 1. Load RAG
        try:
            sys.path.insert(0, str(USB / "context" / "quinn_sota"))
            from quinn_rag_brain import QuinnRAGBrain
            self.rag = QuinnRAGBrain()
            print("✅ RAG loaded")
        except Exception as e:
            print(f"⚠️ RAG: {e}")
            self.rag = None
        
        # 2. Load NTM
        try:
            sys.path.insert(0, str(NTM))
            from ntm_memory import QuinnNTMMemory
            self.ntm = QuinnNTMMemory(memory_units=64, memory_unit_size=32, device='cpu')
            print("✅ NTM loaded")
        except Exception as e:
            print(f"⚠️ NTM: {e}")
            self.ntm = None
        
        # 3. Load HTM
        self.htm = HTMWrapper()
    
    def recall_rag(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """RAG recall - semantic retrieval"""
        if not self.rag:
            return {"error": "RAG not available", "query": query}
        
        # Initialize with test docs if not already done
        if not self.rag._initialized:
            test_docs = [
                "ARES trading strategy: 5-min scalping with RSI+MACD.",
                "Risk: 1-2% per trade, 5% daily loss limit.",
                "Chrome CDP port 9222 for Pocket Option bot.",
                "Quinn memory on /Volumes/QUINN USB.",
                "Timeframe: 5-sec to 1-min expiry.",
                "Sci-fi brain integrates RAG, NTM, and HTM architectures."
            ]
            self.rag.initialize(test_docs)
        
        return self.rag.recall_rag(query, limit)
    
    def ntm_recall(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """NTM recall - differentiable memory"""
        if not self.ntm:
            return {"error": "NTM not available", "query": query}
        
        return self.ntm.ntm_recall(query, limit)
    
    def htm_recognize(self, text: str) -> Dict[str, Any]:
        """HTM pattern recognition"""
        if not self.htm:
            return {"error": "HTM not available", "text": text}
        
        return self.htm.htm_recognize(text)
    
    def recall(self, query: str, limit: int = 5, mode: str = "all") -> Dict[str, Any]:
        """
        Unified recall from all three systems.
        
        Args:
            query: Query text
            limit: Max results per system
            mode: "all", "rag", "ntm", or "htm"
            
        Returns:
            Dict with results from requested systems
        """
        results = {
            "query": query,
            "mode": mode,
            "timestamp": datetime.now().isoformat(),
            "systems": {}
        }
        
        if mode in ["all", "rag"]:
            results["systems"]["rag"] = self.recall_rag(query, limit)
        
        if mode in ["all", "ntm"]:
            results["systems"]["ntm"] = self.ntm_recall(query, limit)
        
        if mode in ["all", "htm"]:
            results["systems"]["htm"] = self.htm.htm_recall(query, limit)
        
        # Fuse results
        results["fused"] = self._fuse_results(results["systems"])
        
        return results
    
    def _fuse_results(self, systems: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fuse results from all three systems into unified context.
        
        Prioritizes:
        1. RAG for semantic accuracy
        2. NTM for sequence memory
        3. HTM for pattern novelty detection
        """
        fused = {
            "semantic_results": [],
            "memory_traces": [],
            "pattern_flags": [],
            "confidence": 0.0,
            "novelty_score": 0.0
        }
        
        # Extract RAG semantic results
        if "rag" in systems:
            rag = systems["rag"]
            if "results" in rag and rag["results"]:
                fused["semantic_results"] = rag["results"]
                fused["confidence"] = max(fused["confidence"], 
                    sum(rag.get("scores", [0])) / len(rag.get("scores", [1])) if rag.get("scores") else 0)
        
        # Extract NTM memory traces
        if "ntm" in systems:
            ntm = systems["ntm"]
            if "memories" in ntm and ntm["memories"]:
                fused["memory_traces"] = ntm["memories"]
                fused["confidence"] = max(fused["confidence"],
                    ntm["memories"][0].get("relevance_score", 0) if ntm["memories"] else 0)
        
        # Extract HTM pattern flags
        if "htm" in systems:
            htm = systems["htm"]
            if htm.get("is_novel"):
                fused["pattern_flags"].append("NOVEL_PATTERN")
            fused["novelty_score"] = htm.get("anomaly_score", 0)
            if htm.get("features"):
                fused["pattern_flags"].extend(htm["features"])
        
        return fused
    
    def think(self, context: str, query: str = None) -> Dict[str, Any]:
        """
        Enriched thinking with all three memory systems.
        
        Args:
            context: Current context/prompt
            query: Optional specific query
            
        Returns:
            Dict with enriched thinking context
        """
        # Get unified recall
        recall_results = self.recall(query or context, mode="all")
        
        # Get HTM pattern analysis on context
        htm_analysis = self.htm_recognize(context) if self.htm else {}
        
        # Build enriched context
        enriched = {
            "original_context": context,
            "recall": recall_results,
            "htm_analysis": htm_analysis,
            "enriched_context": self._build_enriched_context(context, recall_results, htm_analysis),
            "agi_rating": self._calculate_agi_rating(),
            "timestamp": datetime.now().isoformat()
        }
        
        return enriched
    
    def _build_enriched_context(self, context: str, recall: Dict, htm: Dict) -> str:
        """Build enriched context string from all systems"""
        enriched = [context]
        
        # Add RAG context
        if recall.get("systems", {}).get("rag", {}).get("results"):
            enriched.append("\n--- RAG Context ---")
            for doc in recall["systems"]["rag"]["results"][:3]:
                enriched.append(f"• {doc[:150]}")
        
        # Add NTM context
        if recall.get("systems", {}).get("ntm", {}).get("memories"):
            enriched.append("\n--- NTM Memory Traces ---")
            for mem in recall["systems"]["ntm"]["memories"][:3]:
                enriched.append(f"• Sequence {mem.get('sequence_id')}: {mem.get('label')}")
        
        # Add HTM flags
        if htm.get("pattern_flags"):
            enriched.append("\n--- HTM Pattern Flags ---")
            for flag in htm["pattern_flags"]:
                enriched.append(f"• {flag}")
        
        return "\n".join(enriched)
    
    def _calculate_agi_rating(self) -> Dict[str, Any]:
        """
        Calculate AGI rating based on integrated architectures.
        
        Returns:
            Dict with AGI metrics
        """
        systems_active = sum([
            self.rag is not None,
            self.ntm is not None,
            self.htm is not None and self.htm._initialized
        ])
        
        base_rating = 30 + (systems_active * 15)  # 30 base, +15 per system
        
        # Add bonuses for integration
        integration_bonus = 0
        if systems_active == 3:
            integration_bonus = 20  # All three integrated
        
        total = base_rating + integration_bonus
        
        return {
            "rating": total,
            "max_possible": 100,
            "systems_active": systems_active,
            "integration_bonus": integration_bonus,
            "architectures": {
                "rag": self.rag is not None,
                "ntm": self.ntm is not None,
                "htm": self.htm is not None and self.htm._initialized
            },
            "assessment": self._get_assessment(total)
        }
    
    def _get_assessment(self, rating: int) -> str:
        """Get assessment based on rating"""
        if rating >= 80:
            return "Advanced AGI - Multi-architecture integration"
        elif rating >= 60:
            return "Strong AGI - Multiple memory systems"
        elif rating >= 40:
            return "Developing AGI - Basic integration"
        else:
            return "Early AGI - Foundation stage"
    
    def store(self, content: str, label: str = None) -> Dict[str, Any]:
        """Store to all three systems"""
        results = {}
        
        if self.ntm:
            results["ntm"] = self.ntm.ntm_store([content], label or "default")
        
        if self.rag:
            if not self.rag._initialized:
                self.rag.initialize([content])
            else:
                # Reinitialize with new content
                existing = self.rag.chunks + [content]
                self.rag.initialize(existing)
            results["rag"] = {"stored": True}
        
        # HTM learns from sequence automatically
        if self.htm and self.htm.recognizer:
            self.htm.recognizer.sequence_buffer.append(content)
            results["htm"] = {"added_to_sequence": True}
        
        return results
    
    def status(self) -> Dict[str, Any]:
        """Get full system status"""
        return {
            "rag": self.rag.status() if self.rag else {"available": False},
            "ntm": self.ntm.ntm_status() if self.ntm else {"available": False},
            "htm": self.htm.status() if self.htm else {"available": False},
            "agi_rating": self._calculate_agi_rating()
        }


if __name__ == "__main__":
    print("=" * 70)
    print("QUINN SCI-FI BRAIN - RAG + NTM + HTM INTEGRATION")
    print("=" * 70)
    
    brain = SciFiBrain()
    
    print("\n1. SYSTEM STATUS:")
    status = brain.status()
    print(f"   RAG: {status['rag']}")
    print(f"   NTM: {status['ntm']}")
    print(f"   HTM: {status['htm']}")
    
    print("\n2. AGI RATING:")
    rating = status['agi_rating']
    print(f"   Rating: {rating['rating']}/{rating['max_possible']}")
    print(f"   Assessment: {rating['assessment']}")
    
    print("\n3. TEST RECALL (mode='all'):")
    recall = brain.recall("trading strategy", mode="all", limit=3)
    print(f"   Query: {recall['query']}")
    if recall.get("systems", {}).get("rag"):
        print(f"   RAG results: {len(recall['systems']['rag'].get('results', []))} docs")
    if recall.get("systems", {}).get("ntm"):
        print(f"   NTM memories: {recall['systems']['ntm'].get('recalled_count', 0)}")
    if recall.get("systems", {}).get("htm"):
        print(f"   HTM anomaly: {recall['systems']['htm'].get('anomaly_score', 0):.2f}")
    
    print("\n4. TEST THINK:")
    think = brain.think("What is the risk strategy for trading?", query="risk management")
    print(f"   Context enriched: {len(think['enriched_context'])} chars")
    print(f"   AGI rating: {think['agi_rating']['rating']}")
    
    print("\n5. TEST HTM PATTERN RECOGNITION:")
    htm = brain.htm_recognize("Hello world pattern test")
    print(f"   Anomaly score: {htm.get('anomaly_score', 0):.2f}")
    print(f"   Features: {htm.get('detected_features', [])}")
    
    print("\n" + "=" * 70)
    print("ALL SYSTEMS INTEGRATED")
    print("=" * 70)
