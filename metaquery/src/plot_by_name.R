# Configuration
args <- commandArgs(TRUE)
type <- args[1] #taxa
db <- args[2] #metaphlan2
level <- args[3] #species
name <- args[4] #'Bacteroides_vulgatus'
outdir <- args[5]
dbpath <- args[6]
pfunc_dir <- args[7]


library(dplyr)
library(readr)
library(RSQLite)
library(DBI)


source(pfunc_dir)

mydb <- dbConnect(RSQLite::SQLite(), dbpath)


read.sample.abun <- function(mydb, type, db, level, name) {
  metric <- ifelse(type == "function", "copy_number", "relative_abundance")
  query <- paste("SELECT sample_id, ", metric, " from sample_to_abundance ",
                  "WHERE type = '", type, "' ",
                  "and db = '", db, "' ",
                  "and level = '", level, "' ",
                  "and name = '", name, "'", sep="")
  df <- dbGetQuery(mydb, query)
  row.names(df) <- df$sample_id
  return(df)
}


read.pheno.data <- function(mydb, type, db, level, name, pheno, country){
  metric <- ifelse(type=='taxa','relative_abundance', 'copy_number')

  query <- paste("SELECT ",
           " sample_id, ", metric,
           " FROM sample_to_abundance WHERE ",
           "  db = '", db, "' ",
           "  and level = '", level, "' ",
           "  and name = '", name, "' ", sep="")
  sample_to_abundance <- dbGetQuery(mydb, query)
  colnames(sample_to_abundance) <- c("sample_id", "abun")

  sample_to_subject <- dbGetQuery(mydb, "SELECT * FROM sample_to_subject")

  df <- left_join(sample_to_abundance, sample_to_subject, by=c("sample_id")) %>%
    group_by(subject_id) %>%
    summarize(abundance = mean(abun)) %>%
    ungroup()

  pheno_to_subjects <- dbGetQuery(mydb, 'SELECT * FROM pheno_to_subjects WHERE phenotype = :x AND country = :y', list(x = pheno, y = country)) %>%
    mutate(status = ifelse(status==0, "control", "case"))

  df <- left_join(df, pheno_to_subjects, by=c("subject_id")) %>% filter(!is.na(phenotype))
  row.names(df) <- df$subject_id
  return(df)
}

# TODO: I need to make sure there is a outdir in the working environment


abun <- read.sample.abun(mydb, type, db, level, name)
back <- read.background.data(mydb, db, level)
plot.prevalence(abun, back, type, name)
plot.abundance(abun, back, type, name)


phenos <- read.phenos(mydb)
for (i in seq(nrow(phenos))){
  pheno <- phenos[i,'phenotype']
  country <- phenos[i,'country']
  back <- read.background.pvalues(mydb, pheno, country, db, level)
  abun <- read.pheno.data(mydb, type, db, level, name, pheno, country)
  plot.pheno.association(abun, back, type, name=paste(name, pheno, country, sep='.'))
}


dbDisconnect(mydb)
