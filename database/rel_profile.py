import MySQLdb as DB
import copy

class profile_db(object):
    def __init__(self, dict_args):  
    
        db = dict_args["db_name"]
        host = dict_args["db_host"]
        [user, passwd] = dict_args["db_login"].split(";")
            
        self._db = DB.connect(user=user, 
                              host=host, 
                              passwd=passwd, 
                              db=db)
        self._cursor = self._db.cursor(cursorclass=DB.cursors.DictCursor)

        tbl_q = self.query('show tables')
        self._tables = {}
        for tbl_d in tbl_q:
            table = tbl_d.values()[0]
            self._tables[table] = {}
            attr_q = self.query('describe %s' % table)
            for attr_d in attr_q:
                self._tables[table][attr_d['Field']] = copy.deepcopy(attr_d)

    def _display_results(self, results, gap=18):
        if len(results) == 0:
            print '()'
            return

        width = {}
        separator = 5
        line = '\n    '
        for col in results[0]:
            maxlen = len(col)
            for r in results:
                value = str(r[col])
                if len(value) > maxlen:
                    maxlen = len(value)
            segment = col + ' '*(maxlen+separator-len(col))
            if maxlen > gap:
                line = line + segment[:gap-1] + ' '
            else:
                line = line + segment
            width[col] = maxlen+separator
        print line[:len(line)-(maxlen+separator-len(segment))]

        for i, result in enumerate(results):
            line = '%d:  ' % (i+1)
            for col in result:
                value = str(result[col])
                segment = value + ' '*(width[col]-len(value))
                if width[col] > gap:
                    line = line + segment[:gap-1] + ' '
                else:
                    line = line + segment + ' '*(width[col]-len(segment))
            print line[:len(line)-(width[col]-len(segment))]

    def query(self, query, prnt=False, gap=25):
        ''' send a MySQL query to the database '''
        self._cursor.execute(query)
        results = self._cursor.fetchall()
        if prnt:
            self._display_results(results, gap)
        else:
            return results

    def insert(self, table, attrs, date=False):
        '''insert a record into 'table' using all of the values
        in 'attrs' whose keys are columns of 'table' '''

        # create record of only the attrs with fields in table
        record = {}
        for attr, attr_d in self._tables[table].items():
            if attr_d['Key'] == 'PRI':
                continue
            if attrs.has_key(attr):
                record[attr] = attrs[attr]       

        # generate insertion string for all applicable (field, value) pairs
        query = 'insert into %s ' % table
        fields = ''
        values = ''
        for key, value in record.items():
            fields = '%s, %s' % (fields, key)
            values = '%s, %s' % (values, repr(value))

        fields = '(' + fields[2:] + ')'
        values = ' values (' + values[2:] + ')'
        #pdb.set_trace()
        query = query + fields + values
        # execute insertion
        self._cursor.execute(query)
        return self._db.commit()

class schema0(profile_db):
    '''draft schema 0 for a Dolby profiling database''' 

    def insert_profile_table(self,
	                test_table_name, test_case_name,
			max_value, min_value, avg_value, unitperf,
                        cmd, backend, board, target, os, arch, changelist, compiler, glibc):#,
                    #cmd_perf, backend, target, os, arch, change_list,
                    #compiler, technology):
        record = {'test_case_name': test_case_name,
                  'max_value': max_value,
                  'min_value': min_value,
                  'avg_value': avg_value,
                  'unitperf': unitperf,
                  'cmd':cmd,
                  'backend':backend,
                  'board':board,
                  'target':target,
                  'os':os,
                  'arch':arch,
                  'changelist':changelist,
                  'compiler':compiler,
                  'glibc':glibc}

        self.insert(test_table_name, record, date=True)
    def _get_profileRecordID(self, buildRecordID, changelist):
        q = ' '.join(['select * from fft_bench_test',
                      'and changelist = %s' % changelist,
                      ]
                     )
        results = self.query(q)
        if len(results) > 1:
            raise Exception, 'multiple profileRecordID matches'
        elif len(results) == 0:
            return None
        else:
            return int(results[0]['profileRecordID'])
