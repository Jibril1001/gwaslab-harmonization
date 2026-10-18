"""Configuration loading and validation for the GWASLab harmonization workflow.

This module is intentionally independent of GWASLab. It only checks that a
configuration file is well-formed, that referenced project files exist, and
that the combination of options is coherent. It does **not** attempt to
re-implement any of GWASLab's scientific validation.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

__all__ = [
    "ConfigError",
    "InputConfig",
    "ReferenceConfig",
    "HarmonizationSettings",
    "OutputConfig",
    "HarmonizationConfig",
    "load_config",
    "validate_config",
    "GWASLAB_BUILD_CODES",
]

# GWASLab encodes genome build as a two-digit code. We accept common build
# aliases in the config and map them onto those codes.
GWASLAB_BUILD_CODES: dict[str, str] = {
    "hg19": "19",
    "grch37": "19",
    "19": "19",
    "hg38": "38",
    "grch38": "38",
    "38": "38",
}

_REQUIRED_SECTIONS = ("input", "reference", "harmonization", "output")


class ConfigError(ValueError):
    """Raised when a harmonization configuration is missing or invalid."""


@dataclass(frozen=True)
class InputConfig:
    """Input summary-statistics file settings."""

    path: Path
    format: str = "gwaslab"
    other_columns: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReferenceConfig:
    """Reference-resource settings.

    ``fasta_path`` maps to GWASLab ``ref_seq``; ``inference_vcf_path`` to
    ``ref_infer``; ``rsid_tsv_path`` / ``rsid_vcf_path`` to ``ref_rsid_tsv`` /
    ``ref_rsid_vcf``; ``allele_frequency_field`` to ``ref_alt_freq``.
    """

    genome_build: str
    fasta_path: Path | None = None
    inference_vcf_path: Path | None = None
    rsid_tsv_path: Path | None = None
    rsid_vcf_path: Path | None = None
    allele_frequency_field: str | None = None


@dataclass(frozen=True)
class HarmonizationSettings:
    """Options forwarded to ``Sumstats.harmonize``."""

    basic_check: bool = True
    threads: int = 1
    remove: bool = False
    maf_threshold: float = 0.40
    ref_maf_threshold: float = 0.40


@dataclass(frozen=True)
class OutputConfig:
    """Output location and export format."""

    directory: Path
    filename: str = "harmonized_sumstats.tsv"
    save_format: str = "gwaslab"

    @property
    def path(self) -> Path:
        return self.directory / self.filename


@dataclass(frozen=True)
class HarmonizationConfig:
    """A fully validated, path-resolved harmonization configuration."""

    input: InputConfig
    reference: ReferenceConfig
    harmonization: HarmonizationSettings
    output: OutputConfig
    source_path: Path
    base_dir: Path
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def gwaslab_build_code(self) -> str:
        return GWASLAB_BUILD_CODES[self.reference.genome_build]


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------
def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ConfigError(f"Section '{name}' must be a mapping, got {type(value).__name__}.")
    return value


def _resolve_path(value: str, base_dir: Path) -> Path:
    """Resolve a config path: relative paths are joined to ``base_dir``."""
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    return candidate


def _require_str(section: Mapping[str, Any], key: str, section_name: str) -> str:
    if key not in section:
        raise ConfigError(f"Missing required key '{section_name}.{key}'.")
    value = section[key]
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"'{section_name}.{key}' must be a non-empty string.")
    return value


def _optional_str(section: Mapping[str, Any], key: str, section_name: str) -> str | None:
    value = section.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"'{section_name}.{key}' must be a non-empty string or null.")
    return value


def _optional_path(value: Any, key: str, section_name: str, base_dir: Path) -> Path | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"'{section_name}.{key}' must be a file path string or null.")
    return _resolve_path(value, base_dir)


def _require_bool(section: Mapping[str, Any], key: str, section_name: str, default: bool) -> bool:
    value = section.get(key, default)
    if not isinstance(value, bool):
        raise ConfigError(f"'{section_name}.{key}' must be a boolean, got {type(value).__name__}.")
    return value


def _require_int(
    section: Mapping[str, Any], key: str, section_name: str, default: int, minimum: int = 1
) -> int:
    value = section.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"'{section_name}.{key}' must be an integer, got {type(value).__name__}.")
    if value < minimum:
        raise ConfigError(f"'{section_name}.{key}' must be >= {minimum}, got {value}.")
    return value


def _require_float(
    section: Mapping[str, Any],
    key: str,
    section_name: str,
    default: float,
    *,
    low: float,
    high: float,
) -> float:
    value = section.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"'{section_name}.{key}' must be a number, got {type(value).__name__}.")
    value = float(value)
    if not low < value <= high:
        raise ConfigError(f"'{section_name}.{key}' must be in ({low}, {high}], got {value}.")
    return value


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def load_config(config_path: str | Path, base_dir: str | Path | None = None) -> HarmonizationConfig:
    """Load and validate a YAML configuration file.

    Parameters
    ----------
    config_path:
        Path to the YAML configuration file.
    base_dir:
        Directory against which relative paths are resolved. Defaults to the
        current working directory, which is expected to be the repository root.

    Raises
    ------
    ConfigError
        If the file is missing, not valid YAML, or fails validation.
    """

    resolved_config = Path(config_path).expanduser()
    if not resolved_config.is_file():
        raise ConfigError(f"Configuration file not found: {resolved_config}")

    try:
        raw = yaml.safe_load(resolved_config.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:  # pragma: no cover - exercised indirectly
        raise ConfigError(f"Could not parse YAML configuration {resolved_config}: {exc}") from exc

    if raw is None:
        raise ConfigError(f"Configuration file is empty: {resolved_config}")

    base = Path(base_dir).expanduser().resolve() if base_dir is not None else Path.cwd()
    return validate_config(raw, source_path=resolved_config, base_dir=base)


def validate_config(
    config: Mapping[str, Any],
    *,
    source_path: str | Path = "<memory>",
    base_dir: str | Path | None = None,
) -> HarmonizationConfig:
    """Validate a configuration mapping and return a resolved config object."""

    if not isinstance(config, Mapping):
        raise ConfigError("Top-level configuration must be a mapping.")

    missing = [name for name in _REQUIRED_SECTIONS if name not in config]
    if missing:
        raise ConfigError(f"Missing required section(s): {', '.join(missing)}.")

    unknown = [name for name in config if name not in _REQUIRED_SECTIONS]
    if unknown:
        raise ConfigError(f"Unknown top-level section(s): {', '.join(sorted(unknown))}.")

    base = Path(base_dir).expanduser().resolve() if base_dir is not None else Path.cwd()
    warnings: list[str] = []

    # ---- input -----------------------------------------------------------
    input_section = _require_mapping(config["input"], "input")
    input_path = _resolve_path(_require_str(input_section, "path", "input"), base)
    if not input_path.is_file():
        raise ConfigError(f"Input summary-statistics file not found: {input_path}")

    input_format = _optional_str(input_section, "format", "input") or "gwaslab"

    other_columns_raw = input_section.get("other_columns", [])
    if other_columns_raw is None:
        other_columns_raw = []
    if not isinstance(other_columns_raw, (list, tuple)) or not all(
        isinstance(col, str) and col.strip() for col in other_columns_raw
    ):
        raise ConfigError("'input.other_columns' must be a list of non-empty strings.")
    other_columns = tuple(other_columns_raw)

    # ---- reference -------------------------------------------------------
    reference_section = _require_mapping(config["reference"], "reference")
    genome_build_raw = _require_str(reference_section, "genome_build", "reference")
    if genome_build_raw.lower() not in GWASLAB_BUILD_CODES:
        allowed = ", ".join(sorted(set(GWASLAB_BUILD_CODES) - {"19", "38"}))
        raise ConfigError(
            f"Unsupported reference.genome_build '{genome_build_raw}'. Supported: {allowed}."
        )
    genome_build = genome_build_raw.lower()

    fasta_path = _optional_path(
        reference_section.get("fasta_path"), "fasta_path", "reference", base
    )
    inference_vcf_path = _optional_path(
        reference_section.get("inference_vcf_path"), "inference_vcf_path", "reference", base
    )
    rsid_tsv_path = _optional_path(
        reference_section.get("rsid_tsv_path"), "rsid_tsv_path", "reference", base
    )
    rsid_vcf_path = _optional_path(
        reference_section.get("rsid_vcf_path"), "rsid_vcf_path", "reference", base
    )
    allele_frequency_field = _optional_str(reference_section, "allele_frequency_field", "reference")

    for label, configured in (
        ("reference.fasta_path", fasta_path),
        ("reference.inference_vcf_path", inference_vcf_path),
        ("reference.rsid_tsv_path", rsid_tsv_path),
        ("reference.rsid_vcf_path", rsid_vcf_path),
    ):
        if configured is not None and not configured.is_file():
            raise ConfigError(f"Configured {label} does not exist: {configured}")

    # Cross-field coherence: allele-frequency field and inference VCF are used
    # together for strand inference. Do not silently ignore one of them.
    if inference_vcf_path is not None and allele_frequency_field is None:
        raise ConfigError(
            "'reference.allele_frequency_field' is required when "
            "'reference.inference_vcf_path' is set (needed for strand inference)."
        )
    if inference_vcf_path is None and allele_frequency_field is not None:
        raise ConfigError(
            "'reference.allele_frequency_field' is set but 'reference.inference_vcf_path' "
            "is not; remove the field or configure the inference VCF."
        )
    if fasta_path is None and inference_vcf_path is None:
        warnings.append(
            "No reference FASTA or inference VCF configured: harmonize() will run "
            "standardization/basic checks only, not reference-based harmonization."
        )

    # ---- harmonization ---------------------------------------------------
    harmonization_section = _require_mapping(config["harmonization"], "harmonization")
    settings = HarmonizationSettings(
        basic_check=_require_bool(harmonization_section, "basic_check", "harmonization", True),
        threads=_require_int(harmonization_section, "threads", "harmonization", 1),
        remove=_require_bool(harmonization_section, "remove", "harmonization", False),
        maf_threshold=_require_float(
            harmonization_section, "maf_threshold", "harmonization", 0.40, low=0.0, high=0.5
        ),
        ref_maf_threshold=_require_float(
            harmonization_section, "ref_maf_threshold", "harmonization", 0.40, low=0.0, high=0.5
        ),
    )

    # ---- output ----------------------------------------------------------
    output_section = _require_mapping(config["output"], "output")
    output_dir_raw = _optional_str(output_section, "directory", "output") or "results"
    output_directory = _resolve_path(output_dir_raw, base)
    filename = _optional_str(output_section, "filename", "output") or "harmonized_sumstats.tsv"
    if any(sep in filename for sep in ("/", "\\")):
        raise ConfigError(f"'output.filename' must not contain a directory separator: {filename!r}")
    save_format = _optional_str(output_section, "save_format", "output") or "gwaslab"

    output = OutputConfig(directory=output_directory, filename=filename, save_format=save_format)

    # Never allow the workflow to overwrite its own input (data-integrity rule).
    if output.path.resolve() == input_path.resolve():
        raise ConfigError(
            f"Output path equals the input path ({input_path}); refusing to overwrite input."
        )

    return HarmonizationConfig(
        input=InputConfig(path=input_path, format=input_format, other_columns=other_columns),
        reference=ReferenceConfig(
            genome_build=genome_build,
            fasta_path=fasta_path,
            inference_vcf_path=inference_vcf_path,
            rsid_tsv_path=rsid_tsv_path,
            rsid_vcf_path=rsid_vcf_path,
            allele_frequency_field=allele_frequency_field,
        ),
        harmonization=settings,
        output=output,
        source_path=Path(source_path),
        base_dir=base,
        warnings=tuple(warnings),
    )
