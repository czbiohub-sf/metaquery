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
from metaquery.src.search import report_by_name


def launch_job(args):
    flag = run_pipeline(args)
    if flag == "DONE":
        run_R_analyses(args)
        report_job(args)
        export(args)



def main():
    p = argparse.ArgumentParser(prog="metaquery ", description='Run metaquery')
    p.add_argument('--search_by_sequence', action='store_true', default=False)
    p.add_argument('--search_by_name', action='store_true', default=False)

    p.add_argument("--job_yaml", type=str, help="Path to job yaml")
    p.add_argument("--query", type=str, help="Path to query fasta file")

    p.add_argument('--search_name', dest='search_name', type=str, help="Search by NAME")

    args = p.parse_args()

    if args.search_by_sequence:
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
    elif args.search_by_name:
        report_by_name(args)


if __name__ == "__main__":
    main()
