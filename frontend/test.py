#!/usr/bin/env python

__copyright__ = """
This program is protected under international and U.S. copyright laws as
an unpublished work. This program is confidential and proprietary to the
copyright owners. Reproduction or disclosure, in whole or in part, or the
production of derivative works therefrom without the express permission of
the copyright owners is prohibited.

               Copyright (C) 2013 by Dolby Laboratories,
               Copyright (C) 2013 by Dolby International AB.
                           All rights reserved.
"""
import os
import sys
src_dir = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.append(src_dir)

import run_common
import error
import log
import traceback
import pdb

if __name__ == "__main__":
    try:
        sys.exit(run_common.main())
    except (error.XMLError, error.UserError, error.PluginError):
        e = sys.exc_info()[1]
        log.debug(traceback.format_exc(e))
        log.error(e)
        sys.exit(1)

