# MetaQuery

## Install

```
git clone https://github.com/czbiohub/metaquery.git
cd metquery
conda env create -f env.yml
conda activate metaquery
pip install .
```

## Prepare MetaQuery Database

```
aws s3 cp --recursive s3://zhaoc1-metaquery/2022-metaquery/metaquery/db db
aws s3 cp --recursive s3://zhaoc1-metaquery/2022-metaquery/metaquery/data data
```

## Test Run

```
metaquery --search_by_sequence --query tests/query.fasta --job_yaml tests/job.yaml

metaquery --search_by_name --search_name "Bacteroides vulgatus" --job_yaml tests/job2.yaml
```

## MetaQuery Workflow

Figure S1: MetaQuery estimates the abundance of a query sequence across 1267 publicly available faecal metagenomes from human subjects.

![alt text](https://github.com/czbiohub/metaquery/blob/main/FigureS1.png?raw=true)

1) The user enters one or more protein sequences in FASTA format. These sequenced are searched against the integrated catalog of reference genes in the human gut microbiome (IGC) (Li, et al., 2014) using BLAST (Altschul, et al., 1990). The IGC is composed of 9.9 million genes that originate from microbial reference genomes and extensive metagenomic assemblies.

2) Homologs of the query sequence are identified in the IGC based on the BLAST alignments and the set of alignment parameters entered by the user. These parameters include maximum E-value and minimum %ID in addition to a 70% minimum alignment coverage threshold. Because over 40% of the genes in the IGC lack either start/stop codons (Li, et al., 2014), many alignments will fail to globally cover both the query and target sequence. Therefore we enforce a glocal alignment coverage defined as: max(Laln/Lquery, Laln/Ltarget), where Laln is the alignment length, Lquery is the length of the query, and Ltarget is the length of the target. 

4) Next, we obtain the relative abundances of identified homologs from a precomputed abundance matrix built by (Li, et al., 2014). This matrix consists of relative abundances of 9.9 million genes across 1,267 samples, where the relative abundance of genes is scaled to sum to 1.0 per-sample. For each query, we sum the relative abundances of identified homologs for each sample. 

5) Optionally, our software normalizes gene relative abundances using a panel of 30 universal single-copy genes (Nayfach and Pollard, 2015). The result of this normalization is a metric called Average Genomic Copy Number, which represents the estimated average copy number of a gene across microbial cells (Manor and Borenstein, 2015). Without normalization, the resulting metric is Relative Abundance, which is scaled to sum to 1.0 across all genes for a sample.


## Expected Output: Figures

### Abundance Plot

- `abundnace.png`: The abundance of identified homologs across gut microbiome samples.
For taxonomic groups (e.g. species), abundance is defined as the proportion of cells that are from a taxonomic group.
For functional groups (e.g. gene families), abundance is defined as the average copy-number of the function per cell.

Left panel: the abundance of the identified homologs was estimated across human gut metagenomes. Samples with an abundance of zero were assigned the smallest non-zero value.

Right panel: the average abundance of identified homologs was compared to the average abundance of other groups at the same functional or taxonomic level.


### Prevalence Plot

- `prevalence.png`: The prevalence of identified homologs across gut microbiome samples. Prevalence is defined at the percent of samples where identified homologs is found.

Left panel: the prevalence of identified homologs was estimated across human gut metagenomes at different abundance thresholds.

Right panel: the prevalence of identified homologs at a minimum abundance of 0.001 was compared to the prevalence of other groups at the same functional or taxonomic level.


### Boxplots of Association of Abundance with Clinical Phenotypes

In addition, MetaQuery also generates a few figures of association of identified homologs abundance with clinical phenotypes.
[Wilcoxon rank-sum tests](https://en.wikipedia.org/wiki/Mann-Whitney_U_test) were performed to determine if the abundance of identified homologs was different between cases and controls for several diseases (see table).

For each disease, case and control individuals were selected from the same country and individuals with co-morbities were excluded.

See the <a href='./about.py#metagenomes'>documentation</a> for more information on these cohorts

- `p_value` indicates whether there is a significant difference in the abundance of identified homologs between cases and controls.
- `rank` and `percentile` indicate how the p_value for identified homologs compares to other functional or taxonomic groups.

For example, a percentile of 5.0 indicates your p_value was more significant than 95%% of other functions or taxa.

Boxplots include:
- `Ulcerative colitis.Spain.png`
- `Crohns disease.Spain.png`
- `Obesity.Denmark.png`
- `Type II diabetes.China.png`
- `Type II diabetes.Denmark.png`
- `Type II diabetes.Sweden.png`
- `Liver cirrhosis.China.png`
- `Rheumatoid arthritis.China.png`
- `Colorectal cancer.Austria.png`


## Expected Output: Tables

### Search-by-Sequence

As mentioned in the above workflow, MetaQuery generateds the following tables accordingly: 
- `homolog_table.tsv`
- `homologs_abundance.tsv`
- `homologs_annotations.tsv`
- `taxa_covariates.tsv`
- `pheno_covariates.tsv`

In addition, the users can also download the raw blast results `blast_results.tsv` and the full metadata of the subjects `subject_attributes.tsv`. 

### Search-by-Name

MetaQuery returns a `search_results.tsv` table, listing `Query Type`, `Database`, `Level` and `Name`. 

For each result, MetaQuery produces the above-mentioned figures, as well as the statistics table `pheno_table.tsv`.

