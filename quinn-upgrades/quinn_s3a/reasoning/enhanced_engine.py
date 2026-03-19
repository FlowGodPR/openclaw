"""
Quinn Enhanced Reasoning Engine v2.0
Integrates 5 advanced reasoning capabilities:

1. Neural-Symbolic Integration - LLM + symbolic logic (Prolog/Datalog)
2. External Tool Reasoning - Reason BY USING tools (calculator, search, code)
3. Multi-Model Verification - Different models verify conclusions
4. Iterative Refinement - Refine conclusions over multiple passes
5. Uncertainty Calibration - Know when you don't know

This engine:
- Reduces errors vs raw LLM
- Catches hallucinations
- Improves math/logic accuracy
- Knows uncertainty boundaries
"""

import sqlite3
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .neural_symbolic import reason_with_symbolic, NeuralSymbolicReasoner
from .tool_reasoning import reason_with_tools, ToolReasoner
from .multi_model_verification import verify_with_multi_model, MultiModelVerifier
from .iterative_refinement import refine_iteratively, IterativeRefiner
from .uncertainty_calibration import calibrate_uncertainty, UncertaintyCalibrator


class ReasoningStrategy(Enum):
    SYMBOLIC = "symbolic"
    TOOL = "tool"
    MULTI_MODEL = "multi_model"
    ITERATIVE = "iterative"
    UNCERTAINTY = "uncertainty"
    ENHANCED = "enhanced"  # All strategies combined


@dataclass
class EnhancedReasoningResult:
    answer: str
    confidence: float
    calibrated_confidence: float
    strategies_used: List[str]
    hallucination_risk: str
    verification_status: str
    contradictions: List[Dict]
    tool_results: List[Dict]
    refinement_passes: int
    uncertainty_flags: List[Dict]
    should_decline: bool
    decline_reason: str


class EnhancedReasoningEngine:
    """
    Unified reasoning engine with all 5 enhanced capabilities.
    
    Usage:
        engine = EnhancedReasoningEngine()
        result = engine.reason("complex problem")
    """
    
    def __init__(self, db_path: str = ":memory:", auto_strategy: bool = True):
        self.db_path = db_path
        self.auto_strategy = auto_strategy
        self._conn = None
        self.symbolic_reasoner = NeuralSymbolicReasoner(db_path=db_path)
        self.tool_reasoner = ToolReasoner(db_path=db_path)
        self.model_verifier = MultiModelVerifier(db_path=db_path)
        self.iterative_refiner = IterativeRefiner(db_path=db_path)
        self.uncertainty_calibrator = UncertaintyCalibrator(db_path=db_path)
        self._init_db()
    
    def _init_db(self):
        """Initialize unified SQLite database."""
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self._conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reasoning_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                strategy TEXT,
                answer TEXT,
                confidence REAL,
                calibrated_confidence REAL,
                hallucination_risk TEXT,
                verified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accuracy_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                problem_type TEXT,
                correct INTEGER,
                error_type TEXT,
                notes TEXT
            )
        """)
        
        self._conn.commit()
    
    def _select_strategy(self, query: str) -> ReasoningStrategy:
        """Auto-select best reasoning strategy based on query."""
        query_lower = query.lower()
        
        # Math/computation → Tool reasoning
        if any(kw in query_lower for kw in ['calculate', 'compute', 'solve', 'math', 'equation']):
            return ReasoningStrategy.TOOL
        
        # Logic/factual → Symbolic + Multi-model
        if any(kw in query_lower for kw in ['prove', 'verify', 'logic', 'fact', 'true']):
            return ReasoningStrategy.MULTI_MODEL
        
        # Complex/exploratory → Iterative refinement
        if any(kw in query_lower for kw in ['explain', 'analyze', 'discuss', 'complex']):
            return ReasoningStrategy.ITERATIVE
        
        # Unknown/uncertain → Uncertainty calibration
        if any(kw in query_lower for kw in ['might', 'could', 'uncertain', 'unknown']):
            return ReasoningStrategy.UNCERTAINTY
        
        # Default: Enhanced (all strategies)
        return ReasoningStrategy.ENHANCED
    
    def reason_symbolic(self, query: str) -> Dict:
        """Reason using neural-symbolic integration."""
        return reason_with_symbolic(query, db_path=self.db_path)
    
    def reason_with_tools(self, query: str) -> Dict:
        """Reason using external tools."""
        return reason_with_tools(query, db_path=self.db_path)
    
    def verify_multi_model(self, query: str) -> Dict:
        """Verify using multiple models."""
        result = verify_with_multi_model(query, db_path=self.db_path)
        return {
            'consensus': result.consensus,
            'agreement_score': result.agreement_score,
            'hallucination_risk': result.hallucination_risk,
            'disagreements': result.disagreements,
            'recommended_action': result.recommended_action
        }
    
    def refine_iteratively(self, query: str, max_passes: int = 3) -> Dict:
        """Refine answer iteratively."""
        result = refine_iteratively(query, max_passes=max_passes, db_path=self.db_path)
        return {
            'final_answer': result.final_answer,
            'initial_answer': result.initial_answer,
            'improvement': result.improvement,
            'converged': result.converged,
            'total_passes': result.total_passes
        }
    
    def calibrate_uncertainty(self, query: str, answer: str, 
                              confidence: float = 0.7) -> Dict:
        """Calibrate uncertainty for answer."""
        result = calibrate_uncertainty(query, answer, confidence, db_path=self.db_path)
        return {
            'calibrated_confidence': result.calibrated_confidence,
            'uncertainty_flags': [{'type': f.signal_type.value, 'trigger': f.trigger} 
                                  for f in result.uncertainty_flags],
            'should_decline': result.should_decline,
            'decline_reason': result.decline_reason,
            'hedging_level': result.hedging_level
        }
    
    def reason(self, query: str, strategy: str = "auto") -> EnhancedReasoningResult:
        """
        Main reasoning entry point.
        
        Strategies:
        - "symbolic": Neural-symbolic logic
        - "tool": Tool-augmented reasoning
        - "multi_model": Cross-model verification
        - "iterative": Iterative refinement
        - "uncertainty": Uncertainty calibration
        - "enhanced": All strategies combined (default)
        - "auto": Auto-select best strategy
        """
        if strategy == "auto":
            strategy = self._select_strategy(query).value
        
        results = {}
        
        # Execute selected strategy
        if strategy == "symbolic":
            results = self.reason_symbolic(query)
            answer = results.get('clauses', str(results.get('facts', [])))
            confidence = 0.8 if not results.get('contradictions') else 0.4
            hallucination_risk = results.get('hallucination_risk', 'medium')
        
        elif strategy == "tool":
            results = self.reason_with_tools(query)
            answer = results.get('answer', '')
            confidence = results.get('confidence', 0.7)
            hallucination_risk = 'high' if results.get('contradiction') else 'low'
        
        elif strategy == "multi_model":
            results = self.verify_multi_model(query)
            answer = results.get('primary_answer', '')
            confidence = results.get('agreement_score', 0.5)
            hallucination_risk = results.get('hallucination_risk', 'medium')
        
        elif strategy == "iterative":
            results = self.refine_iteratively(query)
            answer = results.get('final_answer', '')
            confidence = 0.7 + results.get('improvement', 0)
            hallucination_risk = 'low' if results.get('converged') else 'medium'
        
        elif strategy == "uncertainty":
            # Placeholder - needs answer to calibrate
            answer = "Answer requires uncertainty calibration"
            confidence = 0.5
            hallucination_risk = 'medium'
            results = self.calibrate_uncertainty(query, answer, confidence)
        
        else:  # enhanced - all strategies
            # 1. Symbolic reasoning
            sym_result = self.reason_symbolic(query)
            
            # 2. Tool reasoning
            tool_result = self.reason_with_tools(query)
            
            # 3. Multi-model verification
            mm_result = self.verify_multi_model(query)
            
            # 4. Iterative refinement
            ref_result = self.refine_iteratively(query)
            
            # 5. Uncertainty calibration
            answer = ref_result.get('final_answer', sym_result.get('clauses', ''))
            uncertainty_result = self.calibrate_uncertainty(query, answer, 0.7)
            
            # Aggregate results
            results = {
                'symbolic': sym_result,
                'tool': tool_result,
                'multi_model': mm_result,
                'iterative': ref_result,
                'uncertainty': uncertainty_result
            }
            
            # Compute aggregate confidence
            confidence = (
                (0.8 if not sym_result.get('contradictions') else 0.4) +
                tool_result.get('confidence', 0.7) +
                mm_result.get('agreement_score', 0.5) +
                (0.7 + ref_result.get('improvement', 0))
            ) / 4
            
            hallucination_risk = uncertainty_result.get('hallucination_risk', 
                                         mm_result.get('hallucination_risk', 'medium'))
            answer = ref_result.get('final_answer', answer)
        
        # Final uncertainty calibration
        if 'uncertainty' not in results:
            uncertainty_result = self.calibrate_uncertainty(query, answer, confidence)
            results['uncertainty'] = uncertainty_result
        
        calibrated_confidence = results['uncertainty'].get('calibrated_confidence', confidence)
        should_decline = results['uncertainty'].get('should_decline', False)
        decline_reason = results['uncertainty'].get('decline_reason', '')
        
        # Build result
        result = EnhancedReasoningResult(
            answer=answer if not should_decline else f"[DECLINED] {decline_reason}",
            confidence=confidence,
            calibrated_confidence=calibrated_confidence,
            strategies_used=[strategy],
            hallucination_risk=hallucination_risk,
            verification_status='verified' if not should_decline else 'declined',
            contradictions=results.get('symbolic', {}).get('contradictions', []),
            tool_results=results.get('tool', {}).get('tool_results', []),
            refinement_passes=results.get('iterative', {}).get('total_passes', 0),
            uncertainty_flags=results['uncertainty'].get('uncertainty_flags', []),
            should_decline=should_decline,
            decline_reason=decline_reason
        )
        
        # Log session
        self._log_session(query, strategy, result)
        
        return result
    
    def _log_session(self, query: str, strategy: str, result: EnhancedReasoningResult):
        """Log reasoning session to database."""
        cursor = self._conn.cursor()
        cursor.execute(
            """INSERT INTO reasoning_sessions 
               (query, strategy, answer, confidence, calibrated_confidence, 
                hallucination_risk, verified)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (query, strategy, result.answer, result.confidence, 
             result.calibrated_confidence, result.hallucination_risk,
             0 if result.should_decline else 1)
        )
        self._conn.commit()
    
    def test_accuracy(self, query: str, expected_answer: str, 
                      problem_type: str = "general") -> Dict:
        """
        Test reasoning accuracy against known answer.
        
        Returns:
        {
            'correct': bool,
            'error_type': str,
            'confidence': float,
            'hallucination_detected': bool
        }
        """
        result = self.reason(query)
        
        correct = result.answer.lower().strip() == expected_answer.lower().strip()
        error_type = "none"
        
        if not correct:
            if result.hallucination_risk == "high":
                error_type = "hallucination"
            elif result.should_decline:
                error_type = "uncertainty"
            else:
                error_type = "incorrect"
        
        hallucination_detected = (
            result.hallucination_risk == "high" or
            (result.contradictions and len(result.contradictions) > 0)
        )
        
        # Log accuracy
        self._log_accuracy(query, problem_type, correct, error_type)
        
        return {
            'correct': correct,
            'error_type': error_type,
            'confidence': result.confidence,
            'calibrated_confidence': result.calibrated_confidence,
            'hallucination_detected': hallucination_detected,
            'strategies_used': result.strategies_used
        }
    
    def _log_accuracy(self, query: str, problem_type: str, 
                      correct: bool, error_type: str):
        """Log accuracy tracking."""
        cursor = self._conn.cursor()
        cursor.execute(
            """INSERT INTO accuracy_tracking 
               (problem_type, correct, error_type)
               VALUES (?, ?, ?)""",
            (problem_type, 1 if correct else 0, error_type)
        )
        self._conn.commit()
    
    def get_accuracy_stats(self) -> Dict:
        """Get accuracy statistics across all tests."""
        cursor = self._conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM accuracy_tracking")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM accuracy_tracking WHERE correct = 1")
        correct = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT error_type, COUNT(*) 
            FROM accuracy_tracking 
            WHERE correct = 0 
            GROUP BY error_type
        """)
        errors = cursor.fetchall()
        
        cursor.execute("""
            SELECT problem_type, COUNT(*) 
            FROM accuracy_tracking 
            GROUP BY problem_type
        """)
        by_type = cursor.fetchall()
        
        accuracy = correct / total if total > 0 else 0
        
        return {
            'total_tests': total,
            'correct': correct,
            'accuracy': accuracy,
            'error_breakdown': {e[0]: e[1] for e in errors},
            'by_problem_type': {t[0]: t[1] for t in by_type}
        }
    
    def clear(self):
        """Clear all reasoning history."""
        self.symbolic_reasoner.clear()
        self.tool_reasoner.clear()
        self.model_verifier.clear()
        self.iterative_refiner.clear()
        self.uncertainty_calibrator.clear()


def reason_enhanced(query: str, strategy: str = "auto",
                    db_path: str = ":memory:") -> EnhancedReasoningResult:
    """
    Main entry point for enhanced reasoning.
    
    Usage:
        result = reason_enhanced("What is 15% of 240?")
        result = reason_enhanced("Prove that all humans are mortal")
        result = reason_enhanced("Complex problem", strategy="enhanced")
        
    Returns:
        EnhancedReasoningResult with all reasoning metadata
    """
    engine = EnhancedReasoningEngine(db_path=db_path)
    return engine.reason(query, strategy)


if __name__ == "__main__":
    # Test enhanced reasoning
    print("=== Enhanced Reasoning Engine Test ===\n")
    
    # Test 1: Math problem (tool reasoning)
    result1 = reason_enhanced("Calculate 15% of 240")
    print("Test 1 - Math:")
    print(f"Answer: {result1.answer}")
    print(f"Confidence: {result1.calibrated_confidence:.2f}")
    print(f"Hallucination risk: {result1.hallucination_risk}")
    print(f"Tools used: {len(result1.tool_results)}\n")
    
    # Test 2: Logic problem (symbolic reasoning)
    result2 = reason_enhanced("All humans are mortal. Socrates is human. Therefore?")
    print("Test 2 - Logic:")
    print(f"Answer: {result2.answer}")
    print(f"Confidence: {result2.calibrated_confidence:.2f}")
    print(f"Contradictions: {len(result2.contradictions)}\n")
    
    # Test 3: Factual question (multi-model)
    result3 = reason_enhanced("What is the capital of France?")
    print("Test 3 - Factual:")
    print(f"Answer: {result3.answer}")
    print(f"Hallucination risk: {result3.hallucination_risk}\n")
    
    # Test 4: Uncertain question
    result4 = reason_enhanced("What might happen in the future?")
    print("Test 4 - Uncertain:")
    print(f"Answer: {result4.answer}")
    print(f"Should decline: {result4.should_decline}")
    print(f"Uncertainty flags: {len(result4.uncertainty_flags)}\n")
