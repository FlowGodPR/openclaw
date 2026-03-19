"""
Uncertainty Calibration Module
Know when you don't know and say so

This module implements uncertainty awareness:
- Confidence scoring with calibration
- Knowledge boundary detection
- "I don't know" recognition
- Uncertainty source identification
- Appropriate hedging language
"""

import sqlite3
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class UncertaintyType(Enum):
    KNOWLEDGE_GAP = "knowledge_gap"  # Don't have the information
    AMBIGUITY = "ambiguity"  # Question is unclear
    LOW_CONFIDENCE = "low_confidence"  # Weak evidence
    CONTRADICTORY = "contradictory"  # Conflicting information
    OUT_OF_SCOPE = "out_of_scope"  # Beyond domain expertise
    SPECULATION = "speculation"  # Requires guessing


@dataclass
class UncertaintySignal:
    signal_type: UncertaintyType
    trigger: str
    confidence_impact: float
    suggestion: str


@dataclass
class CalibratedResponse:
    answer: str
    confidence: float
    calibrated_confidence: float
    uncertainty_flags: List[UncertaintySignal]
    knowledge_boundary: str
    should_decline: bool
    decline_reason: str
    hedging_level: str


class UncertaintyCalibrator:
    """
    Implements uncertainty awareness and calibration.
    
    Architecture:
    1. Detect uncertainty signals in query/answer
    2. Assess knowledge boundaries
    3. Calibrate confidence appropriately
    4. Decide when to decline answering
    5. Apply appropriate hedging language
    """
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.confidence_history: List[float] = []
        self.calibration_errors: List[float] = []
        self._conn = None
        self._init_db()
        self._load_uncertainty_patterns()
    
    def _init_db(self):
        """Initialize SQLite for uncertainty tracking."""
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self._conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uncertainty_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                raw_confidence REAL,
                calibrated_confidence REAL,
                uncertainty_types TEXT,
                declined INTEGER DEFAULT 0,
                decline_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calibration_accuracy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                predicted_confidence REAL,
                actual_correct INTEGER,
                error REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self._conn.commit()
    
    def _load_uncertainty_patterns(self):
        """Load patterns for uncertainty detection."""
        
        self.knowledge_gap_patterns = [
            (r'never heard of', "Unfamiliar concept"),
            (r'don\'t know', "Explicit uncertainty"),
            (r'no information', "Missing data"),
            (r'not sure', "Low confidence"),
            (r'unknown', "Knowledge boundary"),
            (r'cannot determine', "Undecidable"),
            (r'insufficient', "Incomplete information"),
            (r'unclear', "Ambiguous"),
        ]
        
        self.speculation_patterns = [
            (r'probably', "Speculative claim"),
            (r'maybe', "Uncertain claim"),
            (r'perhaps', "Speculative claim"),
            (r'likely', "Probabilistic claim"),
            (r'might', "Uncertain claim"),
            (r'could', "Speculative claim"),
            (r'possibly', "Uncertain claim"),
            (r'i think', "Subjective belief"),
            (r'i believe', "Subjective belief"),
            (r'guess', "Speculation"),
        ]
        
        self.ambiguity_patterns = [
            (r'what do you mean', "Clarification needed"),
            (r'unclear', "Ambiguous query"),
            (r'vague', "Imprecise query"),
            (r'could mean', "Multiple interpretations"),
            (r'depends', "Context-dependent"),
        ]
    
    def detect_knowledge_gaps(self, query: str, answer: str) -> List[UncertaintySignal]:
        """Detect knowledge gap signals."""
        signals = []
        
        for pattern, suggestion in self.knowledge_gap_patterns:
            if re.search(pattern, answer, re.IGNORECASE):
                signals.append(UncertaintySignal(
                    signal_type=UncertaintyType.KNOWLEDGE_GAP,
                    trigger=pattern,
                    confidence_impact=-0.3,
                    suggestion=suggestion
                ))
        
        # Check for out-of-domain queries
        out_of_domain = self._check_domain_boundary(query)
        if out_of_domain:
            signals.append(UncertaintySignal(
                signal_type=UncertaintyType.OUT_OF_SCOPE,
                trigger="domain_mismatch",
                confidence_impact=-0.4,
                suggestion="Query outside knowledge domain"
            ))
        
        return signals
    
    def detect_speculation(self, answer: str) -> List[UncertaintySignal]:
        """Detect speculation and hedging."""
        signals = []
        
        count = 0
        for pattern, suggestion in self.speculation_patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            count += len(matches)
            if matches:
                signals.append(UncertaintySignal(
                    signal_type=UncertaintyType.SPECULATION,
                    trigger=pattern,
                    confidence_impact=-0.1 * len(matches),
                    suggestion=suggestion
                ))
        
        # High speculation → significant confidence reduction
        if count >= 3:
            signals.append(UncertaintySignal(
                signal_type=UncertaintyType.LOW_CONFIDENCE,
                trigger="excessive_hedging",
                confidence_impact=-0.3,
                suggestion="Multiple uncertainty markers detected"
            ))
        
        return signals
    
    def detect_ambiguity(self, query: str) -> List[UncertaintySignal]:
        """Detect query ambiguity."""
        signals = []
        
        for pattern, suggestion in self.ambiguity_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                signals.append(UncertaintySignal(
                    signal_type=UncertaintyType.AMBIGUITY,
                    trigger=pattern,
                    confidence_impact=-0.2,
                    suggestion=suggestion
                ))
        
        # Check for vague queries
        if len(query.split()) < 3:
            signals.append(UncertaintySignal(
                signal_type=UncertaintyType.AMBIGUITY,
                trigger="too_short",
                confidence_impact=-0.2,
                suggestion="Query may be too brief"
            ))
        
        return signals
    
    def _check_domain_boundary(self, query: str) -> bool:
        """Check if query is out of domain."""
        # Placeholder domain check
        # In production, would check against known knowledge boundaries
        
        out_of_domain_keywords = [
            "future prediction", "unreleased", "not yet announced",
            "classified", "secret", "private"
        ]
        
        for keyword in out_of_domain_keywords:
            if keyword in query.lower():
                return True
        
        return False
    
    def calibrate_confidence(self, raw_confidence: float, 
                             signals: List[UncertaintySignal]) -> float:
        """
        Adjust confidence based on uncertainty signals.
        
        Calibration formula:
        calibrated = raw + Σ(impact adjustments)
        bounded to [0.0, 1.0]
        """
        total_impact = sum(s.confidence_impact for s in signals)
        calibrated = raw_confidence + total_impact
        return max(0.0, min(1.0, calibrated))
    
    def should_decline(self, signals: List[UncertaintySignal], 
                       calibrated_confidence: float) -> Tuple[bool, str]:
        """
        Decide whether to decline answering.
        
        Decline conditions:
        - Knowledge gap with no recoverable path
        - Calibrated confidence < 0.3
        - Multiple high-severity uncertainty signals
        - Out of scope domain
        """
        high_severity = sum(1 for s in signals 
                           if s.signal_type in [UncertaintyType.KNOWLEDGE_GAP, 
                                                UncertaintyType.OUT_OF_SCOPE] 
                           and s.confidence_impact < -0.3)
        
        if calibrated_confidence < 0.3:
            return True, "Confidence too low to provide reliable answer"
        
        if high_severity >= 2:
            return True, "Multiple critical uncertainty signals detected"
        
        if any(s.signal_type == UncertaintyType.OUT_OF_SCOPE for s in signals):
            return True, "Query outside knowledge domain"
        
        return False, ""
    
    def get_hedging_level(self, calibrated_confidence: float) -> str:
        """
        Determine appropriate hedging level.
        
        Levels:
        - none: confidence >= 0.8
        - mild: confidence 0.6-0.8
        - moderate: confidence 0.4-0.6
        - strong: confidence < 0.4
        """
        if calibrated_confidence >= 0.8:
            return "none"
        elif calibrated_confidence >= 0.6:
            return "mild"
        elif calibrated_confidence >= 0.4:
            return "moderate"
        else:
            return "strong"
    
    def get_hedging_phrases(self, level: str) -> List[str]:
        """Get appropriate hedging phrases for confidence level."""
        phrases = {
            "none": [],
            "mild": ["appears to", "suggests", "indicates"],
            "moderate": ["likely", "probably", "seems to"],
            "strong": ["may", "might", "possibly", "uncertain"]
        }
        return phrases.get(level, [])
    
    def calibrate(self, query: str, answer: str, 
                  raw_confidence: float = 0.7) -> CalibratedResponse:
        """
        Full uncertainty calibration pipeline.
        
        Process:
        1. Detect uncertainty signals
        2. Calibrate confidence
        3. Assess knowledge boundary
        4. Decide on declining
        5. Determine hedging level
        
        Returns:
        CalibratedResponse with all findings
        """
        # Step 1: Detect signals
        knowledge_signals = self.detect_knowledge_gaps(query, answer)
        speculation_signals = self.detect_speculation(answer)
        ambiguity_signals = self.detect_ambiguity(query)
        
        all_signals = knowledge_signals + speculation_signals + ambiguity_signals
        
        # Step 2: Calibrate confidence
        calibrated = self.calibrate_confidence(raw_confidence, all_signals)
        
        # Step 3: Knowledge boundary
        boundary = "within_domain" if not knowledge_signals else "knowledge_gap_detected"
        
        # Step 4: Decline decision
        should_decline, decline_reason = self.should_decline(all_signals, calibrated)
        
        # Step 5: Hedging level
        hedging_level = self.get_hedging_level(calibrated)
        
        # Track calibration
        self.confidence_history.append(calibrated)
        
        # Log to database
        self._log_uncertainty(query, raw_confidence, calibrated, all_signals, 
                             should_decline, decline_reason)
        
        return CalibratedResponse(
            answer=answer,
            confidence=raw_confidence,
            calibrated_confidence=calibrated,
            uncertainty_flags=all_signals,
            knowledge_boundary=boundary,
            should_decline=should_decline,
            decline_reason=decline_reason,
            hedging_level=hedging_level
        )
    
    def record_calibration_accuracy(self, predicted: float, actual_correct: bool):
        """Track calibration accuracy for learning."""
        error = abs(predicted - (1.0 if actual_correct else 0.0))
        self.calibration_errors.append(error)
        self._log_accuracy(predicted, actual_correct, error)
    
    def get_calibration_stats(self) -> Dict:
        """Get calibration statistics."""
        if not self.calibration_errors:
            return {"mean_error": 0, "samples": 0}
        
        mean_error = sum(self.calibration_errors) / len(self.calibration_errors)
        return {
            "mean_error": mean_error,
            "samples": len(self.calibration_errors),
            "calibration_quality": "good" if mean_error < 0.2 else "needs_improvement"
        }
    
    def _log_uncertainty(self, query: str, raw: float, calibrated: float,
                         signals: List[UncertaintySignal], 
                         declined: bool, reason: str):
        """Log uncertainty calibration to database."""
        cursor = self._conn.cursor()
        types = json.dumps([s.signal_type.value for s in signals])
        cursor.execute(
            """INSERT INTO uncertainty_logs 
               (query, raw_confidence, calibrated_confidence, uncertainty_types, declined, decline_reason)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (query, raw, calibrated, types, 1 if declined else 0, reason)
        )
        self._conn.commit()
    
    def _log_accuracy(self, predicted: float, correct: bool, error: float):
        """Log calibration accuracy."""
        cursor = self._conn.cursor()
        cursor.execute(
            """INSERT INTO calibration_accuracy 
               (predicted_confidence, actual_correct, error)
               VALUES (?, ?, ?)""",
            (predicted, 1 if correct else 0, error)
        )
        self._conn.commit()
    
    def clear(self):
        """Clear history."""
        self.confidence_history = []
        self.calibration_errors = []


def calibrate_uncertainty(query: str, answer: str,
                          raw_confidence: float = 0.7,
                          db_path: str = ":memory:") -> CalibratedResponse:
    """
    Main entry point for uncertainty calibration.
    
    Usage:
        result = calibrate_uncertainty("What is dark matter?", "Dark matter is...")
        
    Returns:
        CalibratedResponse with:
        - answer: str
        - confidence: float (raw)
        - calibrated_confidence: float (adjusted)
        - uncertainty_flags: list
        - knowledge_boundary: str
        - should_decline: bool
        - decline_reason: str
        - hedging_level: str
    """
    calibrator = UncertaintyCalibrator(db_path=db_path)
    return calibrator.calibrate(query, answer, raw_confidence)


if __name__ == "__main__":
    # Test with confident answer
    result1 = calibrate_uncertainty(
        "What is 2+2?",
        "2+2 equals 4. This is basic arithmetic."
    )
    print("Confident answer test:")
    print(f"Calibrated confidence: {result1.calibrated_confidence}")
    print(f"Hedging level: {result1.hedging_level}")
    print(f"Should decline: {result1.should_decline}")
    
    # Test with uncertain answer
    result2 = calibrate_uncertainty(
        "What will happen in 2050?",
        "I'm not sure, but maybe it could probably be something..."
    )
    print("\nUncertain answer test:")
    print(f"Calibrated confidence: {result2.calibrated_confidence}")
    print(f"Uncertainty flags: {len(result2.uncertainty_flags)}")
    print(f"Hedging level: {result2.hedging_level}")
    print(f"Should decline: {result2.should_decline}")
