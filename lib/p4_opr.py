from P4 import P4,P4Exception
import os, sys, re, string, shutil, time, getpass, socket
import platform, random
import time,pdb
import logging

class P4_Ops(object):
    
    # This class is used to wrap perforce operations in python lib module,
    
    def __init__(self, **kwargs):    
        
        # Initialise the p4_ops object, import the p4_opr.py, and provide 
        # the kwargs, only depot is "must have". Give the kwargs as below:
        # kwargs={ 
            #'port': "$your_server:$your_port", (could leave this line blank)
            #'user': "$your_user_name",    (could leave this line blank)
            #'password': "$your_password", 
            #'client_name': "$your_client_name",  (could leave this line blank)
            #'client_root': "$folder_on_your_machine you want to save the download", 
            # (could leave this line blank)
            #'depot': "//depot/ger/dlb_intrinsics/main/dlb_intrinsics/dab/..." \
            #}
         # and then,
         # p4_test = P4_Ops(**kwargs)
           
        self.kwargs = kwargs

        self.logger = logging.getLogger('mylogger')
        self.logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        self._unshelve_cl = None
      
        try:
            self.p4 = P4()
            
        except P4Exception:
            for e in self.p4.errors:
                print "Perforce errors:", e 
                
        # Default server/user configuration if didn't give the parameters
        self.p4.user = "testlc"
        self.p4.password = "taC%g17#"
        self.p4.port = "Perforce-bjo.dolby.net:1666"
        self._namespace = self.gen_namespace()
        self._client_name = getpass.getuser() + '_' + self._namespace
        

        if platform.system() == "Windows":
            self._client_root = "c:\\" + self._namespace
        elif platform.system() == "Linux":
            self._client_root = os.path.expanduser('~') + '/' + self._namespace

        self._depot_excluded = ""

        if ('user' and 'password') in kwargs:
            self.p4.user = kwargs['user']
            self.p4.password = kwargs['password']

        if 'port' in kwargs:
            self.p4.port = kwargs['port']
   
        if 'client_name' in kwargs:
            self._client_name = kwargs['client_name']

        if 'client_root' in kwargs:
            self._client_root = kwargs['client_root']
         
        self._depot = kwargs['depot']
        if 'depot_excluded' in kwargs:
            self._depot_excluded = kwargs['depot_excluded']
        
        self.init_client_root_folder()
            
        try:                        # Catch exceptions with try/except
            self.p4.connect()       # Connect to the Perforce Server
            self.logger.debug("Using the client_root workspace::::::: %s" %self._client_root)
        except P4Exception:
            for e in self.p4.errors:
                print "Perforce errors:", e 
                
        self.logger.debug("DEBUG INFO: p4 status: %s" %self.p4) # return a string of connect status,


    def handle_p4_connection_exception(self, p4_cmd):
    
        # handler of the exception from p4 server "connection reset by peer"

        # p4.exception level = 2 by default, which handle both error and warning. set it to 1
        # to handle error only
        self.p4.exception_level = 1
        p4_exception = 0 
        print "P4 cmd exec is ", p4_cmd
        while True:        
            try:
                exec p4_cmd
            except P4Exception:
                for e in self.p4.errors:
                    print "Perforce errors:", e
                p4_exception += 1 
                if p4_exception < 20:
                    self.logger.debug("DEBUG INFO: Reconnecting ..... ")
                    time.sleep(20)
                    self.p4.disconnect()
                    self.logger.debug("DEBUG INFO: Resume from waiting for 20 secs ..... ")
                    self.p4.connect()
                    continue 
                else:
                    self.logger.debug("DEBUG INFO: timeout: Exit ..... ")
                    self.cleanup_remote_client()
                    self.p4.disconnect()
                    sys.exit(1)
            except Exception, excp:
                p4_exception = 1 
                self.logger.debug("DEBUG INFO: In exception %s" %excp)
                self.cleanup_remote_client()
                sys.exit(1)
            else:
                p4_exception = 0               
            finally:           
                if p4_exception == 0:
                    self.logger.debug("DEBUG INFO: No exception: %s" %p4_cmd)
                    break                                                    
        
    def connect_svr_sync_depot(self, sync_cl=''):
             
        # Catch exceptions with try/except
        p4_cmd = "self.client = self.p4.fetch_client()"
        self.handle_p4_connection_exception(p4_cmd)
        self.client["Client"] = self._client_name
        self.client["Root"] = self._client_root
                            
        # set mapping of client
        self.client["View"] = [self._depot + " " + "//" + self.client["Client"] + "/..."]
        #self.client["View"].append("-//depot/licensing/ddplus/ddp_enc/main/ddp_enc/test/..." + " //" + self.client["Client"] + "/DDP_ENC/ddp_enc/test/...")
        exclude_list = [d + " //" + self.client["Client"] + d.replace(self._depot[:-4], '')[1:] for d in \
        self._depot_excluded.split(',') if d != '']
        self.client['View'].extend(exclude_list)
        self.client['LineEnd' ] = 'unix'
        print "client view is: ", self.client["View"]
        
        # Create the new client/ws 
        p4_cmd = "self.p4.save_client(self.client)"
        self.handle_p4_connection_exception(p4_cmd)
        self.p4.client = self.client["Client"]
            
        if sync_cl:
            self._changelist = sync_cl           
            self._depot_at_cl = self._depot + '@' + str(self._changelist)
            
            self.logger.debug("DEBUG INFO: Sync P4 to  %s" %sync_cl)
            # p4 sync cl to client_root folder 
            p4_cmd = """self.p4.run("sync", "-f", self._depot_at_cl)"""
            self.handle_p4_connection_exception(p4_cmd)
            
        else:
            # p4 sync to client_root folder 
            self.logger.debug("DEBUG INFO: Sync P4 to latest ... ")
            p4_cmd = """self.p4.run("sync", "-f", self._depot)"""
            self.handle_p4_connection_exception(p4_cmd)
                        
        p4_cmd = """self._cur_cl_info = self.p4.run("info")"""
        self.handle_p4_connection_exception(p4_cmd) 
        
        self.logger.debug("DEBUG INFO: Current Self client info:::::::::::::::%s" %self.client)
        # is equal to p4 changes -m1 "./...#have"           
        self._current_cl = self._client_root + "/...#have"
        
        p4_cmd = """self._cur_cl_number =  \
        self.p4.run("changes", "-m1", self._current_cl)[0]['change']"""      
        self.handle_p4_connection_exception(p4_cmd)
        
        self.logger.debug("DEBUG INFO: Current files at changelist::::::::: %s" %self._cur_cl_number)                
        p4_cmd = """self._cur_cl_desc = \
        self.p4.run("changes", "-m1", self._current_cl)[0]['desc']"""
        self.handle_p4_connection_exception(p4_cmd)

        # return a string of current cl, a list of p4 info and a dict of client 
        return  \
        self._cur_cl_number, \
        self._cur_cl_desc,  \
        self._cur_cl_info, \
        self.client

    def connect_svr_unshelve_depot(self, shelve_id):
        # shelve code change to workspace for preflight feature
        self._unshelve_cl = shelve_id
        self.logger.debug("DEBUG INFO: Unshelve Source Code to ... %s" % self._unshelve_cl)
        print "Unshelve Source Code to ... %s" % self._unshelve_cl
        p4_cmd = """self.p4.run("unshelve", "-s", self._unshelve_cl, "-f")"""
        self.handle_p4_connection_exception(p4_cmd)

    def get_latest_p4_cl(self):

        p4_cmd = """self._latest_cl_number =  \
        self.p4.run("changes", "-m1", self._current_cl)[0]['change']"""
        self.handle_p4_connection_exception(p4_cmd)

        return self._latest_cl_number

    def get_current_p4_numbers(self, numbers):  
    
        i = 0
        changelists_on_current_p4 = []        
        while i < numbers:
            p4_cmd = """self._cl_on_current_p4 = \
            self.p4.run("changes", "-m", %i, self._current_cl)[%i]['change'] \
            """%(numbers, i)           
            self.handle_p4_connection_exception(p4_cmd)            
            changelists_on_current_p4.append(self._cl_on_current_p4)
            i += 1
        #print changelists_on_current_p4
        return changelists_on_current_p4
        
    def get_p4_numbers_from_start_to_end(self, start_cl, end_cl):
    
        #p4 changes $DI_WORKSPACE/...@$start_id,@$end_id | wc -l  
        p4_cmd = """self._p4_numbers_from_start_to_end = \
        self.p4.run("changes", "%s@%i,@%i")\
        """%(self._depot, end_cl, start_cl)  
        self.handle_p4_connection_exception(p4_cmd) 
        print len(self._p4_numbers_from_start_to_end)
        return [s['change'] for s in self._p4_numbers_from_start_to_end] 
        
    def get_author_of_p4_changelist(self, number):  

        #print "self._cur_cl_number P4 is at current change list: ", self._cur_cl_number
        p4_cmd = """self._specified_p4_changelist_info = \
        self.p4.run("changes", "%s@%i,@%i")\
        """%(self._depot, number, number)  
        self.handle_p4_connection_exception(p4_cmd) 
        
        #p4_cmd = """self.p4.run("changes", "-m1", self._current_cl)[0]['change']"""      
        #self.handle_p4_connection_exception(p4_cmd)
        return [s['user'] for s in self._specified_p4_changelist_info]
        
    
    def cleanup_remote_client(self):
        # Revert opened file due to unshelve action before clean up client
        self._client_name_stream = "//" + self._client_name + "/..."
        p4_cmd = """self.p4.run("revert", self._client_name_stream)"""
        self.handle_p4_connection_exception(p4_cmd)
        # Catch exceptions with try/except
        p4_cmd = """self.p4.run("client", '-d', self._client_name)"""
        self.handle_p4_connection_exception(p4_cmd)

    def gen_namespace(self):

        return socket.gethostname() + '_' + \
        str(os.getpid()) + '_' + \
        time.strftime("%Y%m%d%H%M%S") + '_' + \
        str(random.randint(0,99))
                
    def init_client_root_folder(self):
    
        if not os.path.exists(self._client_root):
            os.makedirs(self._client_root)  
        else:
            shutil.rmtree(self._client_root)
            os.makedirs(self._client_root)
                
    def __del__(self):
    
        print "Disconnecting...", self.p4
        self.p4.disconnect()
        print "Disconnected...", self.p4
