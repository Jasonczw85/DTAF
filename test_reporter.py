from lib import test_report as r
from lib import param_dict as pr
from optparse import OptionParser
import pdb, sys

def create_nightly_report():
    params = {'c_user': 'sa-tdglab',
              'c_space':'consEng',
              'c_page': 'Zeus Nightly Profiling',
              'test_category': 'FFT Bench',
              'di_database_table': 'fft_bench_test',
              'node': 'ddpi_enc_process',
              'xml_reports': ['config/zeus_comparisons.xml', 'config/zeus_projects.xml'],
              }
              
    parser = OptionParser()
    parser.add_option("--config-file", "-c", dest="cfg_file", help="the specified configure file for di algorithm") 
    parser.add_option("--table-name", "-t", dest="table_name", help="the specified table that will be used")
    parser.add_option("--output-path", "-o", dest="output_path", help="the specified path that will generate the output file")
    parser.add_option("--base-line", "-b", dest="base_line", default=None, help="the changelist as reference value")
    parser.add_option("--thresh-hold", "-s", dest="thresh_hold", help="the threshold in expectation")
    parser.add_option("--avg-line", "-a", dest="avg_line", help="the average line in expectation")
    parser.add_option("--specify-base-line", "-i", dest="specify_base_line", help="the specified base line in expectation")
    parser.add_option("--disable-upload", "-d", dest="disable_upload", action="store_true", default=False, help="disable upload to confluence page")
    parser.add_option("--trigger-binary-search", "-T", dest="trigger_bs", action="store_true", default=False, help="trigger-binary-search")
    parser.add_option("--gen-csv", "-g", dest="gen_csv", default=None, help="enable to generate report in csv format")
    parser.add_option("--db-name", "-n", dest="db_name", default='test1', help="the name of the database which contains the specified table")
    parser.add_option("--db-host", dest="db_host", default='10.204.7.188', help="the host of database")
    parser.add_option("--db-login", dest="db_login", default="root;root", help="the username and password of database, divided by ';'")
    parser.add_option("--disable-paint", "-p", action="store_true", dest="disable_paint", help="disable paint")
    parser.add_option("--statistic", dest="statistic", action="store_true", default=False, help="get the statistic file for the given table")

    (options, args) = parser.parse_args()
    args={'cfg_file':options.cfg_file, 'table_name':options.table_name, \
    'output_path':options.output_path, 'base_line':options.base_line, \
    'thresh_hold':options.thresh_hold, 'avg_line':options.avg_line, \
    'specify_base_line':options.specify_base_line, \
    'disable_upload':options.disable_upload, \
    'trigger_bs':options.trigger_bs, \
    'gen_csv':options.gen_csv, \
    'db_name':options.db_name, \
    'db_host':options.db_host, \
    'db_login':options.db_login, \
    'disable_paint':options.disable_paint}
    
    statistic = options.statistic

    table_name_params = {'table_name':args['table_name']} 
    output_params = {'output_path':args['output_path']}
    base_line = {'base_line':args['base_line']}
    thresh_hold = {'thresh_hold':args['thresh_hold']}
    avg_line = {'avg_line':args['avg_line']}    
    specify_base_line = {'specify_base_line':args['specify_base_line']}
    cfg_file = {'cfg_file':args['cfg_file']}
    disable_upload = {'disable_upload':args['disable_upload']}
    trigger_bs = {'trigger_bs':args['trigger_bs']}
    gen_csv = {'gen_csv':args['gen_csv']}
    db_name = {'db_name':args['db_name']}    
    db_host = {'db_host':args['db_host']}
    db_login = {'db_login':args['db_login']}
    disable_paint = {'disable_paint':args['disable_paint']}
    
    params.update(pr.param_dict(args['cfg_file']))

    params.update(table_name_params)
    params.update(output_params)
    params.update(base_line)
    params.update(specify_base_line)
    params.update(cfg_file)
     

    
    if thresh_hold['thresh_hold'] is None:
        thresh_hold['thresh_hold'] = 10
    
    params.update(thresh_hold)
    params.update(avg_line)
    
    params.update(disable_upload)   
    params.update(gen_csv)
    params.update(trigger_bs)
    params.update(db_name)    
    params.update(db_host)    
    params.update(db_login)
    params.update(disable_paint)    

    report = r.db_report(params)
    if statistic:
        report.generate_statistic()
    else:
        params.update(cfg_file)
        report.gen_history_graphs()
    #print report.warning_notification
    return report.warning_notification
 

if __name__ == '__main__':
    if create_nightly_report():
        sys.exit(1)
    
