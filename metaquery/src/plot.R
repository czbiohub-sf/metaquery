# Configuration
args <- commandArgs(TRUE)
job_id <- args[1]
tempdir <- args[2]
dbpath <- args[3]
pfunc_dir <- args[4]


library(dplyr)
library(readr)
library(RSQLite)
library(DBI)

source(pfunc_dir)

mydb <- dbConnect(RSQLite::SQLite(), dbpath)
outdir <- dirname(tempdir)

# Main
abun <- read.sample.abun(tempdir, job_id)
back <- read.background.data(mydb, 'eggnog', 'gene_family')
###### FINE .....
abun <- as.data.frame(abun)
back <- as.data.frame(back)


plot.prevalence(abun, back, type='function', name=job_id)
plot.abundance(abun, back, type='function', name=job_id)


phenos <- read.phenos(mydb)
for (i in seq(nrow(phenos))){
  pheno <- phenos[i,'phenotype']
  country <- phenos[i,'country']
  back <- read.background.pvalues(mydb, pheno, country, 'eggnog', 'gene_family')
  abun <- read.pheno.data(tempdir, mydb, job_id, pheno, country)
  if (nrow(filter(abun, abundance>0)) > 0) {
    plot.pheno.association(abun, back, type='function', name=paste(pheno, country, sep='.')) #job_id
  }
}

dbDisconnect(mydb)
