"""TI Clang linkinfo analysis package."""

from .analyzer import LinkInfoAnalyzer
from .linkinfo_parser import (
    InputFile,
    LinkInfoParser,
    LogicalGroup,
    MemoryArea,
    MemoryUsage,
    ObjectComponent,
)
from .linkinfo_graph import LinkInfoGraphBuilder

__all__ = [
    "LinkInfoAnalyzer",
    "InputFile",
    "LinkInfoParser",
    "LogicalGroup",
    "MemoryArea",
    "MemoryUsage",
    "ObjectComponent",
    "LinkInfoGraphBuilder",
]

__version__ = "0.1.0"
