import sqlite3

dbpath = "/mnt/cz/metaquery_sqlites3.db"
conn = sqlite3.connect(dbpath)
cursor = conn.cursor()

cursor.execute("SELECT * FROM xx WHERE xx = '%s'" % symbol)
cursor.execute("SELECT * FROM xx WHERE xx = ?", (symbol_name, )).fetchall()

#RUN
name = "ERR321150"

#SAMPLE
name = "V1.UC54.0"

#HOMOLOG
id = "2844770"
fasta = "/mnt/cz/20210802_metaquery_local/MetaQuery_compute/db/fasta/IGC_protein.fa"
molecule_type = "protein"


cursor.commit()
cursor.close()
