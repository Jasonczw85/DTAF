from sqlalchemy import create_engine
import pandas as pd
from pandas.io import sql
from mysqlengipinfo import mysql_eng_signal, mysql_eng
from wrap_tosql import *
import time
import sys
import os

def save_to_mysql(df, schema, mysql_eng):
    engine = create_engine(mysql_eng)
    schema_name = schema
    print "Inserting data to db:%s\n" %schema_name
    df.to_sql(schema_name, engine, if_exists='append', index = False)

def save_to_mysql_profiling(df, schema, mysql_eng):
    schema_name = schema
    for sn in schema_name.split(','):
        save_to_mysql(df, sn, mysql_eng)
    df.to_csv('data.csv', columns=['test_case_name','max_value', 'min_value', 'avg_value'], index=False)
    print "Data stored at %s" % (os.path.join(os.getcwd(), 'data.csv'))

def save_to_mysql_compat(df_list, mysql_eng):
    for df in df_list:
        if 'compare_summary' in list(df):
            save_to_mysql(df, 'CompatTestSummary', mysql_eng)
        elif 'build_msg' in list(df):
            save_to_mysql(df, 'CompatBuildSummary', mysql_eng)
        elif 'test_api' in list(df):
            save_to_mysql(df, 'Compatibility', mysql_eng)

def save_to_mysql_test(df, schema, mysql_eng):
    engine = create_engine(mysql_eng)
    schema_name = schema
    print "Orig Method ---- Inserting data to db:%s\n" %schema_name
    start = time.time()
    df.to_sql(schema_name, engine, if_exists='append', index = False)
    print "orig consume: ", time.time() - start
    
def save_to_mysql_wrap(df, schema, mysql_eng):
    engine = create_engine(mysql_eng)
    schema_name = schema
    print "Wrapp Method ---- Inserting data to db:%s\n" %schema_name
    start = time.time()
    tosql(df, schema_name, engine, if_exists='append', index = False)
    print "wrap consume: ", time.time() - start
    
def save_to_mysql_monitor(df, schema, mysql_eng):
    engine = create_engine(mysql_eng)
    schema_name = schema
    df.to_sql(schema_name, engine, if_exists='replace')

def read_mysql_monitor(schema, mysql_eng, col_list):
    engine = create_engine(mysql_eng)
    schema_name = schema
    data = pd.read_sql_table(schema_name, engine, columns=col_list)
    return data

def read_mysql_query(sql, mysql_eng):
    engine = create_engine(mysql_eng)
    data = pd.read_sql_query(sql, engine)
    return data

# col_dict = {'columnA' : 'valueA', 'columnB' : 'valueB'}
# select query_col from schema where columnA=valueA and columnB=valueB
def read_mysql_select(schema, mysql_eng, col_dict, query_col):
    col_list = []
    for key in col_dict:
        col_list.append(key)
    col_list.append(query_col)
    data = read_mysql_monitor(schema, mysql_eng, col_list)

    for key, value in col_dict.items():
        data = data[data[key] == value]
    return data

def update_mysql(sql_s, mysql_eng):
    engine = create_engine(mysql_eng)
    sql.execute(sql_s, mysql_eng)

def read_mysql_table(schema, mysql_eng):
    engine = create_engine(mysql_eng)
    schema_name = schema
    data = pd.read_sql_table(schema_name, engine, columns=['test_case_name', 'max_value', 'min_value', 'avg_value', 'unitperf', 'cmd', 'backend', 'board', 'target', 'os', 'arch', 'changelist', 'compiler', 'updatetime', 'technology'])
    return data
    
    
def gen_df():
    df_sig_sign = pd.DataFrame(signal_dict_sign.items(), columns=['code', 'name'])
    
    return df_sig_sign


if __name__ == "__main__":

    schema_signal = 'panda_float_dct_bench_test'
    df = read_mysql_table(schema_signal, mysql_eng)
    print df
    #schema_signal = 'testsql_connection'
    #df = gen_df()
    #while(True):
        #save_to_mysql_test(df, schema_signal, mysql_eng_signal)
    
    
    