# encoding: UTF-8

EVENT_TIMER = 'eTimer'                  
EVENT_LOG = 'eLog'                      


#
UPDATE_TO_SQL = 'TestMysqlonRemote'
#----------------------------------------------------------------------
def test():
    
    check_dict = {}
    
    global_dict = globals()    
    
    for key, value in global_dict.items():
        if '__' not in key:                       
            if value in check_dict:
                check_dict[value].append(key)
            else:
                check_dict[value] = [key]
            
    for key, value in check_dict.items():
        if len(value)>1:
            for name in value:
                print name
            print ''
        

    

# 
if __name__ == '__main__':
    test()