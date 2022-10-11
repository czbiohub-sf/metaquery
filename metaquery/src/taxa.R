# Command line arguments
args <- commandArgs(trailingOnly = TRUE)
job_id <- args[1]
tempdir <- args[2]
dbpath <- args[3]

## INPUT table: job_to_abun
## Output: taxa_tests


library(RSQLite)
library(DBI)
library(dplyr)
library(readr)


mydb <- dbConnect(RSQLite::SQLite(), dbpath)


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


read.tax_names <- function(mydb, tax_db, tax_level, min_prevalence){
  tax_names <- dbGetQuery(mydb, 'SELECT name FROM annotations WHERE type = "taxa" AND level = :y AND database = :z AND prevalence >= :k', list(y = tax_level, z = tax_db, k = min_prevalence))[,1]
  return(tax_names)
}


read.taxa <- function(mydb, db, level, name){
  ## MYSQL TABLE: sample_to_abundance 和 sample_to_subject
  query <- paste("select sample_id, relative_abundance",
           "from sample_to_abundance",
           "where type = 'taxa'",
           "and level = ", paste("'",level,"'",sep=""),
           "and name =", paste("'",name,"'",sep=""),
           "and db =", paste("'",db,"'",sep=""))
  taxa <- dbGetQuery(mydb, query)
  colnames(taxa) <- c("sample_id", "relabun")

  query <- "select * from sample_to_subject"
  sample_to_subject <- dbGetQuery(mydb, query)

  taxa <- left_join(taxa, sample_to_subject, by=c("sample_id")) %>%
    group_by(subject_id) %>%
    summarize(relative_abundance = mean(relabun)) %>%
    ungroup()

  return(taxa)
}


abun <- read.abundance(mydb, job_id, tempdir)

if (nrow(abun) == 0) quit()

tax_db <- 'metaphlan2'
min_prev <- 0.5

# taxonomic regressions
data <- as.data.frame(matrix(nrow=0, ncol=0))
row <- 0


for (tax_level in c('phylum', 'class', 'order', 'family', 'genus', 'species')){
  list_of_taxnames <- read.tax_names(mydb, tax_db, tax_level, min_prev)

  for (tax_name in list_of_taxnames){
    # subject_id, relative_abundance
    tax_abun <- read.taxa(mydb, tax_db, tax_level, tax_name)
    tax_abun <- left_join(tax_abun, abun[c("subject_id", "copy_number")], by=c("subject_id"))

    x <- tax_abun$copy_number
    y <- tax_abun$relative_abundance
    test <- cor.test(x, y, method='spearman')

    row <- row + 1
    data[row, 'tax_db'] <- tax_db
    data[row, 'tax_level'] <- tax_level
    data[row, 'tax_name'] <- tax_name
    data[row, 'spearman_rho'] <- round(test$estimate, digits=3)
    data[row, 'spearman_pvalue'] <- format(test$p.value, scientific=T, digits=3)
  }
}
data$spearman_qvalue <- format(p.adjust(data$spearman_pvalue, method='fdr'), scientific=T, digits=3)

data %>% write.table(file.path(tempdir, "taxa_tests"), sep="\t", quote=F, row.names=F)

dbDisconnect(mydb)
