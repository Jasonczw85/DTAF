# encoding: UTF-8

from Queue import Queue, Empty
from threading import Thread
from time import sleep


########################################################################
class EventEngine(object):

	def __init__(self, **kwargs):

		self.kwargs = kwargs

		self._queue = Queue()

		self._active_put = False
		self._put = Thread(target = self._run_put)

		self._active_get = False
		self._get = Thread(target = self._run_get)

		self._handlers = {}

	def _run_get(self):

		while self._active_get:
			try:
				event = self._queue.get(block = True, timeout = 1)
				self._process(event)
			except Empty:
				pass

	def _process(self, event):

		if event._type in self._handlers:
			[handler(event) for handler in self._handlers[event._type]]

	def _run_put(self):

		while self._active_put:
			event = Event(**self.kwargs)
			self._put(event)

	def start(self):

		self._active_get = True
		self._get.start()

		self._active_put = True
		self._put.start()

	def stop(self):

		self._active_put = False
		self._active_get = False

		self._put.join()
		self._get.join()

	def register(self, type, handler):

		try:
			handlerList = self._handlers[type]
		except KeyError:
			handlerList = []
			self._handlers[type] = handlerList

		if handler not in handlerList:
			handlerList.append(handler)

	def unregister(self, type, handler):

		try:
			handlerList = self._handlers[type]

			if handler in handlerList:
				handlerList.remove(handler)

			if not handlerList:
				del self._handlers[type]
		except KeyError:
			pass

	def _put(self, event):

		self._queue.put(event)


########################################################################
class Event(object):

	def __init__(self, **kwargs):

		self._type = kwargs['type']







