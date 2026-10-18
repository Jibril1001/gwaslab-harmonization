# Data

## `to_harmonize.tsv` — tutorial dataset

A deliberately small (15-variant) summary-statistics file from the GWASLab
project, used by the harmonization tutorial. The `NOTE` column describes the
issue each variant was designed to exercise (clean match, allele flip,
palindromic SNP, indel, ambiguous/indistinguishable case, etc.).

- **Source:** https://github.com/Cloufield/gwaslab —
  `examples/0_sample_data/toy_data/to_harmonize.tsv`
- **License:** GWASLab is licensed **GPL-3.0-only**. This file is redistributed
  under that license with attribution. See the repository `LICENSE` notice.
- **Genome build:** hg19 / GRCh37 (the tutorial downloads hg19 reference
  resources; the coordinates in this file match hg19).
- **Format:** tab-separated, header row present.

### Columns

| Column | Meaning |
| --- | --- |
| `SNPID` | Variant identifier, `CHR:POS:EA:NEA` style (reference: `CHR:POS:NEA:EA`). |
| `CHR` | Chromosome (`1`–`22`, `X`). |
| `POS` | Base-pair position. |
| `EA` | Effect allele. |
| `NEA` | Non-effect allele. |
| `EAF` | Effect-allele frequency. |
| `BETA` | Effect size (log-odds / beta). |
| `SE` | Standard error of `BETA`. |
| `P` | P-value. |
| `N` | Sample size. |
| `DIRECTION` | Per-study effect-direction string (GWASLab convention). |
| `NOTE` | Tutorial annotation describing the intended harmonization case. |

> The `NOTE` column is documentation, not a harmonization input. It is kept
> through the run so results can be compared against the intended case.

### Integrity

No checksum is published by GWASLab for this toy file, so none is recorded here.
If you re-download the file, confirm it has 15 data rows plus the header.

## Large reference resources are **not** stored here

The reference FASTA and reference VCF/BCF used by the harmonization workflow are
large (hundreds of MB to several GB) and are **not** committed. See
`docs/reference_data.md` for how to obtain them and how they are configured.
