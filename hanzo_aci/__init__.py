"""Hanzo ACI (Abstract Computer Interface).

This package provides a foundational library for computer interaction capabilities,
serving as the core layer for tools like Hanzo MCP and Hanzo Code.
"""

from hanzo_aci.interface import ComputerInterface
from hanzo_aci.tools.native import NativeComputerInterface
from hanzo_aci.version import __version__

# Create a default instance using the native implementation
computer = NativeComputerInterface()

# Export the main components
__all__ = ["ComputerInterface", "ConcreteComputerInterface", "NativeComputerInterface", "computer", "__version__"]
