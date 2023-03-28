# MetaQuery

## Install

```
git clone https://github.com/czbiohub/metaquery.git
cd metquery
conda env create -f env.yml
conda activate metaquery
pip install .
```

## Prepare DB

```
aws s3 cp --recursive s3://zhaoc1-metaquery/2022-metaquery/metaquery/db db
aws s3 cp --recursive s3://zhaoc1-metaquery/2022-metaquery/metaquery/data data
```

## Test Run

```
metaquery --search_by_sequence --query tests/query.fasta --job_yaml tests/job.yaml

metaquery --search_by_name --search_name "Bacteroides vulgatus" --job_yaml tests/job2.yaml
```

## Search By NAME Expected Output

MetaQuery returns a `search_results.tsv` table, listing `Query Type`, `Database`,
`Level` and `Name`.


For each result, MetaQuery produces a few plots:

### Abundance Plot

- `{name}.abundnace.png`: The abundance of `{name}` across gut microbiome samples.
For taxonomic groups (e.g. species), abundance is defined as the proportion of cells that are from a taxonomic group.
For functional groups (e.g. gene families), abundance is defined as the average copy-number of the function per cell.

Left panel: the abundance of `{name}` was estimated across human gut metagenomes. Samples with an abundance of zero were assigned the smallest non-zero value.

Right panel: the average abundance of `{name}` was compared to the average abundance of other groups at the same functional or taxonomic level.


### Prevalence Plot

- `{name}.prevalence.png`: The prevalence of `{name}` across gut microbiome samples. Prevalence is defined at the percent of samples where `{name}` is found.

Left panel: the prevalence of `{name}` was estimated across human gut metagenomes at different abundance thresholds.

Right panel: the prevalence of `{name}` at a minimum abundance of 0.001 was compared to the prevalence of other groups at the same functional or taxonomic level.


### Boxplots of Association of Abundance with Clinical Phenotypes

In addition, MetaQuery also generates a few figures of association of `{name}` abundance with clinical phenotypes.
[Wilcoxon rank-sum tests](https://en.wikipedia.org/wiki/Mann-Whitney_U_test) were performed to determine if the abundance of `{name}` was different between cases and controls for several diseases (see table).

For each disease, case and control individuals were selected from the same country and individuals with co-morbities were excluded.

See the <a href='./about.py#metagenomes'>documentation</a> for more information on these cohorts

- `p_value` indicates whether there is a significant difference in the abundance of `{name}` between cases and controls.
- `rank` and `percentile` indicate how the p_value for `{name}` compares to other functional or taxonomic groups.

For example, a percentile of 5.0 indicates your p_value was more significant than 95%% of other functions or taxa.

Boxplots include:
- `{name}.Ulcerative colitis.Spain.png`
- `{name}.Crohns disease.Spain.png`
- `{name}/Obesity.Denmark.png`
- `{name}/Type II diabetes.China.png`
- `{name}/Type II diabetes.Denmark.png`
- `{name}/Type II diabetes.Sweden.png`
- `{name}/Liver cirrhosis.China.png`
- `{name}/Rheumatoid arthritis.China.png`
- `{name}/Colorectal cancer.Austria.png`


### Statistics

- `pheno_table.tsv`
