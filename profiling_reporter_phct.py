template = """
<body>
<div id="container"></div>
<script>
{}
</script>
</body>
"""



from lib import profiling_report_pyhct as r
from lib import param_dict as pr
from optparse import OptionParser
import pdb, sys
from pyhighcharts import Chart, ChartTypes

def create_nightly_report():
    params = {}
              
    parser = OptionParser()
    parser.add_option("--dut-backend", "-d", dest="dut_backend", help="the specified table that will be used")
    parser.add_option("--ref-backend", "-r", dest="ref_backend", default=None, help="the changelist as reference value")

    parser.add_option("--dut-cl", "-a", dest="dut_cl", default=None, help="the average line in expectation")
    parser.add_option("--ref-cl", "-s", dest="ref_cl", default=None, help="the average line in expectation")
	
    parser.add_option("--db-name", "-n", dest="db_name", default='test1', help="the name of the database which contains the specified table")
    parser.add_option("--db-host", dest="db_host", default='10.204.7.188', help="the host of database")
    parser.add_option("--db-login", dest="db_login", default="root;root", help="the username and password of database, divided by ';'")
	
    parser.add_option("--statistic", dest="statistic", action="store_true", default=False, help="get the statistic file for the given table")

    (options, args) = parser.parse_args()
    args={'dut_backend':options.dut_backend, \
    'ref_backend':options.ref_backend, \
    'dut_cl':options.dut_cl, 'ref_cl':options.ref_cl, \
    'db_name':options.db_name, \
    'db_host':options.db_host, \
    'db_login':options.db_login }
    
    statistic = options.statistic

    dut_backend = {'dut_backend':args['dut_backend']} 
    ref_backend = {'ref_backend':args['ref_backend']}
    dut_cl = {'dut_cl':args['dut_cl']} 
    ref_cl = {'ref_cl':args['ref_cl']}
	
	
    db_name = {'db_name':args['db_name']}    
    db_host = {'db_host':args['db_host']}
    db_login = {'db_login':args['db_login']}
    

    params.update(dut_backend)
    params.update(ref_backend)
    params.update(dut_cl)
    params.update(ref_cl)
    params.update(db_name)    
    params.update(db_host)    
    params.update(db_login)     
   
    
    
    report = r.db_report(params)
    if statistic:
        perf_data = report.generate_statistic()
    #else:
        #params.update(cfg_file)
        #report.gen_history_graphs()
    #print report.warning_notification
    
    print perf_data  
    # chart = Chart()    
    # data = []    
    # for key, value in perf_data.items():
        # if value == 0:
            # continue
        # data.append([key,value]) 
        
    # print data     
    # chart.add_data_series(ChartTypes.pie, data, name="Numbers of Function")

    # title = 'Performance Comparison: ' + options.dut_cl + ' v.s. ' + options.ref_cl
    # chart.set_title(title)
    # subtitle = 'Backend: ' + options.dut_backend + ' v.s. ' + options.ref_backend
    # chart.set_subtitle(subtitle)

    # template.format(chart.script())
    # html_name = '1.11_vs_1.10/' + options.dut_cl + '-' + options.dut_backend + '_vs_' + options.ref_cl + '-' + options.ref_backend
    # chart.show(html_name)

    return #report.warning_notification
 
   
if __name__ == '__main__':
    if create_nightly_report():
        sys.exit(1)
    
