# Workflow

This document explains what the harmonization workflow does, step by step, and
which GWASLab operation each step maps to.

## Overview

The workflow is a straight line from configuration to result:

```
config/harmonization.yaml
        │
        ▼
  load_config()                  (validation.py)
   - parse YAML
   - resolve paths against base_dir
   - enforce coherence rules (see below)
        │
        ▼
  run_harmonization()            (pipeline.py)
        │
        ├─ gl.Sumstats(input, fmt=…, build=…)        ← read + normalize
        │
        ├─ Sumstats.harmonize(…)                     ← the actual harmonization
        │      basic_check, threads, remove,
        │      ref_seq, ref_infer, ref_alt_freq,
        │      ref_rsid_tsv, ref_rsid_vcf,
        │      maf_threshold, ref_maf_threshold
        │
        └─ Sumstats.to_format(output, build=…)       ← write result
        │
        ▼
  RunResult + optional run_manifest.json          (reporting.py)
```

## Step 1 — Read and normalize the input

`gl.Sumstats(path, fmt=..., build=...)` parses the input file into GWASLab's
internal standardized representation. `fmt` selects the input dialect; `build`
is the two-digit GWASLab genome-build code (`19` for hg19, `38` for hg38). Any
columns listed under `input.other_columns` are carried through via GWASLab's
`other=` argument so they survive to the output (the toy dataset uses this for
the `NOTE` column).

## Step 2 — Harmonize

`Sumstats.harmonize(...)` performs the harmonization. Depending on which
reference resources are configured, different checks are enabled:

| Config field | GWASLab argument | Effect |
| --- | --- | --- |
| `harmonization.basic_check` | `basic_check` | Standardization/QC checks (allele coding, statistics sanity, rsID, etc.). |
| `harmonization.threads` | `threads` | Worker threads (the old `n_cores` name is gone in 4.x). |
| `harmonization.remove` | `remove` | Drop variants flagged as problematic. |
| `harmonization.maf_threshold` | `maf_threshold` | MAF cutoff for palindromic-SNP strand inference. |
| `harmonization.ref_maf_threshold` | `ref_maf_threshold` | MAF cutoff applied to reference frequencies. |
| `reference.fasta_path` | `ref_seq` | Reference FASTA; enables REF/ALT and strand verification. |
| `reference.inference_vcf_path` | `ref_infer` | Reference VCF/BCF; enables strand inference from allele frequencies. |
| `reference.allele_frequency_field` | `ref_alt_freq` | INFO field holding ALT allele frequency in `ref_infer`. |
| `reference.rsid_tsv_path` | `ref_rsid_tsv` | rsID lookup TSV. |
| `reference.rsid_vcf_path` | `ref_rsid_vcf` | rsID lookup VCF. |

Only configured resources are forwarded. This matters: an unset resource is
never silently replaced, so **if you set no reference resources, the run is
standardization/basic-check only and is *not* true reference-based
harmonization.** The validator emits a warning in that case.

## Step 3 — Write the output and the manifest

`Sumstats.to_format(path, build=...)` writes the harmonized table in the format
requested by `output.save_format`. Separately, `write_run_manifest()` records a
JSON manifest capturing the input, reference resources, the exact GWASLab
arguments used, and software versions — see `docs/results.md`.

## Validation rules enforced *before* any GWASLab call

`validation.py` refuses to run when the configuration is incoherent, so that
mistakes surface as clear errors rather than silently degraded science:

1. All required sections (`input`, `reference`, `harmonization`, `output`) must
   be present, and no unknown top-level sections are allowed.
2. `input.path` must exist and be a file.
3. `reference.genome_build` must be a supported build.
4. Any configured reference resource path must exist.
5. `reference.allele_frequency_field` and `reference.inference_vcf_path` must be
   set together (both or neither).
6. Numeric ranges: `threads >= 1`; `0 < maf_threshold, ref_maf_threshold <= 0.5`.
7. Booleans must be real booleans (no `"yes"`/`"true"` strings).
8. `output.filename` must be a bare file name (no directory separators), and
   the resolved output path must not equal the input path (never overwrite
   input).

## Status codes

After harmonization, GWASLab stores a 7-digit status code in the `STATUS`
column (where `1` = the corresponding check passed). The workflow keeps this
column in the output so you can audit each variant. See
`docs/results.md` for how to read the code, and the official GWASLab
documentation for the canonical definition.
