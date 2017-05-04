# encoding: UTF-8

from eventEngine import *


########################################################################
class BuildTestEngine_plus(EventEngine):

	def __init__(self, **kwargs):

		super(BuildTestEngine_plus, self).__init__(**kwargs)
		
		self.kwargs = kwargs
		self._event_number = len(kwargs['executable'])

	def _run_put(self):

		args = {
				'func_name' : self.kwargs['func_name'],
				'type' : self.kwargs['type']
				}

		for i in range(self._event_number):
			args['executable'] = self.kwargs['executable'][i]

			event = BuildTestEvent_plus(**args)

			if not event.method():
				super(BuildTestEngine_plus, self)._put(event)

	def _run_get(self):
		
		while self._active_get == True:
			try:
				event = self._queue.get(block = True, timeout = 1)
				super(BuildTestEngine_plus, self)._process(event)
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
		print ("Get thread in buildtestEngine starts".center(78,'='))

		self._put.start()
		print ("Put thread in buildtestEngine starts".center(78,'='))

	def stop(self):

		self._put.join()
		print ("Put thread in buildtestEngine ends".center(78,'='))

		self._get.join()
		print ("Get thread in buildtestEngine ends".center(78,'='))



########################################################################
class BuildTestEvent_plus(Event):

	def __init__(self, **kwargs):

		super(BuildTestEvent_plus, self).__init__(**kwargs)

		self._executable = kwargs['executable']
		self._func_name = kwargs['func_name']
		
	def method(self):

		return self._func_name(self._executable)