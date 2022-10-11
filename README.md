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
aws s3 cp --recursive xx db
aws s3 cp --recursive xx data
```

## Test Run

```
metaquery --query tests/query.fasta --job_yaml tests/job.yaml
```
