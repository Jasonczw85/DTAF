import time
import pexpect
import sys

def sudo(pw, cmd):
    session = pexpect.spawn('ssh localhost')
    assert session is not None, 'couldn\'t spawn sudo session'
    # set extra-long timeout time since some VMs are very slow at executing sudo commands
    session.timeout = 60
    session.expect('password')
    session.sendline(pw)
    session.expect('baseprompt')
    session.sendline('sudo %s' % cmd)
    session.expect('password')
    session.sendline(pw)
    session.expect('baseprompt')

def time_string():
    '''Return a string representing the current local time.  Useful for appending to filenames to ensure uniqueness.'''

    az = lambda t: t < 10 and ('0' + str(t)) or str(t)
    ts = time.localtime()
    s = az(ts.tm_year) + \
        az(ts.tm_mon) + \
        az(ts.tm_mday) + \
        az(ts.tm_hour) + \
        az(ts.tm_min) + \
        az(ts.tm_sec)

    return s
