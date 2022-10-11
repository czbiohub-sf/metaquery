# Command line arguments
args <- commandArgs(trailingOnly = TRUE)
job_id <- args[1]
tempdir <- args[2]


library(readr)
library(dplyr)

outdir <- dirname(tempdir)

build_homolog_table <- function(job_id) {
  ## OUTPUT: homolog_table
  job_to_homologs <- read_delim(file.path(tempdir, "job_to_homologs"), delim = "\t",
    col_names = c("job_id", "aln_id", "homolog_name", "homolog_id", "status", "kegg", "eggnog", "phylum", "genus", "hoomolog_seq"),
    col_types = cols())

  job_to_m8 <- read_delim(file.path(tempdir, "job_to_m8"), delim="\t",
      col_names = c("job_id", "aln_id", "query_id", "target_name", "target_id", "qlen", "tlen", "aln", "qstart", "qend", "tstart", "tend", "qcov", "tcov", "pid", "evalue"),
      col_types = cols())

  tab <- left_join(job_to_homologs, job_to_m8, by=c("job_id", "aln_id")) %>%
    select(query_id, target_id, status, kegg, eggnog, phylum, genus, qcov, tcov, pid)

  count_homologs <- nrow(tab)

  tab %>% write.table(file.path(outdir, "homolog_table.tsv"), sep="\t", quote=F, row.names = F)
}


build_taxa_table <- function(job_id) {
  ## OUTPUT: taxa_table
  ## INPUT: taxa_tests
  tab <- read_delim(file.path(tempdir, "taxa_tests"), delim="\t", col_types = cols()) %>%
    mutate(spearman_qvalue = as.numeric(spearman_qvalue)) %>%
    mutate(spearman_rho = signif(spearman_rho, 3)) %>%
    mutate(spearman_pvalue = signif(spearman_pvalue, 3)) %>%
    mutate(spearman_qvalue = signif(spearman_qvalue, 3)) %>%
    arrange(spearman_pvalue)

  tab %>% write.table(file.path(outdir, "taxa_covariates.tsv"), sep="\t", quote=F, row.names = F)
}


build_pheno_table <- function(job_id) {
  ## INPUT: pheno_tests
  ## OUTPUT: pheno_table.tsv
  tab <- read_delim(file.path(tempdir, "pheno_tests"), delim="\t", col_types = cols()) %>%
    mutate(case_mean = signif(case_mean, 2)) %>%
    mutate(ctrl_mean = signif(ctrl_mean, 2)) %>%
    mutate(p_value = signif(p_value, 2)) %>%
    mutate(percentile = signif(percentile, 2))
  tab %>% write.table(file.path(outdir, "pheno_covariates.tsv"), sep="\t", quote=F, row.names = F)
}


build_homolog_table(job_id)
build_taxa_table(job_id)
build_pheno_table(job_id)
