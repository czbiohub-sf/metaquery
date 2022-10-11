# Command line arguments
args <- commandArgs(trailingOnly = TRUE)
job_id <- args[1]
tempdir <- args[2]
dbpath <- args[3]

########### INPUT TABLES: pheno_tp_subject, job_to_abun, pheno_tests
########### OUTPUT FILES: pheno_tests

library(RSQLite)
library(DBI)
library(dplyr)
library(readr)


mydb <- dbConnect(RSQLite::SQLite(), dbpath)


list.phenos <- function(mydb){
  df <- dbGetQuery(mydb, "SELECT distinct phenotype, country FROM pheno_to_subjects")
  return(df)
}


list.subjects <- function(mydb, pheno, country){
  df <- dbGetQuery(mydb, 'SELECT subject_id, status FROM pheno_to_subjects WHERE "phenotype" = :x AND country = :y', params = list(x = pheno, y = country))
  return(df)
}


read.abundance <- function(mydb, job_id, out_dir="."){
  # Input: job_to_abun, from store_gene_family()
  # Output: subject_id, copy_number, relative_abundance
  abun <- read_delim(file.path(out_dir, "job_to_abun"), delim="\t", col_names = c("job_id", "sample_id", "cov", "relabun", "copy"), col_types = cols())
  sample_to_subject <- dbGetQuery(mydb, 'SELECT * FROM sample_to_subject')

  abun <- left_join(abun, sample_to_subject, by=c("sample_id")) %>%
    group_by(subject_id) %>%
    summarize(copy_number = mean(copy), relative_abundance = mean(relabun)) %>%
    ungroup()
  return(abun)
}


fetch.pvalues <- function(mydb, pheno, country, database, level){
  pvalues = dbGetQuery(mydb, 'SELECT p_value FROM pheno_tests WHERE phenotype = :x AND country = :y AND database = :z AND level = :k',
      list(x = pheno, y = country, z = database, k = level))[,1]
  return(pvalues)
}


# Read in data
phenos <- list.phenos(mydb)
abun <- read.abundance(mydb, job_id, tempdir)

if (nrow(abun) == 0) quit()

print("\n\n\n")

# Compute associations
table <- as.data.frame(matrix(nrow=0,ncol=0)); row <- 0


for (i in seq(nrow(phenos))){
  subjects <- list.subjects(mydb, phenos[i,'phenotype'], phenos[i,'country'])
  # subject_id, status
  subjects <- left_join(subjects, abun[c("subject_id", "copy_number")], by=c("subject_id"))

  x <- subjects$copy_number
  y <- subjects$status

  my_test <- wilcox.test(x ~ y)
  pvalues <- fetch.pvalues(mydb, phenos[i,'phenotype'], phenos[i,'country'], 'eggnog', 'gene_family')

  if (! is.na(my_test$p.value)){
    row <- row + 1
    table[row,'phenotype'] <- phenos[i,'phenotype']
    table[row,'country'] <- phenos[i,'country']
    table[row,'case_n'] <- length(which(y == 1))
    table[row,'ctrl_n'] <- length(which(y == 0))
    table[row,'case_mean'] <- mean(x[y == 1], na.rm=T)
    table[row,'ctrl_mean'] <- mean(x[y == 0], na.rm=T)
    table[row,'p_value'] <- my_test$p.value
    table[row,'rank'] <- length(which(my_test$p.value > pvalues))
    table[row,'percentile'] <- 100*table[row,'rank']/length(pvalues)
  }
}

table %>% write.table(file.path(tempdir, "pheno_tests"), sep="\t", quote=F, row.names=F)

dbDisconnect(mydb)
