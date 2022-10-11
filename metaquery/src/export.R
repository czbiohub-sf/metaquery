library(dplyr)
library(readr)

# Configuration
args <- commandArgs(TRUE)
job_id <- args[1]
out_dir <- args[2]
dir.create(file.path(out_dir), showWarnings = FALSE)


write_m8 <- function(job_id, outdir = ".") {
  job_to_m8 <- read_delim(file.path(outdir, "temp/job_to_m8"), delim="\t",
      col_names = c("job_id", "aln_id", "query_id", "target_name", "target_id", "qlen", "tlen", "aln", "qstart", "qend", "tstart", "tend", "qcov", "tcov", "pid", "evalue"),
      col_types = cols())
  job_to_m8 %>% write.table(file.path(outdir, "blast_results.tsv"), sep="\t", quote=F, row.names=F)
}

write_homolog_annotations <- function(job_id, outdir = ".") {
  job_to_homologs <- read_delim(file.path(outdir, "temp/job_to_homologs"), delim = "\t",
    col_names = c("job_id", "aln_id", "homolog_name", "homolog_id", "status", "kegg", "eggnog", "phylum", "genus", "hoomolog_seq"),
    col_types = cols())
  job_to_homologs %>% write.table(file.path(outdir, "homologs_annotations.tsv"), sep="\t", quote=F, row.names=F)
}

write_homo_abun <- function(job_id, outdir=".") {
  homolog_to_abun <- read_delim(file.path(outdir, "temp/homolog_to_abun"), delim = "\t",
    col_names = c("job_id", "target_id", "sample_id", "read_depth", "relative_abundance", "copy_number"),
    col_types = cols()) %>%
    select(sample_id, target_id, read_depth, relative_abundance, copy_number)
  homolog_to_abun %>% write.table(file.path(outdir, "homologs_abundance.tsv"), sep="\t", quote=F, row.names=F)
}


write_m8(job_id, out_dir)
write_homolog_annotations(job_id, out_dir)
write_homo_abun(job_id, out_dir)
