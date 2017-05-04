import MySQLdb as DB
import copy
import sys

from database.rel_profile import schema0

from lib.profiler_log_db_opr import Profiler
import pdb


db_params = \
{
    'db_host' : '10.204.7.188',
    'db_login' : "root;root",
    'db_name' : 'test1'
}

db = schema0(db_params)

table_column = "( \
test_case char(128), \
backend char(40),  \
board char(40) default null,\
primary key(test_case, backend, board), \
author char(40) , \
algorithm char(40) , \
comment char(255) default null \
)"

table_name='a1112'
db.create_table(table_name, table_column)

cl_details = \
{
    'test_case': '333',
    'backend': '222',
    'board': 'cuibe2'  
}

db = schema0(db_params)
db.insert_cl_value(table_name, cl_details)


sys.exit(1)

email_table_column = "( \
changelist char(128), author char(40), \
emailed char(40) default null,\
ack char(40) default null, \
jira char(40) default null,\
comment char(40) default null \
)"
table_name_email = "Failed_CL_EmailNotification"
db = schema0(db_params)
db.create_table(table_name_email, email_table_column)


cl_details = \
{
    'changelist': '222000',
    'author': '222', 
}
db = schema0(db_params)
db.insert_value(table_name_email, cl_details)

changelist='222000'
db.update_email_status(changelist)


tch_table_column = "( \
test_case_name char(128), \
parent_test_case char(128) default null \
)"
table_name_tch = "TC_Hierarchy"
db = schema0(db_params)
db.create_table(table_name_tch, tch_table_column)

rvt_table_column = "( \
changelist char(128), \
tag char(40) default null, \
sprint char(40) default null,\
release_version char(40) default null\
)"
table_name_rvt = "Release_Version_Tag"
db = schema0(db_params)
db.create_table(table_name_rvt, rvt_table_column)



