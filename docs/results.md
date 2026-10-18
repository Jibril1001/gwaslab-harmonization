# Results

What the workflow produces and how to read it.

## Outputs

For a run configured by `config/harmonization.yaml`:

| Artifact | Location | Description |
| --- | --- | --- |
| Harmonized table | `output.directory / output.filename` (default `results/harmonized_sumstats.tsv`) | Summary statistics after harmonization, including GWASLab's `STATUS` column. |
| Run manifest | wherever `--manifest` points (optional) | JSON record of inputs, reference resources, GWASLab arguments and versions. |

Both are generated; `results/*` is git-ignored except for a placeholder, so no
generated science is committed.

## Reading the `STATUS` column

GWASLab stores a 7-digit status code per variant. Each digit corresponds to one
check; `1` means the check passed. The checks, in order, are:

| Position | Meaning |
| --- | --- |
| 1 | Build — whether the variant's build matched the requested build. |
| 2 | rsID — whether the rsID was consistent / could be matched. |
| 3 | CHR & POS — whether chromosome and position were consistent. |
| 4 | Effect allele vs non-effect allele — whether the allele pair was valid. |
| 5 | REF & NEA alignment — whether the non-effect allele matched the reference. |
| 6 | Palindromic / strand — whether strand could be resolved against the reference. |
| 7 | Indel — whether the variant was handled as an indel. |

The canonical definitions live in the official GWASLab documentation
("Status code"). Use `Sumstats.lookup_status()` to translate codes, and
`Sumstats.summary()` for aggregate counts.

## The run manifest

Example structure:

```json
{
  "generated_at_utc": "…",
  "versions": {"python": "…", "platform": "…", "gwaslab": "4.2.3"},
  "input": {"path": "…", "format": "gwaslab", "other_columns": ["NOTE"], "n_variants": 15},
  "reference": {"genome_build": "hg19", "fasta_path": null, "inference_vcf_path": null,
                 "allele_frequency_field": null, "rsid_tsv_path": null, "rsid_vcf_path": null},
  "harmonization_settings": {"basic_check": true, "threads": 1, "remove": false,
                             "maf_threshold": 0.4, "ref_maf_threshold": 0.4},
  "gwaslab_sumstats_kwargs": {"fmt": "gwaslab", "build": "19", "other": ["NOTE"]},
  "gwaslab_harmonize_kwargs": {"basic_check": true, "threads": 1, "remove": false,
                               "maf_threshold": 0.4, "ref_maf_threshold": 0.4},
  "output": {"path": "…", "saved": true, "n_variants": 14, "variant_delta": -1},
  "warnings": []
}
```

The manifest is the fastest way to answer "what exactly did this run do?" —
including whether reference resources were actually used (a run with
`fasta_path: null` and `inference_vcf_path: null` is a basic-check run, not full
harmonization).

## Variant counts and the delta

`n_variants_in` is the row count read from the input; `n_variants_out` is the row
count after harmonization. When `harmonization.remove` is `false`, counts should
normally be equal; a decrease means harmonization dropped rows. When
`remove: true`, a decrease is expected as flagged variants are removed.

## Interpreting an unexecuted tutorial

> **Important:** in this repository the notebook has **not** been run against
> real data in the development environment (no GWASLab install + multi-GB
> references were available). The numbers shown in the tutorial are therefore
> illustrative of the tooling, not measured results. Re-run the notebook locally
> once you have installed GWASLab and downloaded the references to obtain real
> results. See `docs/decisions.md`.
