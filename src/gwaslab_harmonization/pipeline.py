"""Reusable GWASLab harmonization workflow.

The pipeline is deliberately thin: it maps validated configuration fields onto
the documented GWASLab API and nothing else, so a reader can see exactly which
GWASLab operations run and with which parameters. GWASLab itself is imported
lazily and can be injected for testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .validation import HarmonizationConfig, load_config

__all__ = [
    "RunResult",
    "build_sumstats_kwargs",
    "build_harmonize_kwargs",
    "run_harmonization",
    "harmonize_from_config",
]


@dataclass
class RunResult:
    """A compact record of what the workflow did."""

    input_path: Path
    output_path: Path | None
    genome_build: str
    gwaslab_build_code: str
    n_variants_in: int | None
    n_variants_out: int | None
    references: dict[str, str | None]
    saved: bool
    warnings: list[str] = field(default_factory=list)

    @property
    def variant_delta(self) -> int | None:
        if self.n_variants_in is None or self.n_variants_out is None:
            return None
        return self.n_variants_out - self.n_variants_in


def _import_gwaslab() -> Any:
    try:
        import gwaslab  # noqa: F401
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "GWASLab is required to run harmonization but is not installed. "
            "Install it with 'pip install gwaslab' (see README 'Installation')."
        ) from exc
    return gwaslab


def build_sumstats_kwargs(config: HarmonizationConfig) -> dict[str, Any]:
    """Arguments passed to the ``gl.Sumstats`` constructor."""

    kwargs: dict[str, Any] = {
        "fmt": config.input.format,
        "build": config.gwaslab_build_code,
    }
    if config.input.other_columns:
        kwargs["other"] = list(config.input.other_columns)
    return kwargs


def build_harmonize_kwargs(config: HarmonizationConfig) -> dict[str, Any]:
    """Arguments passed to ``Sumstats.harmonize``.

    Only reference resources that were actually configured are included, so an
    unset (``null``) resource is never silently replaced by another.
    """

    settings = config.harmonization
    reference = config.reference

    kwargs: dict[str, Any] = {
        "basic_check": settings.basic_check,
        "threads": settings.threads,
        "remove": settings.remove,
        "maf_threshold": settings.maf_threshold,
        "ref_maf_threshold": settings.ref_maf_threshold,
    }
    if reference.fasta_path is not None:
        kwargs["ref_seq"] = str(reference.fasta_path)
    if reference.inference_vcf_path is not None:
        kwargs["ref_infer"] = str(reference.inference_vcf_path)
        kwargs["ref_alt_freq"] = reference.allele_frequency_field
    if reference.rsid_tsv_path is not None:
        kwargs["ref_rsid_tsv"] = str(reference.rsid_tsv_path)
    if reference.rsid_vcf_path is not None:
        kwargs["ref_rsid_vcf"] = str(reference.rsid_vcf_path)
    return kwargs


def _reference_summary(config: HarmonizationConfig) -> dict[str, str | None]:
    reference = config.reference
    return {
        "genome_build": reference.genome_build,
        "fasta_path": str(reference.fasta_path) if reference.fasta_path else None,
        "inference_vcf_path": (
            str(reference.inference_vcf_path) if reference.inference_vcf_path else None
        ),
        "allele_frequency_field": reference.allele_frequency_field,
        "rsid_tsv_path": str(reference.rsid_tsv_path) if reference.rsid_tsv_path else None,
        "rsid_vcf_path": str(reference.rsid_vcf_path) if reference.rsid_vcf_path else None,
    }


def run_harmonization(
    config: HarmonizationConfig,
    *,
    gl: Any | None = None,
    save: bool = True,
) -> RunResult:
    """Run the verified GWASLab harmonization workflow for ``config``.

    Parameters
    ----------
    config:
        A validated :class:`~gwaslab_harmonization.validation.HarmonizationConfig`.
    gl:
        The GWASLab module to use. Defaults to importing ``gwaslab``. Injection
        exists so control flow and argument mapping can be tested without the
        heavy GWASLab/``pysam`` dependency or reference data.
    save:
        When ``True`` (default) the harmonized table is written to
        ``config.output.path`` via ``Sumstats.to_format``.

    Returns
    -------
    RunResult
    """

    gwaslab = gl if gl is not None else _import_gwaslab()

    sumstats = gwaslab.Sumstats(str(config.input.path), **build_sumstats_kwargs(config))
    n_variants_in = len(sumstats.data)

    # --- the actual harmonization --------------------------------------
    sumstats.harmonize(**build_harmonize_kwargs(config))

    n_variants_out = len(sumstats.data)

    output_path: Path | None = None
    if save:
        config.output.directory.mkdir(parents=True, exist_ok=True)
        output_path = config.output.path
        sumstats.to_format(str(output_path), build=config.gwaslab_build_code)

    return RunResult(
        input_path=config.input.path,
        output_path=output_path,
        genome_build=config.reference.genome_build,
        gwaslab_build_code=config.gwaslab_build_code,
        n_variants_in=n_variants_in,
        n_variants_out=n_variants_out,
        references=_reference_summary(config),
        saved=output_path is not None,
        warnings=list(config.warnings),
    )


def harmonize_from_config(
    config_path: str | Path,
    *,
    base_dir: str | Path | None = None,
    gl: Any | None = None,
    save: bool = True,
) -> RunResult:
    """Load a configuration file, validate it and run the workflow."""

    config = load_config(config_path, base_dir=base_dir)
    return run_harmonization(config, gl=gl, save=save)
