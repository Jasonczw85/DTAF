"""
Classes for interacting with Confluence. Currently supports:
    * Creating a page
    * Attaching a file

"""

from __future__ import with_statement
import sys, string, xmlrpclib, re, os, traceback, time
import pdb

# Private attributes
_default_server = 'https://confluence.dolby.net/kb/rpc/xmlrpc'

class Session(object):
    '''An open connection with the Confluence server'''
    
    def __init__(self,
                 user,
                 pw,
                 space,
                 page_title,
                 server_url=_default_server): 
        self._user = user
        self._pw = pw
        self._server = xmlrpclib.ServerProxy(server_url)
        self._token = self._server.confluence2.login(self._user, self._pw)
        self._cur_space = space
        self.set_page(page_title)

    def refresh_token(self):
        self._token = self._server.confluence2.login(self._user, self._pw)

    class Page(object):
        def __init__(self,
                     space,
                     title,
                     content,
                     parentId):
            self.space = space
            self.title = title
            self.content = content         
            self.parentId = parentId

    class Attachment(object):
        def __init__(self,
                     filename,
                     content_type='image/png',
                     comment='auto-attached'):
            self.fileName = filename
            self.contentType = content_type
            self.comment = comment
    
    def get_page(self,
                 title):
        try:
            return self._server.confluence2.getPage(self._token,
                                                    self._cur_space,
                                                    title)
        except:
            return None

    def current_page_content(self):
        if self._cur_page is not None:
            return self._cur_page['content']
        else:
            return None

    def set_page(self,  
                 title):
        self._cur_page = self.get_page(title)
        return self._cur_page

    def create_page(self, 
                    title, 
                    content=''):

        """ Creates a Confluence page """        
        if self._cur_page is None:
            self.set_page('Home')
        try:
            page = Session.Page(self._cur_space,
                                title,
                                content,
                                self._cur_page['id'])

            self._server.confluence2.storePage(self._token, 
                                               page)
            return True
        except Exception as e:
            print 'could not create page ' + title
            return False

    def update_page(self,
                    new_content,
                    line_number=0,
                    overwrite=False):
        assert type(new_content) == type([])
        assert line_number >= -1

        if line_number == -1:
            line_number = len(self._cur_page['content'].split('\n'))
        if overwrite:
            self._cur_page['content'] = ' '

        update_options = {}
        update_options['minorEdit'] = True

        new_lines = len(new_content)

        before_insert = self._cur_page['content'].split('\n')[:line_number]
        after_insert = self._cur_page['content'].split('\n')[line_number:]
        new_content = before_insert + new_content + after_insert
        line_number = line_number + new_lines

        self._cur_page['content'] = new_content[0]

        for line in new_content[1:]:
            self._cur_page['content'] = self._cur_page['content'] + '\n' + line
        
        try:
            self._cur_page = self._server.confluence2.updatePage(self._token, 
                                                                 self._cur_page, 
                                                                 update_options)
            return line_number
        except Exception as e:        
            print 'could not update page ' + self._cur_page['title']
            return None

    def rename_page(self,
                    title,
                    new_title):
        try:
            page = self.get_page(title)
            page['title'] = new_title
            update_options = {'minorEdit':True}
            self._server.confluence2.updatePage(self._token,
                                                page,
                                                update_options)
        except Exception as e:
            print 'could not rename page: ' + title
            print str(e)
            return False
                                                

    def remove_page(self,
                    title):
        try:
            page = self.get_page(title)
            self._server.confluence2.removePage(self._token, 
                                                page['id'])
            print title + ' deleted!'
            return True
        except:
            print 'could not remove ' + title
            return False

    def attach(self, 
               filename,
               content_type='image/png', 
               comment='auto-attached'):        
        """ Attaches a file to a Confluence page """
        
        # read in all the data        
        with open(filename, 'rb') as f:
            data = f.read(); 
        
        attachment = Session.Attachment(os.path.basename(filename),
                                        content_type,
                                        comment)
        
        try:
            self._server.confluence2.addAttachment(self._token, 
                                                   self._cur_page['id'], 
                                                   attachment, 
                                                   xmlrpclib.Binary(data))
        except Exception:
            raise Exception, "Could not create attachment to page " + \
                self._cur_space + ":" + self._cur_page['title'] + \
                " using file " + filename
        
                               
    def remove_children(self,
                        space=None,
                        title=None):
        if space is not None:
            self._cur_space = space
        if title is not None:
            self.set_page(title)

        try:            
            children = self._server.confluence2.getChildren(self._token, 
                                                            self._cur_page['id'])
        except:
            raise Exception, "Could not get children of page"

        for child in children:
            kill = raw_input('delete ' + child['title'] + '?')
            if kill == 'y' or kill == 'Y' or kill == 'yes' or kill == 'Yes' or kill == 'YES':
                try:
                    self._server.confluence2.removePage(self._token, 
                                                        child['id'])
                    print child['title'] + ' deleted!'
                except:
                    raise Exception, "Could not remove child from page"
            else:
                print child['title'] + ' saved'




