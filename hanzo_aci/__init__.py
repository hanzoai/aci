"""Hanzo ACI (Abstract Computer Interface).

This package provides a consistent interface for AI assistants to interact with 
computer systems through various backends like MCP, Claude Code, and native implementations.
"""

from hanzo_aci.interface import ComputerInterface
from hanzo_aci.version import __version__

# Create a default singleton instance
computer = ComputerInterface()

# Export the main interface
__all__ = ["ComputerInterface", "computer", "__version__"]
