import threading
import pdb

def tosql(df, *args, **kargs):
    CHUNKSIZE = 1000
    INITIAL_CHUNK = 100
    if len(df) > CHUNKSIZE:
        df.iloc[:INITIAL_CHUNK, :].to_sql(*args, **kargs)
    if kargs['if_exists'] == 'replace':
        kargs['if_exists'] = 'append'
    workers = []
    #pdb.set_trace()
    for i in range((len(df) - INITIAL_CHUNK)/CHUNKSIZE):
        t = threading.Thread(target=lambda: df.iloc[INITIAL_CHUNK+i*CHUNKSIZE:INITIAL_CHUNK+(i+1)*CHUNKSIZE, :].to_sql(*args, **kargs))
        t.start()
        workers.append(t)
    if len(df) <= INITIAL_CHUNK:
        print "------------ Same as df.to_sql"
        df.to_sql(*args, **kargs)
    else:
        print "------------ child threading method"
        df.iloc[INITIAL_CHUNK+(i+1)*CHUNKSIZE:, :].to_sql(*args, **kargs)
        [t.join() for t in workers]