# encoding: UTF-8

from eventEngine import *


########################################################################
class BuildTestEngine(EventEngine):

	def __init__(self, **kwargs):

		super(BuildTestEngine, self).__init__(**kwargs)
		
		self.kwargs = kwargs
		self._event_number = len(kwargs['executable'])

	def _run_put(self):

		args = {
				'changelist' : self.kwargs['changelist'],
				'func_name' : self.kwargs['func_name'],
				'type' : self.kwargs['type']
				}

		for i in range(self._event_number):
			args['executable'] = self.kwargs['executable'][i]
			args['db_table_name'] = self.kwargs['db_table_name'][i]

			event = BuildTestEvent(**args)

			if not event.method():
				super(BuildTestEngine, self)._put(event)

	def _run_get(self):
		
		while self._active_get == True:
			try:
				event = self._queue.get(block = True, timeout = 1)
				super(BuildTestEngine, self)._process(event)
			except Empty:
				if self._put.isAlive():
					continue
				elif not self._queue.empty():
					continue
				else:
					break

	def start(self):

		self._active_get = True
		self._get.start()
		print "==================== Get thread in buildtestEngine starts ===================="

		self._put.start()
		print "==================== Put thread in buildtestEngine starts ===================="

	def stop(self):

		self._put.join()
		print "==================== Put thread in buildtestEngine ends ===================="

		self._get.join()
		print "==================== Get thread in buildtestEngine ends ===================="



########################################################################
class BuildTestEvent(Event):

	def __init__(self, **kwargs):

		super(BuildTestEvent, self).__init__(**kwargs)

		self._changelist = kwargs['changelist']
		self._executable = kwargs['executable']
		self._func_name = kwargs['func_name']
		self._db_table_name = kwargs['db_table_name']
		
	def method(self):

		return self._func_name(self._changelist, self._executable)