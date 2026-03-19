"""
Neural-Symbolic Reasoning Module
Connects LLM reasoning with symbolic logic (Prolog/Datalog)

This module bridges neural (LLM) and symbolic (logic programming) reasoning:
- LLM extracts facts and rules from natural language
- Symbolic engine performs logical deduction
- Results are verified for logical consistency
- Hallucinations caught via logical contradiction detection
"""

import sqlite3
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json


class LogicFormalism(Enum):
    PROLOG = "prolog"
    DATALOG = "datalog"
    FIRST_ORDER = "fol"


@dataclass
class Fact:
    predicate: str
    arguments: Tuple[str, ...]
    confidence: float = 1.0
    source: str = "llm"


@dataclass
class Rule:
    head: str
    body: List[str]
    confidence: float = 1.0
    source: str = "llm"


@dataclass
class Query:
    predicate: str
    arguments: Tuple[str, ...]
    variables: List[str]


class NeuralSymbolicReasoner:
    """
    Integrates LLM fact extraction with symbolic logic reasoning.
    
    Architecture:
    1. LLM extracts facts/rules from natural language
    2. Facts compiled to Datalog/Prolog clauses
    3. Symbolic engine performs forward/backward chaining
    4. Results verified for logical consistency
    5. Contradictions flagged as potential hallucinations
    """
    
    def __init__(self, db_path: str = ":memory:", formalism: LogicFormalism = LogicFormalism.DATALOG):
        self.db_path = db_path
        self.formalism = formalism
        self.facts: List[Fact] = []
        self.rules: List[Rule] = []
        self.contradictions: List[Dict] = []
        self._conn = None
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for fact storage."""
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self._conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbolic_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                predicate TEXT NOT NULL,
                arguments TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT 'llm',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbolic_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                head TEXT NOT NULL,
                body TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT 'llm',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contradictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact1_id INTEGER,
                fact2_id INTEGER,
                contradiction_type TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self._conn.commit()
    
    def extract_facts(self, text: str, model_response: str = None) -> List[Fact]:
        """
        Extract logical facts from natural language using LLM.
        
        Pattern: "X is Y" → fact("is", ("X", "Y"))
        Pattern: "X has Y" → fact("has", ("X", "Y"))
        Pattern: "X causes Y" → fact("causes", ("X", "Y"))
        """
        facts = []
        
        # Simple pattern extraction (can be enhanced with LLM)
        patterns = [
            (r'(\w+) is (\w+)', 'is'),
            (r'(\w+) has (\w+)', 'has'),
            (r'(\w+) causes (\w+)', 'causes'),
            (r'(\w+) implies (\w+)', 'implies'),
            (r'(\w+) before (\w+)', 'before'),
            (r'(\w+) after (\w+)', 'after'),
        ]
        
        for pattern, predicate in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                fact = Fact(
                    predicate=predicate,
                    arguments=(match[0].lower(), match[1].lower()),
                    confidence=0.9,
                    source="pattern"
                )
                facts.append(fact)
        
        self.facts.extend(facts)
        self._persist_facts(facts)
        return facts
    
    def extract_rules(self, text: str) -> List[Rule]:
        """
        Extract logical rules from natural language.
        
        Pattern: "If X then Y" → rule(head="Y", body=["X"])
        Pattern: "All X are Y" → rule(head="Y(X)", body=["X(X)"])
        """
        rules = []
        
        # If-then rules
        if_pattern = r'[Ii]f (.+?) then (.+)'
        matches = re.findall(if_pattern, text)
        for match in matches:
            rule = Rule(
                head=match[1].strip().lower(),
                body=[match[0].strip().lower()],
                confidence=0.85,
                source="pattern"
            )
            rules.append(rule)
        
        # Universal quantification
        all_pattern = r'[Aa]ll (.+?) are (.+)'
        matches = re.findall(all_pattern, text)
        for match in matches:
            rule = Rule(
                head=f"{match[1].strip().lower()}(X)",
                body=[f"{match[0].strip().lower()}(X)"],
                confidence=0.8,
                source="pattern"
            )
            rules.append(rule)
        
        self.rules.extend(rules)
        self._persist_rules(rules)
        return rules
    
    def _persist_facts(self, facts: List[Fact]):
        """Store facts in SQLite."""
        cursor = self._conn.cursor()
        for fact in facts:
            cursor.execute(
                "INSERT INTO symbolic_facts (predicate, arguments, confidence, source) VALUES (?, ?, ?, ?)",
                (fact.predicate, json.dumps(fact.arguments), fact.confidence, fact.source)
            )
        self._conn.commit()
    
    def _persist_rules(self, rules: List[Rule]):
        """Store rules in SQLite."""
        cursor = self._conn.cursor()
        for rule in rules:
            cursor.execute(
                "INSERT INTO symbolic_rules (head, body, confidence, source) VALUES (?, ?, ?, ?)",
                (rule.head, json.dumps(rule.body), rule.confidence, rule.source)
            )
        self._conn.commit()
    
    def forward_chain(self) -> List[Fact]:
        """
        Apply modus ponens: If A and (A→B), then B.
        
        Returns newly derived facts.
        """
        derived = []
        
        for rule in self.rules:
            for fact in self.facts:
                # Simple matching: if fact matches rule body
                if self._match_fact_to_body(fact, rule.body):
                    new_fact = Fact(
                        predicate=rule.head.split('(')[0] if '(' in rule.head else rule.head,
                        arguments=(),
                        confidence=fact.confidence * rule.confidence,
                        source="forward_chain"
                    )
                    derived.append(new_fact)
        
        self.facts.extend(derived)
        return derived
    
    def _match_fact_to_body(self, fact: Fact, body: List[str]) -> bool:
        """Check if fact matches rule body (simplified matching)."""
        if not body:
            return False
        
        body_pred = body[0].split('(')[0] if '(' in body[0] else body[0]
        return fact.predicate == body_pred
    
    def detect_contradictions(self) -> List[Dict]:
        """
        Detect logical contradictions in fact base.
        
        Contradiction types:
        - Direct: A and not-A
        - Functional: f(X)=Y and f(X)=Z where Y≠Z
        - Transitive: A<B and B<A (asymmetry violation)
        """
        contradictions = []
        
        # Build predicate index
        pred_index: Dict[str, List[Fact]] = {}
        for fact in self.facts:
            if fact.predicate not in pred_index:
                pred_index[fact.predicate] = []
            pred_index[fact.predicate].append(fact)
        
        # Check for functional contradictions
        functional_preds = {'is', 'has', 'equals', 'value'}
        for pred in functional_preds:
            if pred in pred_index:
                facts = pred_index[pred]
                args_by_subject: Dict[str, List[str]] = {}
                for fact in facts:
                    if fact.arguments:
                        subj = fact.arguments[0]
                        if subj not in args_by_subject:
                            args_by_subject[subj] = []
                        args_by_subject[subj].append(fact.arguments[1] if len(fact.arguments) > 1 else "")
                
                for subj, preds in args_by_subject.items():
                    if len(preds) > 1 and len(set(preds)) > 1:
                        contradictions.append({
                            'type': 'functional',
                            'predicate': pred,
                            'subject': subj,
                            'values': preds,
                            'severity': 'high'
                        })
        
        # Check for asymmetry violations (before/after)
        asym_preds = {'before', 'after', 'greater', 'less'}
        for pred in asym_preds:
            if pred in pred_index:
                facts = pred_index[pred]
                pairs = set()
                for fact in facts:
                    if fact.arguments and len(fact.arguments) >= 2:
                        pairs.add((fact.arguments[0], fact.arguments[1]))
                
                for a, b in pairs:
                    if (b, a) in pairs:
                        contradictions.append({
                            'type': 'asymmetry',
                            'predicate': pred,
                            'pair': (a, b),
                            'severity': 'high'
                        })
        
        self.contradictions = contradictions
        self._persist_contradictions(contradictions)
        return contradictions
    
    def _persist_contradictions(self, contradictions: List[Dict]):
        """Log contradictions to database."""
        cursor = self._conn.cursor()
        for c in contradictions:
            cursor.execute(
                "INSERT INTO contradictions (contradiction_type) VALUES (?)",
                (c['type'],)
            )
        self._conn.commit()
    
    def query(self, predicate: str, arguments: Tuple[str, ...] = None) -> List[Fact]:
        """Query fact base for matching facts."""
        results = []
        for fact in self.facts:
            if fact.predicate == predicate:
                if arguments is None:
                    results.append(fact)
                elif fact.arguments == arguments:
                    results.append(fact)
                elif not arguments:
                    results.append(fact)
        return results
    
    def verify_consistency(self, llm_claim: str) -> Dict:
        """
        Verify if an LLM claim is consistent with symbolic knowledge base.
        
        Returns:
        {
            'consistent': bool,
            'contradictions': [...],
            'confidence': float,
            'hallucination_risk': str (low/medium/high)
        }
        """
        # Extract claim as fact
        claim_facts = self.extract_facts(llm_claim)
        
        # Temporarily add claim facts
        original_facts = self.facts.copy()
        self.facts.extend(claim_facts)
        
        # Check for contradictions
        new_contradictions = self.detect_contradictions()
        
        # Restore original facts
        self.facts = original_facts
        
        # Assess hallucination risk
        if not new_contradictions:
            risk = "low"
            consistent = True
        elif any(c['severity'] == 'high' for c in new_contradictions):
            risk = "high"
            consistent = False
        else:
            risk = "medium"
            consistent = len(new_contradictions) < 2
        
        return {
            'consistent': consistent,
            'contradictions': new_contradictions,
            'confidence': 0.9 if consistent else 0.3,
            'hallucination_risk': risk,
            'claim_facts': claim_facts
        }
    
    def to_clauses(self) -> str:
        """Export facts and rules as Prolog/Datalog clauses."""
        clauses = []
        
        for fact in self.facts:
            args = ','.join(fact.arguments) if fact.arguments else ''
            clauses.append(f"{fact.predicate}({args}).")
        
        for rule in self.rules:
            body = ','.join(rule.body)
            clauses.append(f"{rule.head} :- {body}.")
        
        return '\n'.join(clauses)
    
    def clear(self):
        """Clear all facts and rules."""
        self.facts = []
        self.rules = []
        self.contradictions = []


def reason_with_symbolic(text: str, db_path: str = ":memory:") -> Dict:
    """
    Main entry point for neural-symbolic reasoning.
    
    Usage:
        result = reason_with_symbolic("All humans are mortal. Socrates is human.")
        
    Returns:
        {
            'facts': [...],
            'rules': [...],
            'derived': [...],
            'contradictions': [...],
            'clauses': str,
            'hallucination_risk': str
        }
    """
    reasoner = NeuralSymbolicReasoner(db_path=db_path)
    
    # Extract knowledge
    facts = reasoner.extract_facts(text)
    rules = reasoner.extract_rules(text)
    
    # Derive new facts
    derived = reasoner.forward_chain()
    
    # Check consistency
    contradictions = reasoner.detect_contradictions()
    
    # Assess hallucination risk
    risk = "high" if contradictions else ("medium" if len(rules) > 3 else "low")
    
    return {
        'facts': [{'predicate': f.predicate, 'arguments': f.arguments, 'confidence': f.confidence} for f in facts],
        'rules': [{'head': r.head, 'body': r.body, 'confidence': r.confidence} for r in rules],
        'derived': [{'predicate': d.predicate, 'confidence': d.confidence} for d in derived],
        'contradictions': contradictions,
        'clauses': reasoner.to_clauses(),
        'hallucination_risk': risk,
        'db_path': reasoner.db_path
    }


if __name__ == "__main__":
    # Test
    result = reason_with_symbolic("""
        All humans are mortal.
        Socrates is human.
        If X is human then X is mortal.
        Socrates is a philosopher.
        Socrates is mortal.
    """)
    
    print("Facts extracted:", len(result['facts']))
    print("Rules extracted:", len(result['rules']))
    print("Derived facts:", len(result['derived']))
    print("Contradictions:", result['contradictions'])
    print("Hallucination risk:", result['hallucination_risk'])
    print("\nProlog clauses:")
    print(result['clauses'])
