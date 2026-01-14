"""
Text similarity algorithms - Python implementations.

This package provides multiple implementations of text similarity algorithms:
- pure_python: Baseline pure Python implementation
- numpy_impl: NumPy-accelerated implementation
- opensource_libs: Wrappers for popular open-source libraries
"""

from . import pure_python
from . import numpy_impl
from . import opensource_libs

__all__ = ['pure_python', 'numpy_impl', 'opensource_libs']
