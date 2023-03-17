## 2023-03-17

# libraries
import os, time, sys, urllib2, subprocess, cgi, cgitb, tempfile
import sqlite3
from collections import defaultdict
from metaquery.src.model import config, temp_dirm get_Rscript
from metaquery.src.igctools import sqlite3_connect


cgitb.enable()


def search_results_html(message, table):
    print("""
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="description" content="">
        <meta name="author" content="">
        <title>MetaQuery</title>

        <!-- Alex: Minified DataTable files downloaded from a CDN! -->
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/s/bs-3.3.5/jq-2.1.4,jszip-2.5.0,dt-1.10.10,b-1.1.0,b-html5-1.1.0,fc-3.2.0,fh-3.1.0,sc-1.4.0/datatables.min.css"/>
        <script type="text/javascript" src="https://cdn.datatables.net/s/bs-3.3.5/jq-2.1.4,jszip-2.5.0,dt-1.10.10,b-1.1.0,b-html5-1.1.0,fc-3.2.0,fh-3.1.0,sc-1.4.0/datatables.min.js"></script>

        <!-- Bootstrap core CSS -->
        <link href="css/bootstrap.min.css" rel="stylesheet">

        <!-- Custom styles for this template -->
        <link href="jumbotron-narrow.css" rel="stylesheet">

        <!-- Hovering help text -->
        <link href="css/hover-help-text.css" rel="stylesheet">

        <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
        <!--[if lt IE 9]>
          <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
          <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
        <![endif]-->
      </head>

    <body>
    <div class="container">
        <!-- Navbar -->
        <div class="header clearfix">
        <nav>
            <ul class="nav nav-pills pull-right">
                <li role="presentation"><a href="../index.html">Home</a></li>
                <li role="presentation"><a href="/cgi-bin/list_jobs.py">Jobs</a></li>
                <li role="presentation"><a href="/cgi-bin/about.py">About</a></li>
                <li role="presentation"><a href="../faq.html">FAQ</a></li>
                <li role="presentation"><a href="../downloads.html">Downloads</a></li>
                <li role="presentation"><a href="../contact.html">Contact</a></li>
            </ul>
        </nav>
        <h4 class="text-muted">MetaQuery: quantitative analysis of the human gut microbiome</h4>
        </div>
        <!-- Jumbotron -->
        <div class="jumbotron">
        <h2>Search results</h2>
        <p class="lead">Listing of taxa and functions that matched your search terms</p>
        </div>
        %s
        <!-- Tables -->
        %s
        <!-- Footer -->
        <br>
        <footer class="footer">
          <hr/>
          <ul class="nav nav-pills pull-left">
            <li><a href="http:///www.docpollard.org">Pollard Lab</a></li>
            <li><a href="contact.html">Contact</a></li>
          </ul>
        </footer>
    </div>

    <SCRIPT>$(document).ready(function(){$('#table').DataTable({
        "order": [],
        "scrollY":"500px",
        "scrollCollapse":true,
        "scrollX": true,
        "paging":false,
        "autoWidth":false,
        "fixedHeader":{header:false,footer:false},
        "deferRender":true})});
    </SCRIPT>

    <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
    <script src="js/ie10-viewport-bug-workaround.js"></script>
    </body>
    </html>
    """ % (message, table))
    exit()


def build_table(rows, id = "table"):
    table="<table id=%s class='table table-striped table-bordered' cellspacing='0'>" % id
    table += '<thead><tr>'
    table += ''.join(['<th> %s </th>' % i[0] for i in cursor.description])
    table += '</tr></thead>'
    table += '<tbody>'
    for row in rows:
        table += '<tr>'
        for v in row:
            #table += "<td style='text-align: center'>%s</td>" % v
            table += '<td>%s</td>' % v
        table += '</tr>'
    table += '</tbody></table>'
    return table


#################### FROM report_by_name.py
def success_html(args):
    return("""
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <!-- The above 3 meta tags *must* come first in the head; any other head content must come *after* these tags -->
        <meta name="description" content="">
        <meta name="author" content="">

        <title>MetaQuery</title>

        <!-- DataTables -->
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/s/bs-3.3.5/jq-2.1.4,jszip-2.5.0,dt-1.10.10,b-1.1.0,b-html5-1.1.0,fc-3.2.0,fh-3.1.0,sc-1.4.0/datatables.min.css"/>
        <script type="text/javascript" src="https://cdn.datatables.net/s/bs-3.3.5/jq-2.1.4,jszip-2.5.0,dt-1.10.10,b-1.1.0,b-html5-1.1.0,fc-3.2.0,fh-3.1.0,sc-1.4.0/datatables.min.js">
        </script>

        <!-- Bootstrap core CSS -->
        <link href="css/bootstrap.min.css" rel="stylesheet">

        <!-- Custom styles for this template -->
        <link href="jumbotron-narrow.css" rel="stylesheet">

        <!-- Hovering help text -->
        <link href="css/hover-help-text.css" rel="stylesheet">

        <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
        <!--[if lt IE 9]>
          <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
          <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
        <![endif]-->
      </head>

        <!-- Body -->
        <body>
        <div class="container">

        <!-- Navbar -->
        <div class="header clearfix">
        <nav>
        <ul class="nav nav-pills pull-right">
        <li role="presentation"><a href="../../index.html">Home</a></li>
        <li role="presentation"><a href="../../cgi-bin/list_jobs.py">Jobs</a></li>
        <li role="presentation"><a href="../../cgi-bin/about.py">About</a></li>
        <li role="presentation"><a href="../../faq.html">FAQ</a></li>
        <li role="presentation"><a href="../../downloads.html">Downloads</a></li>
        <li role="presentation"><a href="../../contact.html">Contact</a></li>
        </ul>
        </nav>
        <h4 class="text-muted">MetaQuery: quantitative analysis of the human gut microbiome</h4>
        </div>

        <!-- Jumbotron -->
        <div class="jumbotron">
        <h2>Results</h2>
        <p class="lead">Estimated abundances and results from statistical analyses</p>
        </div>

        <!-- Tables -->
        <h4 id="job_details">Job details:</h4>

        Query type: %(type)s <br>
        Database: %(database)s <br>
        Level: %(level)s <br>
        Name: %(link_out)s <br>
        Description: %(description)s <br>
        <br><a class="btn btn-primary btn-block" href="/cgi-bin/export.py?type=%(type)s&db=%(database)s&level=%(level)s&name=%(name)s&plotdir=%(plotdir)s">
        <b>Click here to download results</b></a>
        <hr/>

        <h4>The abundance of %(name)s across gut microbiome samples:</h4>
        <ul>
        <li>
        For taxonomic groups (e.g. species), <i><b>abundance</b></i> is defined as the proportion of cells that are from a taxonomic group<br>
        For functional groups (e.g. gene families), <i><b>abundance</b></i> is defined as the average copy-number of the function per cell<br>
        </li>
        <li>
        <b>Left:</b>
        the abundance of %(name)s was estimated across human gut metagenomes<br>
        Samples with an abundance of zero were assigned the smallest non-zero value
        </li>
        <li>
        <b>Right:</b>
        the average abundance of %(name)s was compared to the average abundance
        of other groups at the same functional or taxonomic level<br>
        </li>
        </ul>
        %(abundance_plot)s
        <hr/>

        <h4>The prevalence of %(name)s across gut microbiome samples:</h4>
        <ul>
        <li>
        <i><b>Prevalence</b></i>
        is defined at the percent of samples where %(name)s is found
        </li>
        <li>
        <b>Left:</b>
        the prevalence of %(name)s was estimated across human gut metagenomes at different abundance thresholds<br>
        </li>
        <li>
        <b>Right:</b>
        the prevalence of %(name)s at a minimum abundance of 0.001 was compared to the prevalence
        of other groups at the same functional or taxonomic level.<br>
        </li>
        </ul>
        %(prevalence_plot)s
        <hr/>

        <h4>Association of %(name)s abundance with clinical phenotypes:</h4>
        <ul>
        <li>
        <a href="https://en.wikipedia.org/wiki/Mann-Whitney_U_test">Wilcoxon rank-sum tests</a>
        were performed to determine if the abundance of %(name)s was different between cases and controls for several diseases (see table)
        </li>
        <li>
        For each disease, case and control individuals were selected from the same country and individuals with co-morbities were excluded<br>
        See the <a href='./about.py#metagenomes'>documentation</a> for more information on these cohorts
        </li>
        <li>
        <b>p_value</b> indicates whether there is a significant difference in the abundance of %(name)s between cases and controls<br>
        <b>rank</b> and <b>percentile</b> indicate how the p_value for %(name)s compares to other functional or taxonomic groups<br>
        For example, a percentile of 5.0 indicates your p_value was more significant than 95%% of other functions or taxa
        </li>
        </ul>

        <h4>Boxplots:</h4>
        <div id="myCarousel" class="carousel slide" data-ride="carousel" data-interval="false">
        <!-- Wrapper for slides -->
        <div class="carousel-inner" role="listbox">
        <div class="item active">
          <img style="display: block; margin: 0 auto" src="/plot/%(tempdir)s/%(name)s.Ulcerative colitis.Spain.png">
        </div>
        <div class="item">
          <img style="display: block; margin: 0 auto" src="/plot/%(tempdir)s/%(name)s.Crohns disease.Spain.png">
        </div>
        <div class="item">
          <img style="display: block; margin: 0 auto" src="/plot/%(tempdir)s/%(name)s.Obesity.Denmark.png">
        </div>
        <div class="item">
          <img style="display: block; margin: 0 auto" src="/plot/%(tempdir)s/%(name)s.Type II diabetes.China.png">
        </div>
        <div class="item">
          <img style="display: block; margin: 0 auto" src="/plot/%(tempdir)s/%(name)s.Type II diabetes.Denmark.png">
        </div>
        <div class="item">
          <img style="display: block; margin: 0 auto" src="/plot/%(tempdir)s/%(name)s.Type II diabetes.Sweden.png">
        </div>
        <div class="item">
          <img style="display: block; margin: 0 auto" src="/plot/%(tempdir)s/%(name)s.Liver cirrhosis.China.png">
        </div>
        <div class="item">
          <img style="display: block; margin: 0 auto" src="/plot/%(tempdir)s/%(name)s.Rheumatoid arthritis.China.png">
        </div>
        <div class="item">
          <img style="display: block; margin: 0 auto" src="/plot/%(tempdir)s/%(name)s.Colorectal cancer.Austria.png">
        </div>
        </div>
        <!-- Left and right controls -->
        <a class="left carousel-control" href="#myCarousel" role="button" data-slide="prev">
        <span class="glyphicon glyphicon-chevron-left" aria-hidden="true"></span>
        <span class="sr-only">Previous</span>
        </a>
        <a class="right carousel-control" href="#myCarousel" role="button" data-slide="next">
        <span class="glyphicon glyphicon-chevron-right" aria-hidden="true"></span>
        <span class="sr-only">Next</span>
        </a>
        </div>
        <br>

        <h4>Statistics:</h4>

        %(pheno_table)s
        Click on arrows to sort table data. Shift+click to sort by multiple columns.
        <hr/>

        <h4> Citation:</h4>
        Nayfach S, Fischbach MA, Pollard KS.
        MetaQuery: a web server for rapid annotation and quantitative analysis of specific genes in the human gut microbiome.
        Bioinformatics 2015;31(14).
        doi:<a href="http://dx.doi.org/10.1093/bioinformatics/btv382">10.1093/bioinformatics/btv382</a>
        <hr/>

        <!-- Footer -->
        <footer class="footer">
        <ul class="nav nav-pills pull-left">
        <li><a href="http://www.docpollard.org/">Pollard Lab</a></li>
        <li><a href="../../contact.html">Contact</a></li>
        </ul>
        </footer>

        </div>

    <SCRIPT>$(document).ready(function(){$('#pheno').DataTable({
        "order":[],
        "scrollX":true,
        "scrollY":"400px",
        "scrollCollapse":true,
        "searching": false,
        "paging":false,
        "fixedHeader":{header:false,footer:false}})});
    </SCRIPT>

    <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
    <script src="js/ie10-viewport-bug-workaround.js"></script>
    </body>
    </html>
    """ % args)


def fetch_results(cursor):
    fields = [_[0] for _ in cursor.description]
    for record in cursor.fetchall():
        yield dict([(x,y)for x,y in zip(fields, record)])


def make_plots(args):
    if args['mean_abundance'] > 0:
        plotdir = args.plotdir
        Rdir = get_Rscript()['plot_by_name']
        pfunc_dir = get_Rscript()["pfunc"]
        local_db = config['sqlite_db']
        command = f"Rscript {Rdir} {args.type} {args.database} {args.level} {args.name} {plotdir} {local_db} {pfunc_dir}"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        ## Specify the local path
        args['abundance_plot'] = f"{plotdir}/{args.name}.abundance.png" #<--- "/plot/%(tempdir)s/%(name)s.abundance.png"
        args['prevalence_plot'] = f"{plotdir}/{args.name}.prevalence.png"
        #args['abundance_plot'] = '<br><img style="display: block; margin: 0 auto" src="/plot/%(tempdir)s/%(name)s.abundance.png" align="middle"><br><br>' % args
        #args['prevalence_plot'] = '<br><img style="display: block; margin: 0 auto" src="/plot/%(tempdir)s/%(name)s.prevalence.png" align="middle"><br><br>' % args
    else:
        args['abundance_plot'] = 'No data! The selected function/taxa was not found in any sample.'
        args['prevalence_plot'] = 'No data! The selected function/taxa was not found in any sample.'
    return args


def build_pheno_talbe(cursor, args):


if __name__ == '__main__':

    p = argparse.ArgumentParser(prog="search ", description='search by name')
    p.add_argument('--search_name', dest='search_name', type=str, help="Search by NAME")

    conn, cursor = sqlite3_connect(config['sqlite_db'])
    search_name = args.search_name.replace(" ", "_")

    form = cgi.FieldStorage() #<-- maybe we don't need this term anymore

    search_term1 = "Bacteroides vulgatus"
    #search_term1 = "ABC Transporter"
    #search_term1 = "K00001"

    search_term1 = form.getvalue('search_term')
    search_term2 = search_term1.replace(' ', '_')

    cursor.execute("SELECT type, database, level, name, description FROM annotations WHERE name like ? or name like ? or description like ?", ('%'+search_term1+'%', '%'+search_term2+'%', '%'+search_term1+'%'))
    _rows = cursor.fetchall()

    # let's ignore the special meaning of double quote for now.
    rows = []
    dict_of_args = defaultdict(dict)
    for type, database, level, name, description in _rows:
        # TODO: check if we can remove calling report_by_name.py within the web
        rows.append(("<a href='report_by_name.py?type=" + type + "&db=" + database + "&level=" + level + "&name=" + name + "'><b>Report</b></a>", ))
        ## Move report_by_name::fetch_args here
        myargs = dict(zip(["type", "databasee", "level", "name"],[type, database, level, name]))
        # add abundance metric
        if myargs['type'] == 'taxa': myargs['metric'] = 'proportion of cells'
        else: myargs['metric'] = 'gene copies per cell'
        # link to external databases
        if myargs['database'] == 'kegg':
            html = "http://www.genome.jp/dbget-bin/www_bget?%s" % myargs['name']
            myargs['link_out'] = "<a target='_blank' href='%s'>%s</a>" % (html, myargs['name'])
        elif myargs['database'] == 'eggnog':
            html = "http://eggnog.embl.de/version_3.0/cgi/search.py?search_term_0=%s&search_species_0=-1" % myargs['name']
            myargs['link_out'] =  "<a target='_blank' href='%s'>%s</a>" % (html, myargs['name'])
        else:
            myargs['link_out'] = myargs['name']
        # add other info from annotations table
        cursor.execute("SELECT * from annotations WHERE database = ? AND level = ? AND name = ?", (myargs['database'], myargs['level'], myargs['name']))
        for row in fetch_results(cursor):
            for field, value in row.items():
                myargs[field] = value
        print(f"search::fetch_args::myargs: {myargs}")
        ## HERE: we can also handle the output file
        curr_outdir = f"temp_dir/{search_name}" #<--- TODO: should this be a jobid? if so, how to pass the parameter?
        myargs['tempdir'] = f"temp_dir/{search_name}" #<---- why not call it outdir ...
        myargs['plotdir'] = f"{temp_dir}/htdocs/plot"
        tempfile.mkdtemp(dir = myargs['plotdir'])
        args = make_plots(args)
        print(f"after making plots args: {args}")
        ############# build_pheno_table
        cursor.execute("SELECT phenotype, country, case_n, ctrl_n, case_mean, ctrl_mean, p_value, rank, percentile from pheno_tests WHERE type = ? AND database = ? AND level = ? AND name = ?", (type, database, level, name))
        tables = {}
        pheno_data = cursor.fetchall()
        pheno_table = []
        for row in pheno_data:
            case_mean = '%s' % float('%.2g' % row[4])
            ctrl_mean = '%s' % float('%.2g' % row[5])
            p_value = '%s' % float('%.2g' % row[6])
            percentile = '%s' % float('%.2g' % row[8])
            pheno_table.append((row[0],row[1],row[2], row[3], case_mean, ctrl_mean, p_value, row[7], percentile))
        tables['pheno_table'] = pheno_table
        with open(f"{curr_outdir}/pheno_table.tsv", "w") as stream:
            for row in pheno_table:
                stream.write('\t'.join([str(v) for v in row])+'\n')
        # Let's write to the same local directory for now. And check back later with the front end.
        #dict_of_args[] = myargs # not sure we need to save it, which was passed onto

    table = build_table(rows)
    print(table)

    if len(rows):
        message = """
            <p style='font-size:20px'>
            Showing <b>%s</b> results for search term <b>'%s'</b><br>
            Click on table entries for a full report
            </p><br>""" % (len(rows), search_term1)
    else:
        message = """
            <p style='font-size:20px'>
            There are no results for search term <b>'%s'</b>
            </p><br>""" % search_term1

    # TODO: comment off for now. Check with
    #search_results_html(message, table)
