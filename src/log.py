"""This module provides logging functionality, simultaneously to stdout/stderr and to a log file. The module must be initialized before usage:

    Log.init("INFO", "DEBUG", "log_file.txt")

The module may be reinitialized, in order to change the verbosity settings and use a different log file.

Examples:

    Log.debug("A debug message")
    Log.info("An informational message")
    Log.error("An error", "message!", with_more, data)

The intended usage of the logging levels are:

DEBUG: Debug messages targeted to the ITAF developer (and possibly but not necessarily meaningful to the user)
INFO: Informational messages to the ITAF user
WARNING: Warning messages that something does not seem quite right, but not severe enough that processing cannot continue
ERROR: A problem happened from which recovery is not possible
QUIET: No messages can be printed at this level

A verbosity level is defined separately for stdout/stderr and for the log file. A message is sent to stdout/stderr only if its severity exceeds the verbosity level. For example, at the INFO level, only info(), warning() and error() messages are displayed. At the QUIET level, no messages are shown.

At the debug level, source filename and line number is attached to all messages.

This logger is implemented as a module, in order to avoid having to pass around logger object everywhere.
"""

__copyright__ = """
This program is protected under international and U.S. copyright laws as
an unpublished work. This program is confidential and proprietary to the
copyright owners. Reproduction or disclosure, in whole or in part, or the
production of derivative works therefrom without the express permission of
the copyright owners is prohibited.

               Copyright (C) 2015 by Dolby Laboratories,
               Copyright (C) 2011-2015 by Dolby International AB.
                           All rights reserved.
"""

import inspect
import shutil
import sys
import os

class _Level:
    QUIET = 0
    ERROR = 1
    WARNING = 2
    INFO = 3
    DEBUG = 4

_lookup = {}
_lookup["DEBUG"] = _Level.DEBUG
_lookup["INFO"] = _Level.INFO
_lookup["WARNING"] = _Level.WARNING
_lookup["ERROR"] = _Level.ERROR
_lookup["QUIET"] = _Level.QUIET

# state variables
class _State:
    level = None
    log_level = None
    log_file = None
    log_filename = None

# If this module is already loaded under a different name, then use the state of the other module. This is a work-around for the fact that plug-ins may reload this module using a different module name

_found = False
for module in sys.modules.keys():
    if module.endswith("log") and module != __name__:
        other = sys.modules[module]
        if hasattr(other, "_state"): # incase we come across some other log class
            _state = other._state
            _found = True
if not _found:
    _state = _State()
        
def init(verbosity, logfile_verbosity="QUIET", logfile="log.txt"):
    """Initializes or re-initializes the Log module"""

    if _state.log_file:
        _state.log_file.close()

    _state.log_filename = os.path.abspath(logfile)

    if verbosity in _lookup:
        _state.level = _lookup[verbosity]
    else:
        raise Exception("Illegal verbosity level " + str(verbosity))

    if logfile_verbosity in _lookup:
        _state.log_level = _lookup[logfile_verbosity]
    else:
        raise Exception("Illegal logfile verbosity level " + str(logfile_verbosity))
    if _state.log_level > _Level.QUIET:
        _state.log_file = open(_state.log_filename, "w")


def set_verbosity(verbosity):
    """Changes the message verbosity after the module has been initialized"""
    
    if verbosity in _lookup:
        _state.level = _lookup[verbosity]
    else:
        raise Exception("Illegal verbosity level " + str(verbosity))

def _dump(level, newline, *messages):
    """Prints messages to stdout/stderr and to the logfile.
    Warnings/errors are printed to stderr.
    When printing at the debug level, all messages have the severity and file/line prepended to them. Otherwise, only warnings and errors have the severity prepended to them.
    """

    if _state.level is None or _state.log_level is None:
        raise Exception("Log module is not initialized")
    
    # Build string to show
    out_msg = " ".join([str(m) for m in messages])
    if newline:
        out_msg += "\n"
    log_msg = out_msg

    severity = [k for k in _lookup.keys() if _lookup[k] == level]
    sev_msg = "[ %s ]: %s" % (severity[0], out_msg)

    # If at the debug level, add more information to the message
    if _state.level >= _Level.DEBUG or _state.log_level >= _Level.DEBUG:

        frame = inspect.currentframe().f_back.f_back
        f, l = frame.f_code.co_filename, frame.f_lineno

        f = os.path.basename(f)

        dbg_msg = "[ %s ] %s:%s: %s" % (severity[0], f, l, out_msg)


    # Prepend more or less info to the message
    if _state.level >= _Level.DEBUG:
        out_msg = dbg_msg
    elif level <= _Level.WARNING:
        out_msg = sev_msg

    if _state.log_level >= _Level.DEBUG:
        log_msg = dbg_msg
    elif level <= _Level.WARNING:
        log_msg = sev_msg

    # Print only if the message severity is high enough
    if _state.level >= level:
        if level <= _Level.WARNING:
            sys.stderr.write(out_msg)
        else:
            sys.stdout.write(out_msg)
            sys.stdout.flush()

    if _state.log_level >= level:
        _state.log_file.write(log_msg)

def move_logfile(logfile):
    """Flushes and moves the old logfile to the new location"""

    logfile = os.path.abspath(logfile)

    if _state.log_level > _Level.QUIET:

        if _state.log_file:
            _state.log_file.close()

        shutil.move(_state.log_filename, logfile)
        _state.log_file = open(logfile, "a")

    _state.log_filename = logfile

def get_logfile():
    return _state.log_filename

def debug(*msgs):
    _dump(_Level.DEBUG, True, *msgs)
    
def info(*msgs):
    _dump(_Level.INFO, True, *msgs)
    
def info_no_newline(*msgs):
    _dump(_Level.INFO, False, *msgs)
    
def warning(*msgs):
    _dump(_Level.WARNING, True, *msgs)
    
def error(*msgs):
    _dump(_Level.ERROR, True, *msgs)
        
