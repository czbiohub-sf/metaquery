##
## Libraries
##

import subprocess
import time
import sqlite3
import Bio.SeqIO


##
## Classes
##
class Query:
    """ Base class for query sequences """
    def __init__(self, name, desc, seq):
        self.name = name
        self.desc = desc
        self.sequence = str(seq)
        self.length = len(self.sequence)


class Run:
    """
    Base class for sequencing run
    Four table lookup the MYSQL tables give the INPUT NAME
    """
    def __init__(self, name, cursor):
        self.name = name # run_accession, the first row of the large matrix
        self.phyeco = self.fetch_phyeco(cursor)
        self.igc = self.fetch_igc(cursor)
        self.status = self.fetch_status(cursor)
        self.read_count = self.fetch_read_count(cursor)

    def fetch_phyeco(self, cursor):
        cursor.execute("SELECT coverage FROM run_to_abundance WHERE name = 'median' AND db = 'phyeco' AND run_accession = ?", (self.name,))
        return cursor.fetchone()[0]

    def fetch_igc(self, cursor):
        cursor.execute("SELECT coverage FROM run_to_abundance WHERE name = 'sum' AND db = 'igc' AND run_accession = ?", (self.name,))
        return cursor.fetchone()[0]

    def fetch_status(self, cursor):
        cursor.execute("SELECT status FROM run_to_qc WHERE run_accession = ?", (self.name,))
        return cursor.fetchone()[0]

    def fetch_read_count(self, cursor):
        cursor.execute("SELECT spots FROM runs WHERE run_accession = ?", (self.name,))
        return cursor.fetchone()[0]


class Sample:
    """ Base class for metagenomic samples """
    def __init__(self, name, runs, cursor):
        self.name = name  # sample_id in the run_to_sample table
        self.runs = self.fetch_runs(runs, cursor)
        self.phyeco = self.phyeco_cov()
        self.igc = self.igc_cov()
        self.read_count = self.count_reads()

    def fetch_runs(self, runs, cursor):
        """ Return list of Runs """
        sample_runs = []
        cursor.execute("SELECT run_accession FROM run_to_sample WHERE sample_id = ?", (self.name, ))
        ## one sample_id can correspond to multile run_accessions
        for r in cursor.fetchall():
            if r[0] in runs and runs[r[0]].status == 'PASS':
                sample_runs.append(runs[r[0]])
        return sample_runs

    def phyeco_cov(self):
        return sum([run.phyeco for run in self.runs])

    def igc_cov(self):
        return sum([run.igc for run in self.runs])

    def count_reads(self):
        return sum([run.read_count for run in self.runs])


class Homolog:
    """ Base class for query homologs """
    def __init__(self, m8, samples, cursor, args):
        self.id = m8['target_id']
        self.aln_id = m8['aln_id']
        self.name = m8['target_name']
        self.query_id = m8['query_id']
        self.annotations = self.fetch_annotations(cursor)
        self.sequence = self.fetch_fasta_seq(args, cursor) # fetch IGC protein sequences
        self.length = len(self.sequence)
        self.run_abun = self.fetch_run_abun(args['matrix_path'], cursor)
        self.sample_abun = self.fetch_sample_abun(samples)

    def fetch_annotations(self, cursor):
        cursor.execute("SELECT * FROM igc_info WHERE cluster_id = ?", (self.id,))
        # NOTE: the MYSQL used Unicode string ('u'). Not sure if this will affect the
        fields = [i[0] for i in cursor.description]
        values = cursor.fetchone()
        return dict([(f, v) for f, v in zip(fields, values)])

    def fetch_fasta_seq(self, args, cursor):
        seq = ''
        infile = open(args['fasta'])
        infile.seek(self.fetch_fasta_offset(cursor, args['molecule_type']))
        next(infile)
        for line in infile:
            if line[0] == '>':
                break
            else:
                seq += line.rstrip()
        infile.close()
        return seq

    def fetch_fasta_offset(self, cursor, molecule_type):
        ## There are three columns end with _offset: dna, protein and matrix
        cursor.execute("SELECT %s_offset FROM igc_info WHERE cluster_id = %s" % (molecule_type, self.id))
        return cursor.fetchone()[0]

    def fetch_abun_offset(self, cursor):
        cursor.execute("SELECT matrix_offset FROM igc_info WHERE cluster_id = ?", (self.id,))
        return cursor.fetchone()[0]

    def fetch_run_abun(self, matrix_path, cursor):
        infile = open(matrix_path)
        runs = next(infile).rstrip().split() #this is the first row of the large abundance matrix
        infile.seek(self.fetch_abun_offset(cursor))
        abuns = [float(_) for _ in infile.readline().rstrip().split()[1:]]
        infile.close()
        run_to_abun = dict([(run, abun) for run, abun in zip(runs, abuns)])
        return run_to_abun

    def fetch_sample_abun(self, samples):
        sample_to_abun = {}
        for sample in samples:
            sample_to_abun[sample.name] = {'cov':0.0, 'relabun':0.0, 'copy':0.0}

        for sample in samples:
            for run in sample.runs:
                sample_to_abun[sample.name]['cov'] += self.run_abun[run.name]

            coverage = sample_to_abun[sample.name]['cov']
            sample_to_abun[sample.name]['relabun'] += coverage/sample.igc
            sample_to_abun[sample.name]['copy'] += coverage/sample.phyeco
        return sample_to_abun


class GeneFamily:
    """ Base class for group of homologs """
    def __init__(self, homologs):
        self.sample_abun = self.fetch_sample_abun(homologs)

    def fetch_sample_abun(self, homologs):
        sample_to_abun = {}
        if len(homologs) == 0:
            return sample_to_abun
        ## list of all samples (2139)
        for sample_id in homologs[0].sample_abun:
            sample_to_abun[sample_id] = {'cov':0.0, 'relabun':0.0, 'copy':0.0}

        for homolog in homologs:
            for sample_id in homolog.sample_abun:
                sample_to_abun[sample_id]['cov'] += homolog.sample_abun[sample_id]['cov']
                sample_to_abun[sample_id]['relabun'] += homolog.sample_abun[sample_id]['relabun']
                sample_to_abun[sample_id]['copy'] += homolog.sample_abun[sample_id]['copy']
        return sample_to_abun


class Genera:
    """ Base class for group of genera: homolog 对应的genus """
    def __init__(self, homologs):
        self.names = self.fetch_names(homologs) ## <--- genera
        self.genus_abun = self.fetch_genus_abun(homologs)

    def fetch_names(self, homologs):
        genera = set([])
        for homolog in homologs:
            genera.add(homolog.annotations['genus'])
        return list(genera)

    def fetch_genus_abun(self, homologs):
        genus_to_abun = {}
        if len(homologs) == 0:
            return genus_to_abun
        for genus in self.names:
            genus_to_abun[genus] = {}
            for sample_id in homologs[0].sample_abun:
                genus_to_abun[genus][sample_id] = {'cov':0.0, 'relabun':0.0, 'copy':0.0}

        for homolog in homologs:
            genus = homolog.annotations['genus']
            for sample_id in homolog.sample_abun:
                genus_to_abun[genus][sample_id]['cov'] += homolog.sample_abun[sample_id]['cov']
                genus_to_abun[genus][sample_id]['relabun'] += homolog.sample_abun[sample_id]['relabun']
                genus_to_abun[genus][sample_id]['copy'] += homolog.sample_abun[sample_id]['copy']
        return genus_to_abun

##
## Functions
##

def sqlite3_connect(local_db):
    conn = sqlite3.connect(local_db)
    cursor = conn.cursor()
    return conn, cursor


def format_data(x, decimal=".6f"):
    return format(x, decimal) if isinstance(x, float) else str(x)


def init_runs(args):
    conn, cursor = sqlite3_connect(args['sqlite_db'])
    runs = {} # dictionary of Run objects: first row of the large matrix
    for line in open(args['matrix_path']):
        for run in line.rstrip().split():
            runs[run] = Run(run, cursor)
        break
    conn.close()
    return runs


def init_samples(args, runs):
    conn, cursor = sqlite3_connect(args['sqlite_db'])
    samples = [] # list of Sample objects
    cursor.execute("SELECT distinct sample_id FROM run_to_sample")
    for r in cursor.fetchall(): # ONE sample_id ~ SEVERAL run_accessions
        sample = Sample(r[0], runs, cursor)
        if sample.read_count >= args['min_reads']:
            samples.append(sample)
    conn.close()
    return samples


def init_queries(args):
    queries = {}
    with open(args['query']) as stream:
        for rec in Bio.SeqIO.parse(stream, 'fasta'):
            ## If we have multiple input sequences, it should show up here.
            qry_id = rec.id
            description = ""
            qry_seq = str(rec.seq).upper()
            qry_len = len(qry_seq)
            queries[qry_id] = Query(qry_id, description, qry_seq)
    return queries


def init_alignments(args, queries):
    conn, cursor = sqlite3_connect(args['sqlite_db'])
    alignments = []
    blastout = igc_blast(args)
    for index, m8 in enumerate(parse_blast(blastout)):
        m8 = update_m8(m8, args['job_id'], queries[m8['query_id']], index, cursor, args['molecule_type'])
        alignments.append(m8)
    conn.close()
    return alignments


def fetch_target_info(cursor, molecule_type, target_id):
    query = "select cluster_id, %s_length from igc_info where gene_id = '%s'" % (molecule_type, target_id)
    cursor.execute(query)
    return cursor.fetchone()


def update_m8(m8, job_id, query, index, cursor, molecule_type):
    target_id, target_length = fetch_target_info(cursor, molecule_type, m8['target_id'])
    m8['job_id'] = job_id
    m8['aln_id'] = index
    m8['qlen'] = query.length
    m8['tlen'] = target_length
    m8['target_name'] = m8['target_id']
    m8['target_id'] = target_id
    qstart, qend, tstart, tend = m8['qstart'], m8['qend'], m8['tstart'], m8['tend']
    m8['qstart'] = min(qstart, qend)
    m8['qend'] = max(qstart, qend)
    m8['tstart'] = min(tstart, tend)
    m8['tend'] = max(tstart, tend)
    m8['qcov'] = round(100*(m8['qend']-m8['qstart']+1)/float(m8['qlen']), 2)
    m8['tcov'] = round(100*(m8['tend']-m8['tstart']+1)/float(m8['tlen']), 2)
    return m8


def igc_blast(args):
    command = f"{args['blast']} -query {args['query']} -db {args['blastdb']} -evalue {args['max_evalue']} -num_threads {args['threads']} -max_target_seqs 10000 -outfmt 6"
    print(f"\n{command}\n")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    return out.decode()


def parse_blast(blastout):
    formats = {0:str, 1:str, 2:float, 3:int, 4:float,
               5:float, 6:float, 7:float, 8:float,
               9:float, 10:float, 11:float}
    fields = {0:'query_id', 1:'target_id', 2:'pid', 3:'aln', 4:'mis',
              5:'gaps', 6:'qstart', 7:'qend', 8:'tstart',
              9:'tend', 10:'evalue', 11:'score'}
    for line in blastout.rstrip('\n').split('\n'):
        r = line.rstrip().split()
        if len(r) == 12:
            yield dict([(fields[i], formats[i](v)) for i, v in enumerate(r)])


def format_m8(m8):
    value = (m8['job_id'], m8['aln_id'], m8['query_id'], m8['target_name'], m8['target_id'], \
            m8['qlen'], m8['tlen'], m8['aln'], m8['qstart'], m8['qend'], m8['tstart'], m8['tend'], \
            m8['qcov'], m8['tcov'], m8['pid'], m8['evalue'])
    return value


def insert_rows(outdir, table, values):
    table_fp = f"{outdir}/{table}"
    with open(table_fp, "w") as stream:
        for val in values:
            stream.write("\t".join(map(format_data, val)) + "\n")


def store_alignments(args, alignments):
    values = []
    for m8 in alignments:
        values.append(format_m8(m8))
    cols_job_to_m8 = ["job_id", "aln_id", "query_id", "target_name", "target_id", "qlen", \
            "tlen", "aln", "qstart", "qend", "tstart", "tend", "qcov", "tcov", "pid", "evalue"]
    insert_rows(args['tempdir'], "job_to_m8", values)


def init_homologs(args, alns, samples):
    """ Store homologs for each query """
    conn, cursor = sqlite3_connect(args['sqlite_db'])
    homologs = []
    top_hits = find_top_hits(alns, args)

    for m8 in top_hits:
        homolog = Homolog(m8, samples, cursor, args)
        homologs.append(homolog)
    conn.close()
    return homologs


def find_top_hits(alns, args):
    """ For each query, we only keep the top hit """
    top_hits = {}
    for m8 in alns:
        if filter_hit(m8, args):
            continue
        elif m8['target_id'] not in top_hits:
            top_hits[m8['target_id']] = m8
        elif m8['score'] > top_hits[m8['target_id']]['score']:
            top_hits[m8['target_id']] = m8
    return top_hits.values()


def filter_hit(m8, args):
    """ Filter blast alignment from m8 file """
    if m8['score'] < args['min_score']:
        return True
    elif m8['pid'] < args['min_pid']:
        return True
    elif m8['qcov'] < args['min_qcov']:
        return True
    elif m8['tcov'] < args['min_tcov']:
        return True
    else:
        return False


def store_homologs(args, homologs):
    """ Write to job_to_homologs """
    values = []
    for h in homologs:
        value = (args['job_id'], h.aln_id, h.name, h.id, h.annotations['status'].replace("'", "\\'"), \
                h.annotations['kegg'], h.annotations['eggNOG'], h.annotations['phylum'], h.annotations['genus'], h.sequence)
        values.append(value)
    cols_job_to_homoglos = ["job_id", "aln_id", "homolog_name", "homolog_id", "status", "kegg", "eggNog", "phylum", "genus", "hoomolog_seq"]
    insert_rows(args['tempdir'], "job_to_homologs", values)


def store_homolog_abun(args, homologs):
    values = []
    for h in homologs:
        for sample_id in h.sample_abun:
            value = (args['job_id'], h.id, sample_id, h.sample_abun[sample_id]['cov'], h.sample_abun[sample_id]['relabun'], h.sample_abun[sample_id]['copy'])
            values.append(value)
    insert_rows(args['tempdir'], "homolog_to_abun", values)


def store_gene_family(args, gene_family):
    values = []
    for sample_id in gene_family.sample_abun:
        value = (args['job_id'], sample_id, gene_family.sample_abun[sample_id]['cov'], \
                gene_family.sample_abun[sample_id]['relabun'], gene_family.sample_abun[sample_id]['copy'])
        values.append(value)
    schema = ["job_id", "sample_id", "cov", "relabun", "copy"]
    insert_rows(args['tempdir'], "job_to_abun", values)


def store_genera(args, genera):
    values = []
    for genus_name in genera.genus_abun:
        for sample_id in genera.genus_abun[genus_name]:
            value = (args['job_id'], genus_name, sample_id, \
                    genera.genus_abun[genus_name][sample_id]['cov'], \
                    genera.genus_abun[genus_name][sample_id]['relabun'], \
                    genera.genus_abun[genus_name][sample_id]['copy'])
            values.append(value)
    schema = ["job_id", "genus_name", "sample_id", "cov", "relabun", "copy"]
    insert_rows(args['tempdir'], "genus_to_abun", values)


####################################################
def run_pipeline(args):
    """ Run IGCtools pipeline """
    start = time.time()
    runs = init_runs(args)
    print("Init RUNS (s): %s" % round(time.time()-start, 2))

    start = time.time()
    samples = init_samples(args, runs)
    print("Init SAMPLES (s): %s" % round(time.time()-start, 2))

    start = time.time()
    queries = init_queries(args)
    print("Init QUERIES (s): %s" % round(time.time()-start, 2))

    start = time.time()
    alignments = init_alignments(args, queries)
    if len(alignments) == 0:
        print("EMPTY BLAST Search Results. Exit Now")
        return "EMPTY"

    store_alignments(args, alignments)
    print("Init ALIGNMENTS (s): %s" % round(time.time()-start, 2))

    start = time.time()
    homologs = init_homologs(args, alignments, samples)
    store_homologs(args, homologs)
    store_homolog_abun(args, homologs)
    print("Init HOMOLOGS (s): %s" % round(time.time()-start, 2))

    start = time.time()
    gene_family = GeneFamily(homologs) ## 环环相扣
    store_gene_family(args, gene_family)
    print("Init GENE FAMILY(s): %s" % round(time.time()-start, 2))

    start = time.time()
    genera = Genera(homologs)
    store_genera(args, genera)
    print("Init GENERA (s): %s" % round(time.time()-start, 2))

    return "DONE"
