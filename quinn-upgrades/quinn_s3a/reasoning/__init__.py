"""
Quinn Enhanced Reasoning Engine v2.0

5 Advanced Reasoning Capabilities:
1. Neural-Symbolic Integration - LLM + symbolic logic (Prolog/Datalog)
2. External Tool Reasoning - Reason BY USING tools
3. Multi-Model Verification - Cross-model verification
4. Iterative Refinement - Multiple refinement passes
5. Uncertainty Calibration - Know when you don't know
"""

from .neural_symbolic import (
    NeuralSymbolicReasoner,
    reason_with_symbolic,
    Fact,
    Rule,
    LogicFormalism
)

from .tool_reasoning import (
    ToolReasoner,
    reason_with_tools,
    ToolCall,
    ToolResult,
    ToolType
)

from .multi_model_verification import (
    MultiModelVerifier,
    verify_with_multi_model,
    ModelResponse,
    VerificationResult,
    ModelRole
)

from .iterative_refinement import (
    IterativeRefiner,
    refine_iteratively,
    RefinementPass,
    RefinementResult
)

from .uncertainty_calibration import (
    UncertaintyCalibrator,
    calibrate_uncertainty,
    CalibratedResponse,
    UncertaintyType,
    UncertaintySignal
)

from .enhanced_engine import (
    EnhancedReasoningEngine,
    reason_enhanced,
    EnhancedReasoningResult,
    ReasoningStrategy
)

__version__ = "2.0.0"
__author__ = "Quinn AI Agent"

__all__ = [
    # Main engine
    'EnhancedReasoningEngine',
    'reason_enhanced',
    'EnhancedReasoningResult',
    'ReasoningStrategy',
    
    # Neural-symbolic
    'NeuralSymbolicReasoner',
    'reason_with_symbolic',
    'Fact',
    'Rule',
    'LogicFormalism',
    
    # Tool reasoning
    'ToolReasoner',
    'reason_with_tools',
    'ToolCall',
    'ToolResult',
    'ToolType',
    
    # Multi-model verification
    'MultiModelVerifier',
    'verify_with_multi_model',
    'ModelResponse',
    'VerificationResult',
    'ModelRole',
    
    # Iterative refinement
    'IterativeRefiner',
    'refine_iteratively',
    'RefinementPass',
    'RefinementResult',
    
    # Uncertainty calibration
    'UncertaintyCalibrator',
    'calibrate_uncertainty',
    'CalibratedResponse',
    'UncertaintyType',
    'UncertaintySignal',
]
