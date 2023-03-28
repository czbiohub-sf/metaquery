library(dplyr)
library(readr)
library(RSQLite)
library(DBI)

log10 <- function(x){
  return(ifelse(x==0, log(min(x[x>0]),10), log(x,10)))
}


read.sample.abun <- function(outdir, job_id) {
  df <- read_delim(file.path(outdir, "job_to_abun"), delim="\t", col_names = c("job_id", "sample_id", "cov", "relative_abundance", "copy_number"), col_types = cols()) %>%
    select(sample_id, copy_number, relative_abundance)
  return(df)
}


read.phenos <- function(local_db){
  query <- "SELECT distinct phenotype, country FROM pheno_to_subjects"
  return(dbGetQuery(local_db, query))
}


read.pheno.data <- function(outdir, local_db, job_id, pheno, country){
  abun <- read_delim(file.path(outdir, "job_to_abun"), delim="\t", col_names = c("job_id", "sample_id", "cov", "relabun", "copy"), col_types = cols())
  query <- "SELECT * FROM sample_to_subject"
  sample_to_subject <- dbGetQuery(local_db, query)

  df <- left_join(abun, sample_to_subject, by=c("sample_id")) %>%
    group_by(subject_id) %>%
    summarize(abundance = mean(copy)) %>%
    ungroup()

  pheno_to_subjects <- dbGetQuery(local_db, 'SELECT * FROM pheno_to_subjects WHERE phenotype = :x AND country = :y', list(x = pheno, y = country)) %>%
    mutate(status = ifelse(status==0, "control", "case"))

  df <- left_join(df, pheno_to_subjects, by=c("subject_id")) %>% filter(!is.na(phenotype))
  return(df)
}

read.background.data <- function(mydb, db, level){
  df <- dbGetQuery(mydb, 'SELECT name, mean_abundance, prevalence FROM annotations WHERE database = :x AND level = :y', list(x = db, y = level))
  return(df)
}

read.background.pvalues <- function(mydb, pheno, country, db, level){
  df <- dbGetQuery(mydb, 'SELECT name, p_value FROM pheno_tests WHERE database = :x AND level = :y AND phenotype = :z AND country = :k',
        list(x = db, y = level, z = pheno, k = country))
  return(df)
}

compute.prev <- function(x){
  # prevalence is computed based on copy_number
  df <- as.data.frame(matrix(nrow=0,ncol=0)); row <- 0
  copy_nums <- c(1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1e-0)
  for (min_copy in copy_nums){
    row <- row + 1
    df[row, 'min_copy'] <- min_copy
    df[row, 'percent_samples'] <- 100*sum(x >= min_copy)/length(x)
  }
  return(df)
}

get.ats <- function(n=7,space=0.2,width=1){
  ats <- c(width/2+space)
  for (i in seq(2,n)){
    ats <- c(ats, max(ats)+space+width)
  }
  return(ats)
}

set.par <- function(){
  par(mfrow=c(1,2))
  par(mar=c(7,7,1.5,1.5))
  par(bg = 'gray99')
}

plot.prevalence <- function(abun, back, type, name){

  width <- 1000
  plot_name <- paste(outdir, paste(name, "prevalence", "png", sep="."), sep="/")
  if (file.exists(plot_name)) file.remove(plot_name)
  png(plot_name, width=width, height = width*0.5)
  set.par()

  sample.prev <- compute.prev(abun[,2])
  barplot(
    sample.prev$percent_samples, col='gray',
    xlab='', ylab='Prevalence (% of samples)', main='',
    ylim=c(0,110), names.arg=sample.prev$min_copy,
    cex.lab=2, cex.axis=1.75, cex.names=1.25
    )
  if (type == 'function') {
    xlab <- 'Minimum Abundance\n(gene copies per cell)'
  } else {
    xlab <- 'Minimum Abundance\n(proportion total cells)'
  }
  mtext(
    xlab, side=1, line=5, cex=2
    )
  text(
    x=get.ats(),
    y=6+(sample.prev$percent_samples),
    labels=round(sample.prev$percent_samples,1),
    cex=1.25, font=2, srt=90
    )

  indexes <- order(back$prevalence, decreasing=T)
  prevs <- back$prevalence[indexes]
  ranks <- seq(1, length(indexes))
  back[indexes, 'rank'] <- ranks
  prev <- sample.prev[sample.prev$min_copy==1e-3, 'percent_samples']
  rank <- length(which(prev < prevs))+1
  plot(
    ranks, log10(prevs),
    type='l', col='black',
    xlab='Rank', ylab='Prevalence (% of samples)', main='',
    cex.lab=2, cex.axis=1.75, lwd=2,
    yaxt='n'
    )
  mtext(
    side=1, adj=1, line=2.5, text='(less prevalent)', cex=1.25
  )
  mtext(
    side=1, adj=0, line=2.5, text='(more prevalent)', cex=1.25
  )
  axis(
    side=2, at=seq(-2,2), labels=10^seq(-2,2), cex.axis=1.75
  )
  points(
    rank, log10(prev),
    pch=21, cex=2, bg='red', lwd=2
  )
  legend(
    'topright',
    cex=1.5,
    legend=c(
      name,
      paste('Prevalence = ', round(prev, 2), '%', sep=''),
      paste('Rank = ', rank, '/', nrow(back), sep='')
    )
  )
  box(which='outer', lty='solid')
  dev.off()
}

plot.abundance <- function(abun, back, type, name){

  width <- 1000
  plot_name <- paste(outdir, paste(name, "abundance", "png", sep="."), sep="/")
  if (file.exists(plot_name)) file.remove(plot_name)
  png(plot_name, width=width, height=width*0.5)
  set.par()

  if ("copy_number" %in% colnames(abun)) {
    plotdata = abun$copy_number
  } else {
    print("here")
    plotdata = abun[,2]
  }

  hist(
    log10(plotdata), col='gray',
    xlab='', ylab='Number of Samples', main='',
    cex.lab=2, cex.axis=1.75,
    xaxt='n', breaks=30
    )
  mtext(
    side=1, line=5, cex=2,
    text=ifelse(type=='function', 'Abundance\n(gene copies per cell)', 'Abundance\n(proportion of cells)')
    )
  axis(
    side=1, at=seq(-6,2), labels=10^seq(-6,2), cex.axis=1.25
  )

  indexes <- order(back$mean_abundance, decreasing=T)
  abuns <- back$mean_abundance[indexes]
  ranks <- seq(1, length(indexes))
  back[indexes, 'rank'] <- ranks

  mean_abun <- mean(plotdata)
  rank <- length(which(mean_abun < abuns)) + 1
  plot(
    ranks, log10(abuns),
    type='l', col='black',
    xlab='Rank', ylab='Mean abundance', main='',
    cex.lab=2, cex.axis=1.75, lwd=2,
    yaxt='n'
    )
  mtext(
    side=1, adj=1, line=2.5, text='(less abundant)', cex=1.25
  )
  mtext(
    side=1, adj=0, line=2.5, text='(more abundant)', cex=1.25
  )
  axis(
    side=2, at=seq(-8,2), labels=10^seq(-8,2), cex.axis=1.75
  )
  points(
    rank, log10(mean_abun),
    pch=21, cex=2, bg='red', lwd=2
  )
  legend(
    'topright',
    cex=1.5,
    legend=c(
      name,
      paste('Mean Abundance = ', format(mean_abun, digits=2), sep=''),
      paste('Rank = ', rank, '/', nrow(back), sep='')
    )
  )
  box(which='outer', lty='solid')
  dev.off()
}


plot.pheno.association <- function(abun, back, type, name){
  width <- 1000
  plot_name <- paste(outdir, paste(name, "png", sep="."), sep="/")
  if (file.exists(plot_name)) file.remove(plot_name)
  png(plot_name, width=width, height = width*0.5)
  par(mfrow=c(1,2))
  par(mar=c(6,7,6,1.5))

  pvalue <- wilcox.test(abun$abundance ~ abun$status)$p.value

  ymin <- floor(min(log10(abun$abundance)))
  ymax <- ceiling(max(log10(abun$abundance)))
  ylab <- ifelse(type == 'function', 'Abundance (gene copies per cell)', 'Abundance (proportion total cells)')
  boxplot(
    log10(abun$abundance) ~ abun$status,
    col='blue', cex.axis=1.75, cex.lab=2,
    xlab='Disease Status', ylab=ylab,
    staplelwd=2, whisklwd=2, outline=FALSE,
    ylim=c(ymin, ymax), yaxt='n'
    )
  axis(
    side=2, cex.axis=1.75,
    at=seq(ymin, ymax),
    labels=10^seq(ymin, ymax)
  )
  stripchart(
    log10(abun$abundance) ~ abun$status, vertical=T,
    method = 'jitter', add=T
    )

  indexes <- order(back$p_value, decreasing=F)
  pvalues <- back$p_value[indexes]
  ranks <- seq(1, length(indexes))
  back[indexes, 'rank'] <- ranks
  rank <- length(which(pvalue > pvalues))+1
  plot(
    ranks, -log10(pvalues),
    type='l', col='black',
    xlab='Rank', ylab='Wilcoxon P-value', main='',
    cex.lab=2, cex.axis=1.75, lwd=2,
    yaxt='n'
    )
  mtext(
    side=1, adj=1, line=2.5, text='(less significant)', cex=1.25
  )
  mtext(
    side=1, adj=0, line=2.5, text='(more significant)', cex=1.25
  )
  ymin <- floor(min(-log10(pvalues)))
  ymax <- ceiling(max(-log10(pvalues)))
  axis(
    side=2, at=seq(ymin,ymax), labels=10^-seq(ymin,ymax), cex.axis=1.75
  )
  points(
    rank, -log10(pvalue),
    pch=21, cex=2, bg='red', lwd=2
  )
  legend(
    'topright',
    cex=1.5,
    legend=c(
      paste('P-value = ', format(pvalue, digits=2), sep=''),
      paste('Rank = ', rank, '/', nrow(back), sep='')
    )
  )
  title(name, side=3, outer=T, cex.main=2, line=-3)
  box(which='outer', lty='solid')
  dev.off()
}
