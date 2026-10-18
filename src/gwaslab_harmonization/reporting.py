"""Human-readable and machine-readable reporting for harmonization runs.

Producing a manifest turns an otherwise ephemeral notebook run into something
reproducible: the exact input, reference resources, GWASLab parameters and
software versions are recorded next to the results.
"""

from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .pipeline import RunResult, build_harmonize_kwargs, build_sumstats_kwargs
from .validation import HarmonizationConfig

__all__ = [
    "get_version_info",
    "format_config_summary",
    "write_run_manifest",
]


def get_version_info(gl: Any | None = None) -> dict[str, str]:
    """Collect versions of the interpreter and relevant packages."""

    info = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
    }

    try:  # GWASLab is optional at report time.
        import gwaslab

        info["gwaslab"] = getattr(gwaslab, "__version__", "unknown")
    except ImportError:
        info["gwaslab"] = "not installed"

    if gl is not None:
        info["gwaslab"] = getattr(gl, "__version__", info.get("gwaslab", "unknown"))

    return info


def format_config_summary(config: HarmonizationConfig) -> str:
    """Return a multi-line, human-readable summary of a validated config."""

    reference = config.reference
    input_cfg = config.input
    output_cfg = config.output
    settings = config.harmonization

    lines = [
        "Harmonization configuration",
        "===========================",
        f"  source config     : {config.source_path}",
        f"  base directory    : {config.base_dir}",
        "",
        "Input",
        f"  path              : {input_cfg.path}",
        f"  format            : {input_cfg.format}",
        f"  carried columns   : {', '.join(input_cfg.other_columns) if input_cfg.other_columns else '(none)'}",
        "",
        "Reference",
        f"  genome build      : {reference.genome_build} (GWASLab code {config.gwaslab_build_code})",
        f"  FASTA (ref_seq)   : {reference.fasta_path or '(not set)'}",
        f"  inference VCF     : {reference.inference_vcf_path or '(not set)'}",
        f"  allele freq field : {reference.allele_frequency_field or '(not set)'}",
        f"  rsID TSV          : {reference.rsid_tsv_path or '(not set)'}",
        f"  rsID VCF          : {reference.rsid_vcf_path or '(not set)'}",
        "",
        "Harmonization settings",
        f"  basic_check       : {settings.basic_check}",
        f"  threads           : {settings.threads}",
        f"  remove            : {settings.remove}",
        f"  maf_threshold     : {settings.maf_threshold}",
        f"  ref_maf_threshold : {settings.ref_maf_threshold}",
        "",
        "Output",
        f"  directory         : {output_cfg.directory}",
        f"  filename          : {output_cfg.filename}",
        f"  save format       : {output_cfg.save_format}",
    ]

    if config.warnings:
        lines += ["", "Warnings"]
        lines += [f"  ! {warning}" for warning in config.warnings]

    return "\n".join(lines)


def write_run_manifest(
    result: RunResult,
    config: HarmonizationConfig,
    *,
    manifest_path: str | Path,
    gl: Any | None = None,
) -> Path:
    """Write a JSON manifest describing the run. Returns the written path."""

    manifest_path = Path(manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "versions": get_version_info(gl),
        "input": {
            "path": str(result.input_path),
            "format": config.input.format,
            "other_columns": list(config.input.other_columns),
            "n_variants": result.n_variants_in,
        },
        "reference": result.references,
        "harmonization_settings": config.harmonization.__dict__,
        "gwaslab_sumstats_kwargs": build_sumstats_kwargs(config),
        "gwaslab_harmonize_kwargs": build_harmonize_kwargs(config),
        "output": {
            "path": str(result.output_path) if result.output_path else None,
            "saved": result.saved,
            "n_variants": result.n_variants_out,
            "variant_delta": result.variant_delta,
        },
        "warnings": result.warnings,
    }

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest_path
