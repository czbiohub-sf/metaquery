import os


base_dir = os.getcwd() # local path of metaquery folder
db_dir = os.path.join(base_dir, "db")
data_dir = os.path.join(base_dir, "data")
src_dir = os.path.join(base_dir, "metaquery", "src")


job_form = {
    "job_id": "MQ000001",
    "query": f"{base_dir}/tests/query.fasta",
    "outdir": f"{base_dir}/tests",
    "molecule_type": "protein",
    "max_evalue": 1e-5,
    "min_score": 70,
    "min_pid": 95,
    "min_qcov": 70,
    "min_tcov": 10,
    "threads": 8,
}


config = {
    "outdir": "/mnt/cz/metaquery_output",
    "sqlite_db": f"{db_dir}/metaquery_sqlites3.db",
    "matrix_path": f"{data_dir}/matrix/large_matrix/2016-02-04_6051-runs_matrix.txt",
    "protein_fa": f"{db_dir}/fasta/IGC_protein.fa",
    "dna_fa": f"{db_dir}/fasta/IGC_dna.fa",
    "protein_blastdb": f"{db_dir}/blast/protein/IGC",
    "dna_blastdb": f"{db_dir}/blast/dna/IGC",
    "rapdb": f"{data_dir}/ref/rapsearch/IGC.pep",
    "protein_blast": f"blastp",
    "dna_blast": f"blastn",
    "threads": 8
}


def get_args(form=job_form):
    return {
        "job_id": form['job_id'],
        "outdir": form['outdir'],
        "tempdir": form['tempdir'],
        "query": f"{form['outdir']}/query.fasta",
        "job_yaml": f"{form['outdir']}/job.ymal",
        'threads': int(form['threads']),

        'molecule_type': form['molecule_type'],
        'max_evalue': float(form['max_evalue']),
        'min_score': float(form['min_score']),
        'min_pid': float(form['min_pid']),
        'min_qcov': float(form['min_qcov']),
        'min_tcov': float(form['min_tcov']),

        'matrix_path': config['matrix_path'],
        'sqlite_db': config['sqlite_db'],
        'fasta': config['protein_fa'] if form['molecule_type'] == 'protein' else config['dna_fa'],
        'blast': config['protein_blast'] if form['molecule_type'] == 'protein' else config['dna_blast'],
        'rapsearch': 'rapsearch',
        'blastdb': config['protein_blastdb'] if form['molecule_type'] == 'protein' else config['dna_blastdb'],
        'rapdb': config['rapdb'],

        'min_reads':4000000,
    }


def get_Rscript():
    return {
        "pheno": f"{src_dir}/pheno.R",
        "taxa": f"{src_dir}/taxa.R",
        "table": f"{src_dir}/table.R",
        "plot": f"{src_dir}/plot.R",
        "pfunc": f"{src_dir}/pfunc.R",
        "export": f"{src_dir}/export.R"
    }


# Executable Documentation
def get_output_layout(token_id):
    return {
        "job_id":               f"{token_id}",
        "outdir":               f"{token_id}",
        "job_to_m8":            f"{token_id}/job_to_m8", #store_alignments
        "job_to_homologs":      f"{token_id}/job_to_homologs", #store_homologs
        "homolog_to_abun":      f"{token_id}/homolog_to_abun", #store_homolog_abun
        "job_to_abun":          f"{token_id}/job_to_abun", #store_gene_family
        "genus_to_abun":        f"{token_id}/genus_to_abun", #store_genera
    }
