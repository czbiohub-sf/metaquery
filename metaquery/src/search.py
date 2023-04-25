## 2023-03-17 Chunyu Zhao

import os, time, sys, subprocess, cgi, tempfile
from pathlib import Path
import shutil
import sqlite3
from collections import defaultdict
from metaquery.src.model import config, temp_dir, get_Rscript
from metaquery.src.igctools import sqlite3_connect


def fetch_results(cursor):
    fields = [_[0] for _ in cursor.description]
    for record in cursor.fetchall():
        yield dict([(x,y)for x,y in zip(fields, record)])


def make_plots(args):
    if args['mean_abundance'] > 0:
        plotdir = args["plotdir"]
        Rdir = get_Rscript()['plot_by_name']
        pfunc_dir = get_Rscript()["pfunc"]
        local_db = config['sqlite_db']
        command = f"Rscript {Rdir} {args['type']} {args['database']} {args['level']} {args['name']} {plotdir} {local_db} {pfunc_dir}"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        ## Specify the local path
        args['abundance_plot'] = f"{plotdir}/{args['name']}.abundance.png"
        args['prevalence_plot'] = f"{plotdir}/{args['name']}.prevalence.png"
    else:
        args['abundance_plot'] = 'No data! The selected function/taxa was not found in any sample.'
        args['prevalence_plot'] = 'No data! The selected function/taxa was not found in any sample.'
    return args


def report_by_name(args):

    outdir = args["outdir"]
    job_id = args["job_id"]
    search_name = args["search_name"]

    conn, cursor = sqlite3_connect(config['sqlite_db'])
    search_term1 = search_name.replace(" ", "_")
    search_term2 = search_term1.replace(' ', '_')

    #search_term1 = "Bacteroides vulgatus"
    #search_term1 = "ABC Transporter"
    #search_term1 = "K00001"

    cursor.execute("SELECT type, database, level, name, description FROM annotations WHERE name like ? or name like ? or description like ?", ('%'+search_term1+'%', '%'+search_term2+'%', '%'+search_term1+'%'))
    rows = cursor.fetchall()

    # For each row of record, we would created a temp directory under the outdir directory
    nrows = len(rows)
    if nrows == 0:
        print(f"\nSEARCH BY NAME::EMPTY Results for search term {search_name}. Exit Now.")
        return "EMPTY" # equivalent to empty blast results
    else:
        print(f"\nShowing {nrows} results for search term {search_name}. Full report table can be downloaded.")

    index = 1
    list_of_rets = []
    for type, database, level, name, description in rows:
        print(f"\nSearching results for # {index}")
        index = index + 1

        ## Move report_by_name::fetch_args here
        myargs = dict(zip(["type", "database", "level", "name"],[type, database, level, name]))

        ## Output Directory
        plot_dir = tempfile.mkdtemp(dir=outdir)
        plot_name = os.path.basename(plot_dir)
        myargs['plotdir'] = plot_dir

        # Add abundance metric
        if myargs['type'] == 'taxa':
            myargs['metric'] = 'proportion of cells'
        else:
            myargs['metric'] = 'gene copies per cell'

        # Link to external databases
        if myargs['database'] == 'kegg':
            html = "http://www.genome.jp/dbget-bin/www_bget?%s" % myargs['name']
            myargs['link_out'] = html
        elif myargs['database'] == 'eggnog':
            html = "http://eggnog.embl.de/version_3.0/cgi/search.py?search_term_0=%s&search_species_0=-1" % myargs['name']
            myargs['link_out'] =  html
        else:
            myargs['link_out'] = myargs['name']

        # Add other info from annotations table
        cursor.execute("SELECT * from annotations WHERE database = ? AND level = ? AND name = ?", (myargs['database'], myargs['level'], myargs['name']))
        for row in fetch_results(cursor):
            for field, value in row.items():
                myargs[field] = value

        myargs = make_plots(myargs)

        # Update the full path of the plot into relative path
        myargs2 = myargs
        myargs2["mean_abundance"] = '%s' % float('%.2g' % myargs["mean_abundance"])
        myargs2["abundance_plot"] = plot_name + "/" + os.path.basename(myargs["abundance_plot"])
        myargs2["prevalence_plot"] = plot_name + "/" + os.path.basename(myargs["prevalence_plot"])
        myargs2.pop("plotdir")
        list_of_rets.append(myargs2)

        ############# build_pheno_table
        cursor.execute("SELECT phenotype, country, case_n, ctrl_n, case_mean, ctrl_mean, p_value, rank, percentile from pheno_tests WHERE type = ? AND database = ? AND level = ? AND name = ?", (type, database, level, name))
        pheno_data = cursor.fetchall()
        pheno_table = []
        for row in pheno_data:
            case_mean = '%s' % float('%.2g' % row[4])
            ctrl_mean = '%s' % float('%.2g' % row[5])
            p_value = '%s' % float('%.2g' % row[6])
            percentile = '%s' % float('%.2g' % row[8])
            pheno_table.append((row[0],row[1],row[2], row[3], case_mean, ctrl_mean, p_value, row[7], percentile))

        with open(f"{plot_dir}/pheno_table.tsv", "w") as stream:
            stream.write('\t'.join(['phenotype', 'country', 'case_n', 'ctrl_n', 'case_mean', 'ctrl_mean', 'p_value', 'rank', 'percentile']) + '\n')
            for row in pheno_table:
                stream.write('\t'.join([str(v) for v in row])+'\n')

    # Write main table to file
    header = list(list_of_rets[0].keys())
    with open(f"{outdir}/search_results.tsv", "w") as stream:
        stream.write('\t'.join(header) + '\n')
        for _arg in list_of_rets:
            stream.write('\t'.join(map(str, _arg.values())) + '\n')
    return "DONE"

if __name__ == '__main__':
    main()
