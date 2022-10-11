#!/usr/bin/env python3

import time
import subprocess

from metaquery.src.model import get_Rscript
from metaquery.src.igctools import sqlite3_connect


def command(cmd):
    return subprocess.run(cmd, shell=True)


def run_R_analyses(config):
    job_id = config['job_id']
    local_db = config['sqlite_db']
    outdir = config['tempdir']

    for module in ['pheno', 'taxa']:
        start = time.time()
        rdir = get_Rscript()[module]
        command = f"Rscript {rdir} {job_id} {outdir} {local_db}"
        print(f"\n{command}")
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        print("Rscript %s (s): %s" % (module, round(time.time() - start, 2)))


def report_job(config):
    job_id = config['job_id']
    local_db = config['sqlite_db']
    outdir = config['tempdir']
    pfunc_dir = get_Rscript()["pfunc"]
    for module in ['table', 'plot']:
        start = time.time()
        rdir = get_Rscript()[module]
        command = f"Rscript {rdir} {job_id} {outdir} {local_db} {pfunc_dir}"
        print(f"\n{command}")
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        print("Rscript %s (s): %s" % (module, round(time.time() - start, 2)))


def write_subject_attributes(config):
    """ INPUT:subject_attributes. OUTPUT: subject_attributes"""
    job_id = config['job_id']
    outdir = config['outdir']

    conn, cursor = sqlite3_connect(config["sqlite_db"])
    query = "select * from subject_attributes where pubmed_id not in ('25807110', '25981789')"
    cursor.execute(query)

    outfile = open(f"{outdir}/subject_attributes.tsv", 'w')
    outfile.write('\t'.join([_[0] for _ in cursor.description])+'\n')
    for r in cursor.fetchall():
        outfile.write('\t'.join([str(v) for v in r])+'\n')
    outfile.close()
    conn.close()


def export(config):
    job_id = config['job_id']
    outdir = config['outdir']
    write_subject_attributes(config)
    start = time.time()
    rdir = get_Rscript()['export']
    command = f"Rscript {rdir} {job_id} {outdir}"
    print(f"\n{command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    print("Rscript %s (s): %s" % ('export', round(time.time() - start, 2)))
