#!/usr/bin/env python
"""Command-line entry point for the GWASLab harmonization workflow.

Examples
--------
Run with the bundled default configuration::

    python scripts/run_harmonization.py

Use a custom configuration and write a run manifest::

    python scripts/run_harmonization.py \
        --config config/harmonization.yaml \
        --manifest results/run_manifest.json

Validate the configuration without running anything::

    python scripts/run_harmonization.py --check-only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running the script directly from a source checkout without installation.
_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from gwaslab_harmonization import (  # noqa: E402
    ConfigError,
    format_config_summary,
    load_config,
    run_harmonization,
    write_run_manifest,
)

_DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "harmonization.yaml"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_harmonization",
        description="Harmonize GWAS summary statistics against reference resources with GWASLab.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=_DEFAULT_CONFIG,
        help="Path to the YAML configuration file (default: config/harmonization.yaml).",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=None,
        help="Directory against which relative config paths are resolved (default: current directory).",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Run harmonization but do not write the output table.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Optional path to write a JSON run manifest.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate the configuration and exit without running harmonization.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        config = load_config(args.config, base_dir=args.base_dir)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    print(format_config_summary(config))

    if args.check_only:
        print("\nConfiguration is valid. Exiting (--check-only).")
        return 0

    # GWASLab is imported only when actually running, so --check-only works
    # without the heavy dependency installed.
    try:
        result = run_harmonization(config, save=not args.no_save)
    except ImportError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 3

    print("\nRun summary")
    print("===========")
    print(f"  variants in  : {result.n_variants_in}")
    print(f"  variants out : {result.n_variants_out}")
    print(f"  delta        : {result.variant_delta}")
    if result.output_path:
        print(f"  output       : {result.output_path}")
    else:
        print("  output       : (not saved)")

    if args.manifest is not None:
        manifest_path = write_run_manifest(result, config, manifest_path=args.manifest)
        print(f"  manifest     : {manifest_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
