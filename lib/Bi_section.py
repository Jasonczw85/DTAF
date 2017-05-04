import os, sys, re, string, shutil, time, getpass, socket
import platform, random
import logging

class Bi_Section_Search_On_P4(object):
    """ 
    This class is used to search the change list on P4 with bi section algrithom,
    it will get the middle change list from the given start changelist to the end 
    change list.
    
    The calculation method is:
    Length of Change lists from start to end is presented by n. The middle one 
    is at the point of the last "n-(n/2)" of the list.
    
    For example, the list as below:
    
 <--- 6---------> the start one
 |    5
 |    4           <-------------|If grow upwards, the next middle one
 |--->3--->| The middle one --->|
      2<---| If grow downwards, the next middle one
      1-------> the end one 
    
    """
    def __init__(self, args):
        self._start_cl = args['start_cl']
        self._end_cl = args['end_cl']
        self._p4_instance = args['p4_instance']
        
        current_path = os.getcwd()
        
        self.logger = logging.getLogger('Bi_section_search_logger')
        self.logger.setLevel(logging.INFO)

        fh = logging.FileHandler(os.path.join(os.getcwd(),'Bi_search_log.txt'),'w')
        fh.setLevel(logging.INFO)
        
        formatter = logging.Formatter(\
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)


    def calculate_run(self):
        p4_changelists = self._p4_instance.get_p4_numbers_from_start_to_end(\
            self._start_cl, self._end_cl)
        p4_numbers = len(p4_changelists)
        print p4_changelists
        self._p4_changelists = p4_changelists
        #self.logger.info(p4_changelists)
        p4_middle_changelist = p4_changelists[-(p4_numbers - p4_numbers/2)]
        self._mid_cl = int(p4_middle_changelist)
        
        return (p4_numbers, self._mid_cl)

