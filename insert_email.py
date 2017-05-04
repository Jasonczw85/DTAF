import MySQLdb as DB
import copy

from lib.test_send_mail import send_mail
from database.rel_profile import schema0

from lib.profiler_log_db_opr import Profiler
import pdb
import sys

db_params = \
{
    'db_host' : '10.204.7.188',
    'db_login' : "root;root",
    'db_name' : 'test1'
}


table_name = "Failed_CL_EmailNotification"
db = schema0(db_params)

#select * from Failed_CL_EmailNotification where emailed="NO";

profileRecordID_q = ' '.join(['select changelist,author from %s where' % (table_name),
                              'emailed = "NO"' 
                              ]
                             )
ID_CL_pairs = db.query(profileRecordID_q)
print ID_CL_pairs

for email_dict in ID_CL_pairs:
    print email_dict['changelist'], email_dict['author'] 
    mailto = email_dict['author'] 
    mail_sub = 'Performance Issue on Changelist %s' % (email_dict['changelist'])
    mail_content = "Hi %s \n \
The changelist %s introduced the performance drops, please go to database test1 ip:10.204.7.188 with MYSQL front and look at the schema xcl%s. Then please ack this email notification \
in schema Failed_CL_EmailNotification, thanks!" \
% (mailto, email_dict['changelist'], email_dict['changelist'])
    send_mail(mailto, mail_sub, mail_content)
    db.update_email_status(email_dict['changelist'])

