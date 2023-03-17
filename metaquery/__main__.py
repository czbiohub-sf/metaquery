#!/usr/bin/env python3

import os
import time
import argparse
import tempfile
import yaml
import json

from metaquery.src.model import get_args
from metaquery.src.igctools import run_pipeline
from metaquery.src.utils import command, run_R_analyses, report_job, export


def launch_job(args):
    flag = run_pipeline(args)
    if flag == "DONE":
        run_R_analyses(args)
        report_job(args)
        export(args)



def main():
    p = argparse.ArgumentParser(prog="metaquery ", description='Run metaquery')
    p.add_argument("--job_yaml", required=True, type=str, help="Path to job yaml")
    p.add_argument("--query", required=True, type=str, help="Path to query fasta file")
    args = p.parse_args()

    raw_yaml_fp = args.job_yaml
    raw_seq_fp = args.query

    assert os.path.exists(raw_yaml_fp), f"Provided YAML doesn't exist."
    with open(raw_yaml_fp) as f:
        form = yaml.safe_load(f)
    print("Start time: %s for JOB ID %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), form["job_id"]))

    outdir = f"{form['outdir']}/{form['job_id']}"
    tempdir = f"{outdir}/temp"
    form["outdir"] = outdir
    form["tempdir"] = tempdir
    args = get_args(form)

    if os.path.exists(outdir):
        print(f"WARNING: {outdir} exists. DELETE.")
        command(f"rm -rf {outdir}")

    print(f"\n{json.dumps(args, indent=4)}\n")
    command(f"mkdir -p {outdir}")
    command(f"cp {raw_yaml_fp} {outdir}/job.yaml")
    command(f"cp {raw_seq_fp} {outdir}/query.fasta")
    command(f"mkdir -p {tempdir}")

    launch_job(args)
    print("End time: %s for JOB ID %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), form["job_id"]))


if __name__ == "__main__":
    main()
