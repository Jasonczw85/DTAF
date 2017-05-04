"""This modules defines exceptions for error conditions which happen outside of ITAF"""

__copyright__ = """
This program is protected under international and U.S. copyright laws as
an unpublished work. This program is confidential and proprietary to the
copyright owners. Reproduction or disclosure, in whole or in part, or the
production of derivative works therefrom without the express permission of
the copyright owners is prohibited.

               Copyright (C) 2015 by Dolby Laboratories,
               Copyright (C) 2015 by Dolby International AB.
                           All rights reserved.
"""


class XMLError(Exception):
    """All problems with reading XML test specs should result in an XML error being raised"""
    def __init__(self, element, msg):
        """element: XML element close to where the error occurred"""

        if element is None:
            # Support that the element is not given
            position = ""
        else:
            filename = element.attrib["_file"]
            line_number = element.attrib["_line"]
            column = element.attrib["_column"]
            position = "%s:%s:%s:<%s>: " % (filename, line_number, column, element.tag)

        Exception.__init__(self, "%s%s" % (position, str(msg)))

class PluginError(Exception):
    """All problems related to the plug-ins"""
    def __init__(self, plugin_name, msg):
        """plugin_name: Name of problematic plug-in"""
        Exception.__init__(self, "%s: %s" % (str(plugin_name), str(msg)))

class UserError(Exception):
    """All problems related to user input from the command line"""
    def __init__(self, msg):
        Exception.__init__(self, msg)
