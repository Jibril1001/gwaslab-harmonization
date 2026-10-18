"""Reusable GWASLab harmonization workflow.

Public API
----------
- :func:`load_config` / :func:`validate_config` — parse and validate the
  YAML configuration.
- :func:`run_harmonization` / :func:`harmonize_from_config` — execute the
  workflow.
- :func:`write_run_manifest` / :func:`format_config_summary` — record what ran.
"""

from __future__ import annotations

from .pipeline import (
    HarmonizationConfig,
    RunResult,
    build_harmonize_kwargs,
    build_sumstats_kwargs,
    harmonize_from_config,
    run_harmonization,
)
from .reporting import format_config_summary, get_version_info, write_run_manifest
from .validation import (
    ConfigError,
    HarmonizationSettings,
    InputConfig,
    OutputConfig,
    ReferenceConfig,
    load_config,
    validate_config,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "ConfigError",
    "HarmonizationConfig",
    "HarmonizationSettings",
    "InputConfig",
    "OutputConfig",
    "ReferenceConfig",
    "RunResult",
    "build_harmonize_kwargs",
    "build_sumstats_kwargs",
    "format_config_summary",
    "get_version_info",
    "harmonize_from_config",
    "load_config",
    "run_harmonization",
    "validate_config",
    "write_run_manifest",
]
