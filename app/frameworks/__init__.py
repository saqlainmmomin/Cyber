"""
Multi-framework compliance assessment engine.

Provides a generic framework abstraction layer that supports any compliance
standard (DPDPA, ISO 27001, GDPR, HIPAA, NIST CSF, PCI-DSS, etc.).
"""

from app.frameworks.registry import FrameworkRegistry

__all__ = ["FrameworkRegistry"]
