import re
import os
import pdb

def split_backend_target(bkndtgt):
    if 'generic_float32' in bkndtgt:
        backend = 'generic_float32'
    elif 'armv7int_neon' in bkndtgt:
        backend = 'armv7int_neon'
    elif 'armv7int' in bkndtgt:
        backend = 'armv7int'
    elif 'c64plus' in bkndtgt:
        backend = 'c64plus'
    elif 'ipp_float_interleaved' in bkndtgt:
        backend = 'ipp_float_interleaved'
    elif 'ipp_float_non_interleaved' in bkndtgt:
        backend = 'ipp_float_non_interleaved'
    else:
        raise Exception, 'backend not recognized in: %s' % bkndtgt

    if 'dlb_profile' in bkndtgt:
        target = 'dlb_profile'
    else:
        raise Exception, 'target not recognized in: %s' % bkndtgt
    
    return (backend, target)


class param_dict(dict):
    '''param_dict is a dictionary subclass that stores all parameters needed for profiling automation'''

    def _handle_type(self, value):
        '''
        if the string contains a bash-style variable, 
        expand it and return the expanded string. if 
        the string value is a number, convert it to a 
        float, otherwise leave it as a string and 
        remove any line feeds
        '''
        
        m = re.match('\$\((.+)\)(.+)?', value)
        if m is not None and len(m.groups()) == 2:
            try:
                if m.group(2) is None:
                    return self[m.group(1)]
                else:
                    return self[m.group(1)] + m.group(2)
            except KeyError:
                raise KeyError, 'Config File Error: variable referenced before declaration.'
        else:
            try:
                fv = float(value)
                if int(fv) == fv:
                    return int(fv)
                else:
                    return fv
            except ValueError:
                return value.rstrip('\n')

    def _parse_cfg(self, cfg_fn):
        with open(cfg_fn, 'r') as cfg:
            for line in cfg:
                if len(line) > 1 and line[0] is not '#':
                    (key, raw_value) = re.split(' *= *', line)
                    self[key] = self._handle_type(raw_value)
    
    def __init__(self, cfg_fn):
        super(param_dict, self).__init__()
        self._parse_cfg(cfg_fn)

class profiling_params(param_dict):
    @staticmethod
    def get_machine_cfg_fn(buildconfig):
        filedir = os.path.dirname(os.path.abspath(__file__))
        if 'linux' in buildconfig:
            if 'cortex_a9' in buildconfig:
                return '%s/../config/panda_0.cfg' % filedir
            elif 'amd64' in buildconfig or 'x86' in buildconfig:
                return '%s/../config/optiplex_lin64.cfg' % filedir    
        elif 'osx' in buildconfig:
            return '%s/../config/macmini.cfg' % filedir
        elif 'beagleboard' in buildconfig:
            return '%s/../config/beagle_0.cfg' % filedir
        raise Exception, 'unsupported buildconfig: ' + buildconfig

    def __init__(self, 
                 cases_fn, 
                 exename, 
                 buildconfig,
                 target,
                 n_iters, 
                 project,
                 changelist,
                 node):
        '''
        parse the config file and add the parameter 
        names and values to the dictionary
        '''
        cfg_fn = profiling_params.get_machine_cfg_fn(buildconfig)
        super(profiling_params, self).__init__(cfg_fn)
        self.parse_build_config(buildconfig)
        self['project'] = project
        self['n_iters'] = n_iters
        self['changelist'] = changelist
        self['node'] = node
        self['backend'], self['target'] = split_backend_target(target)
        if self['platform'] in ['arm', 'linux'] and self['project'] != 'ddp_enc_joc_multicore':
            self['exename'] = 'taskset 1 ./' + exename
        else:
            self['exename'] = './' + exename

        self.parse_cases_file(cases_fn)

    def parse_cases_file(self, cases_fn):
        with open(cases_fn, 'r') as cases:
            self['cases'] = []
            last_line = ''
            for line in cases:
                if line.startswith('%'):
                    self['extTable'] = line[1:].rstrip()
                elif line[0] == '-':
                    if last_line.startswith('$'):
                        cmd = line.rstrip()
                        [label, fps] = last_line[1:].rstrip().split()
                        self['cases'].append((label, float(fps), cmd))
                    else:
                        raise Exception, 'command-line not preceded by a case label: %s' % line
                last_line = line

    def parse_build_config(self, cfg):
        if 'linux' in cfg or 'beagleboard' in cfg:
            op_sys = 'linux'
        elif 'osx' in cfg:
            op_sys = 'osx'
        else:
            raise Exception, 'unsupported os type'

        if 'cortex_a9' in cfg:
            if 'vfp_neon' in cfg:
                arch = 'cortex_a9_vfp_neon'
            else:
                arch = 'cortex_a9'
        elif 'x86' in cfg:
            arch = 'x86'
        elif 'amd64' in cfg:
            arch = 'amd64'
        elif 'c64plus' in cfg:
            arch = 'c64plus'
        elif 'c64' in cfg:
            arch = 'c64'
        else:
            raise Exception, 'unsupported architecture'

        if 'gnu' in cfg:
            cc = 'gnu'
        elif 'icc' in cfg:
            cc = 'icc'
        elif 'rvct_cslibc' in cfg:
            cc = 'rvct_cslibc'
        elif 'c6run' in cfg:
            cc = 'ccs'
        else:
            raise Exception, 'unsupported compiler'

        def version(cc):
            if cc == 'gnu':
                return '4.4.6'
            elif cc == 'icc':
                return '12.1.3'
            elif cc == 'rvct_cslibc':
                return '5.01'
            elif cc == 'ccs':
                return '7.1.4'

        self['os'] = op_sys
        self['architecture'] = arch
        self['compiler'] = cc
        self['version'] = version(cc)
