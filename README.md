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

metaquery --search_by_name --search_name "Bacteroides vulgatus"
```
