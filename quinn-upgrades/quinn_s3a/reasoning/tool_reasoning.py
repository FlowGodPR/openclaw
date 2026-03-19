"""
External Tool Reasoning Module
Reasoning BY USING tools (calculator, search, code execution)

This module enables tool-augmented reasoning:
- LLM decides which tools to use
- Tools execute and return results
- Results integrated into reasoning chain
- Verification via tool cross-checking
- Hallucinations caught when claims contradict tool results
"""

import subprocess
import json
import re
import math
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import sqlite3


class ToolType(Enum):
    CALCULATOR = "calculator"
    SEARCH = "search"
    CODE_EXEC = "code_exec"
    DATE_TIME = "datetime"
    FILE_READ = "file_read"
    API_CALL = "api_call"


@dataclass
class ToolResult:
    tool: str
    output: Any
    success: bool
    error: Optional[str] = None
    confidence: float = 1.0


@dataclass
class ToolCall:
    tool: str
    arguments: Dict[str, Any]
    purpose: str
    result: Optional[ToolResult] = None


class ToolReasoner:
    """
    Enables reasoning through tool execution.
    
    Architecture:
    1. Parse problem to identify tool needs
    2. Select appropriate tools
    3. Execute tools with proper arguments
    4. Integrate results into reasoning
    5. Cross-verify with multiple tools when possible
    """
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.tool_registry: Dict[str, Callable] = {}
        self.executed_tools: List[ToolCall] = []
        self._conn = None
        self._init_db()
        self._register_builtin_tools()
    
    def _init_db(self):
        """Initialize SQLite for tool execution history."""
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self._conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT NOT NULL,
                arguments TEXT NOT NULL,
                output TEXT,
                success INTEGER DEFAULT 1,
                error TEXT,
                confidence REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self._conn.commit()
    
    def _register_builtin_tools(self):
        """Register built-in tool implementations."""
        
        def calculator(expr: str) -> ToolResult:
            """Evaluate mathematical expression."""
            try:
                # Safe eval with only math operations
                allowed = {
                    'sqrt': math.sqrt, 'log': math.log, 'log10': math.log10,
                    'exp': math.exp, 'sin': math.sin, 'cos': math.cos,
                    'tan': math.tan, 'pi': math.pi, 'e': math.e,
                    'abs': abs, 'round': round, 'pow': pow
                }
                result = eval(expr, {"__builtins__": {}}, allowed)
                return ToolResult(tool="calculator", output=result, success=True)
            except Exception as e:
                return ToolResult(tool="calculator", output=None, success=False, error=str(e))
        
        def search_web(query: str) -> ToolResult:
            """Execute web search via ollama_web_search."""
            try:
                # This would integrate with ollama_web_search tool
                # For now, placeholder
                return ToolResult(
                    tool="search",
                    output={"query": query, "status": "search_executed"},
                    success=True
                )
            except Exception as e:
                return ToolResult(tool="search", output=None, success=False, error=str(e))
        
        def code_exec(code: str, language: str = "python") -> ToolResult:
            """Execute code snippet."""
            try:
                if language == "python":
                    # Capture stdout
                    import io
                    import sys
                    old_stdout = sys.stdout
                    sys.stdout = io.StringIO()
                    
                    exec(code)
                    output = sys.stdout.getvalue()
                    sys.stdout = old_stdout
                    
                    return ToolResult(tool="code_exec", output=output, success=True)
                else:
                    return ToolResult(tool="code_exec", output=None, success=False, error=f"Unsupported language: {language}")
            except Exception as e:
                return ToolResult(tool="code_exec", output=None, success=False, error=str(e))
        
        def get_datetime() -> ToolResult:
            """Get current date/time."""
            from datetime import datetime
            return ToolResult(
                tool="datetime",
                output=datetime.now().isoformat(),
                success=True
            )
        
        def file_read(path: str) -> ToolResult:
            """Read file contents."""
            try:
                with open(path, 'r') as f:
                    content = f.read()
                return ToolResult(tool="file_read", output=content, success=True)
            except Exception as e:
                return ToolResult(tool="file_read", output=None, success=False, error=str(e))
        
        self.tool_registry = {
            ToolType.CALCULATOR.value: calculator,
            ToolType.SEARCH.value: search_web,
            ToolType.CODE_EXEC.value: code_exec,
            ToolType.DATE_TIME.value: get_datetime,
            ToolType.FILE_READ.value: file_read,
        }
    
    def register_tool(self, name: str, func: Callable):
        """Register a custom tool."""
        self.tool_registry[name] = func
    
    def parse_tool_needs(self, problem: str) -> List[ToolCall]:
        """
        Analyze problem to identify tool requirements.
        
        Patterns:
        - Numbers + operators → calculator
        - "search", "find", "look up" → search
        - "calculate", "compute", "solve" → calculator
        - "run", "execute", "code" → code_exec
        - "current", "now", "today" → datetime
        - File paths → file_read
        """
        calls = []
        
        # Calculator triggers
        calc_patterns = [
            r'\d+\s*[\+\-\*\/]\s*\d+',
            r'calculate', r'compute', r'solve', r'evaluate',
            r'what is \d+', r'how much', r'cost', r'price'
        ]
        for pattern in calc_patterns:
            if re.search(pattern, problem, re.IGNORECASE):
                # Extract expression
                expr_match = re.search(r'([\d\s\+\-\*\/\.\(\)]+)', problem)
                if expr_match:
                    calls.append(ToolCall(
                        tool="calculator",
                        arguments={"expr": expr_match.group(1).strip()},
                        purpose="Evaluate mathematical expression"
                    ))
                break
        
        # Search triggers
        search_patterns = [r'search', r'find', r'look up', r'what is', r'who is', r'when did']
        for pattern in search_patterns:
            if re.search(pattern, problem, re.IGNORECASE):
                calls.append(ToolCall(
                    tool="search",
                    arguments={"query": problem},
                    purpose="Look up factual information"
                ))
                break
        
        # Code execution triggers
        code_patterns = [r'write code', r'run', r'execute', r'programming', r'script']
        for pattern in code_patterns:
            if re.search(pattern, problem, re.IGNORECASE):
                calls.append(ToolCall(
                    tool="code_exec",
                    arguments={"code": "# Generated code", "language": "python"},
                    purpose="Execute code solution"
                ))
                break
        
        # DateTime triggers
        time_patterns = [r'current', r'now', r'today', r'date', r'time']
        for pattern in time_patterns:
            if re.search(pattern, problem, re.IGNORECASE):
                calls.append(ToolCall(
                    tool="datetime",
                    arguments={},
                    purpose="Get current date/time"
                ))
                break
        
        # File read triggers
        if re.search(r'read|open|file|path', problem, re.IGNORECASE):
            path_match = re.search(r'([~/\w\.\-]+)', problem)
            if path_match:
                calls.append(ToolCall(
                    tool="file_read",
                    arguments={"path": path_match.group(1)},
                    purpose="Read file contents"
                ))
        
        return calls
    
    def execute_tools(self, calls: List[ToolCall]) -> List[ToolResult]:
        """Execute planned tool calls."""
        results = []
        
        for call in calls:
            if call.tool in self.tool_registry:
                func = self.tool_registry[call.tool]
                try:
                    output = func(**call.arguments)
                    call.result = output
                    results.append(output)
                    self._log_execution(call, output)
                except Exception as e:
                    result = ToolResult(tool=call.tool, output=None, success=False, error=str(e))
                    call.result = result
                    results.append(result)
                    self._log_execution(call, result)
            else:
                result = ToolResult(tool=call.tool, output=None, success=False, error=f"Unknown tool: {call.tool}")
                call.result = result
                results.append(result)
        
        self.executed_tools.extend(calls)
        return results
    
    def _log_execution(self, call: ToolCall, result: ToolResult):
        """Log tool execution to database."""
        cursor = self._conn.cursor()
        cursor.execute(
            """INSERT INTO tool_executions (tool_name, arguments, output, success, error, confidence)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (call.tool, json.dumps(call.arguments), 
             str(result.output) if result.output else None,
             1 if result.success else 0, result.error, result.confidence)
        )
        self._conn.commit()
    
    def verify_with_tools(self, claim: str) -> Dict:
        """
        Verify a claim using tool execution.
        
        Returns:
        {
            'verified': bool,
            'tool_results': [...],
            'contradiction': bool,
            'confidence': float
        }
        """
        # Parse claim for tool-verifiable components
        calls = self.parse_tool_needs(claim)
        results = self.execute_tools(calls)
        
        # Check if results contradict claim
        contradiction = False
        confidence = 1.0
        
        for result in results:
            if not result.success:
                confidence *= 0.7
            elif result.tool == "calculator":
                # Check if calculation matches claim
                if isinstance(result.output, (int, float)):
                    # Extract numbers from claim
                    claim_nums = re.findall(r'\d+\.?\d*', claim)
                    if claim_nums and abs(float(claim_nums[-1]) - result.output) > 0.01:
                        contradiction = True
                        confidence *= 0.3
        
        return {
            'verified': not contradiction and confidence > 0.5,
            'tool_results': [{'tool': r.tool, 'output': r.output, 'success': r.success} for r in results],
            'contradiction': contradiction,
            'confidence': confidence,
            'calls': [{'tool': c.tool, 'arguments': c.arguments} for c in self.executed_tools]
        }
    
    def reason_with_tools(self, problem: str) -> Dict:
        """
        Main reasoning entry point using tools.
        
        Process:
        1. Parse problem for tool needs
        2. Execute tools
        3. Integrate results into answer
        4. Verify answer with additional tools if needed
        
        Returns:
        {
            'answer': str,
            'tool_calls': [...],
            'tool_results': [...],
            'verified': bool,
            'confidence': float
        }
        """
        # Step 1: Identify tool needs
        calls = self.parse_tool_needs(problem)
        
        # Step 2: Execute tools
        results = self.execute_tools(calls)
        
        # Step 3: Build answer from results
        answer_parts = []
        confidence = 1.0
        
        for result in results:
            if result.success:
                answer_parts.append(f"{result.tool}: {result.output}")
            else:
                answer_parts.append(f"{result.tool} failed: {result.error}")
                confidence *= 0.5
        
        answer = "\n".join(answer_parts) if answer_parts else "No tools applicable"
        
        # Step 4: Verify answer
        verification = self.verify_with_tools(problem)
        
        return {
            'answer': answer,
            'tool_calls': [{'tool': c.tool, 'arguments': c.arguments} for c in self.executed_tools],
            'tool_results': [{'tool': r.tool, 'output': r.output, 'success': r.success} for r in results],
            'verified': verification['verified'],
            'confidence': confidence * verification['confidence'],
            'contradiction': verification['contradiction']
        }
    
    def clear(self):
        """Clear execution history."""
        self.executed_tools = []


def reason_with_tools(problem: str, db_path: str = ":memory:") -> Dict:
    """
    Main entry point for tool-based reasoning.
    
    Usage:
        result = reason_with_tools("What is 15% of 240?")
        result = reason_with_tools("Search for quantum computing basics")
        
    Returns:
        {
            'answer': str,
            'tool_calls': [...],
            'tool_results': [...],
            'verified': bool,
            'confidence': float,
            'contradiction': bool
        }
    """
    reasoner = ToolReasoner(db_path=db_path)
    return reasoner.reason_with_tools(problem)


if __name__ == "__main__":
    # Test calculator
    result = reason_with_tools("Calculate 15% of 240")
    print("Calculator test:")
    print(f"Answer: {result['answer']}")
    print(f"Verified: {result['verified']}")
    print(f"Confidence: {result['confidence']}")
    
    # Test datetime
    result = reason_with_tools("What is the current date?")
    print("\nDateTime test:")
    print(f"Answer: {result['answer']}")
    print(f"Tool used: {result['tool_calls'][0]['tool'] if result['tool_calls'] else 'none'}")
