#!/usr/bin/env python3

import os
import time
import argparse
import tempfile
import yaml
import json

from hashlib import md5
from metaquery.src.model import get_args
from metaquery.src.igctools import run_pipeline
from metaquery.src.utils import command, run_R_analyses, report_job, export
from metaquery.src.search import report_by_name


def launch_job(args):
    flag = run_pipeline(args)
    if flag == "DONE":
        run_R_analyses(args)
        report_job(args)
        export(args)
    return flag


def main():
    p = argparse.ArgumentParser(prog="metaquery ", description='Run metaquery')
    p.add_argument('--search_by_sequence', action='store_true', default=False)
    p.add_argument('--search_by_name', action='store_true', default=False)
    p.add_argument("--job_yaml", required = True, type=str, help="Path to job yaml")

    p.add_argument("--query", type=str, help="Search by Sequence: path to query input file")
    p.add_argument('--search_name', dest='search_name', type=str, help="Search by NAME")

    _args = p.parse_args()

    # Read in job.yaml for job_id, outdir
    job_yaml_fp = _args.job_yaml
    assert os.path.exists(job_yaml_fp), f"Provided JOB YAML doesn't exist."
    with open(job_yaml_fp) as f:
        form = yaml.safe_load(f)
    job_id = form["job_id"]
    base_dir = form['outdir']

    if _args.search_by_sequence:
        print("Start time: %s for JOB ID %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), job_id))

        query_fp = _args.query
        outdir = f"{base_dir}/metaquery_output_{job_id}"
        tempdir = f"{outdir}/temp"
        form["outdir"] = outdir
        form["tempdir"] = tempdir
        args = get_args(form)
        print(f"\n{json.dumps(args, indent=4)}\n")

        if os.path.exists(outdir):
            print(f"WARNING: {outdir} exists. DELETE.")
            command(f"rm -rf {outdir}")
        command(f"mkdir -p {outdir}")
        command(f"cp {job_yaml_fp} {outdir}/job.yaml")
        command(f"cp {query_fp} {outdir}/query.fasta")
        command(f"mkdir -p {tempdir}")

        flag = launch_job(args)
        if flag == "EMPTY":
            print("EMPTY BLAST RESULTS")
        if flag == "DONE":
            command(f"rm -rf {tempdir}")
            command(f"rm -f {outdir}/job.yaml")
            command(f"rm -f {outdir}/query.fasta")
        print("End time: %s for JOB ID %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), form["job_id"]))
    elif _args.search_by_name:
        search_term1 = _args.search_name.replace(" ", "_")
        if job_id == "":
            search_hash = md5(search_term1.encode('utf-8')).hexdigest()[-6:]
            job_id = f"{search_term1}_{search_hash}"
        outdir = f"{base_dir}/metaquery_output_{job_id}"
        if os.path.exists(outdir):
            print(f"WARNING: {outdir} exists. DELETE.")
            command(f"rm -rf {outdir}")
        command(f"mkdir -p {outdir}")
        args = {"job_id": job_id, "search_name": _args.search_name}
        args["outdir"] = outdir
        print(args)
        flag = report_by_name(args)
        if flag == "EMPTY":
            print("EMPTY BLAST RESULTS")


if __name__ == "__main__":
    main()
