# encoding: UTF-8
from eventEngine import *
from eventType import *
from mysqlengipinfo import mysql_eng_signal
from mysqlops import *


########################################################################
class MySqlEngine(EventEngine):

    def __init__(self, **kwargs):

        super(MySqlEngine, self).__init__(**kwargs)

        self.kwargs = kwargs
        self._put = Thread(target = self._run_put)
        self._timerSleep = 2

    def _run_put(self):
        while self._active_put:
            event = MySqlEvent(**self.kwargs)

            if event._df is not None:
                super(MySqlEngine, self)._put(event)
            
            self._df = None
            sleep(self._timerSleep)


########################################################################
class MySqlEvent(Event):

    def __init__(self, **kwargs):

        super(MySqlEvent, self).__init__(**kwargs)

        self._df = kwargs['dataframe']
        self._schemaName = kwargs['schemaName']
        self._strategyExec = kwargs['strategyExec']


#----------------------------------------------------------------------
#def test():
    # import sys
    # from datetime import datetime
    
    # def simpletest(event):
    #     print event.schemaName_
    #     print event.df_
    #     print event.type_
    # def savetomysqltest(event):
    #     save_to_mysql_test(event.df_, event.schemaName_, mysql_eng_signal)
    # def savetomysqlwrap(event):
    #     save_to_mysql_wrap(event.df_, event.schemaName_, mysql_eng_signal)       
        
    # argument = dict()
    # argument['schemaName'] = '1111test'
    # argument['funcName'] = test_gen_df
    # ee = EventEngine2(**argument)
    # ee.register(UPDATE_NAV_TO_ALIYUN, savetomysqlwrap)
    # ee.register(UPDATE_NAV_TO_ALIYUN, savetomysqltest)
    

    # ee.start()
    
    # print "Waiting 15s in main test"
    # sleep(15)

    # ee.stop()

# if __name__ == '__main__':
#     test()
