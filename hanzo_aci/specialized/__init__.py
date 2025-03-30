"""Specialized modules for Hanzo ACI.

This package contains specialized modules for specific capabilities like
vector databases, symbolic reasoning, and full-text search. These modules
can be installed as optional dependencies.
"""

# Try to import the specialized modules if available
try:
    from hanzo_aci.specialized.vector_search import VectorSearchInterface, vector_search
except ImportError:
    # Vector database dependencies not available
    pass

try:
    from hanzo_aci.specialized.symbolic_reasoning import SymbolicReasoningInterface, symbolic_reasoning
except ImportError:
    # Symbolic reasoning dependencies not available
    pass

# Export the available modules
__all__ = []

# Check which modules are available and export them
try:
    VectorSearchInterface
    __all__.extend(["VectorSearchInterface", "vector_search"])
except NameError:
    pass

try:
    SymbolicReasoningInterface
    __all__.extend(["SymbolicReasoningInterface", "symbolic_reasoning"])
except NameError:
    pass
