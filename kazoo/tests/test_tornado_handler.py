import threading
import unittest

from nose import SkipTest
from nose.tools import eq_
from nose.tools import raises

from kazoo.client import KazooClient
from kazoo.exceptions import NoNodeError
from kazoo.protocol.states import Callback
from kazoo.testing import KazooTestCase
from kazoo.tests import test_client

try:
    from tornado.testing import gen_test, AsyncTestCase
    TestCase = AsyncTestCase
except ImportError:
    def gen_test(func):
        return func
    TestCase = unittest.TestCase


class TestTornadoHandler(AsyncTestCase):

    def setUp(self):
        try:
            import tornado
        except ImportError:
            raise SkipTest('tornado not available.')
        super(TestTornadoHandler, self).setUp()

    def _makeOne(self, *args):
        from kazoo.handlers.tornado import TornadoHandler
        return TornadoHandler()

    def _getAsync(self, *args):
        from kazoo.handlers.tornado import AsyncResult
        return AsyncResult

    @gen_test
    def test_proper_threading(self):
        h = self._makeOne()
        h.start()
        # In Python 3.3 _Event is gone, before Event is function
        event_class = getattr(threading, '_Event', threading.Event)
        assert isinstance(h.event_object(), event_class)

    @gen_test
    def test_matching_async(self):
        h = self._makeOne()
        h.start()
        async = self._getAsync()
        assert isinstance(h.async_result(), async)

    @gen_test
    def test_exception_raising(self):
        h = self._makeOne()

        @raises(h.timeout_exception)
        def testit():
            raise h.timeout_exception("This is a timeout")
        testit()

#
# class TestBasicGeventClient(KazooTestCase):
#
#     def setUp(self):
#         try:
#             import tornado  # NOQA
#         except ImportError:
#             raise SkipTest('tornado not available.')
#
#     def _makeOne(self, *args):
#         from kazoo.handlers.gevent import SequentialGeventHandler
#         return SequentialGeventHandler(*args)
#
#     def _getEvent(self):
#         from gevent.event import Event
#         return Event
#
#     def test_start(self):
#         client = self._get_client(handler=self._makeOne())
#         client.start()
#         self.assertEqual(client.state, 'CONNECTED')
#         client.stop()
#
#     def test_start_stop_double(self):
#         client = self._get_client(handler=self._makeOne())
#         client.start()
#         self.assertEqual(client.state, 'CONNECTED')
#         client.handler.start()
#         client.handler.stop()
#         client.stop()
#
#     def test_basic_commands(self):
#         client = self._get_client(handler=self._makeOne())
#         client.start()
#         self.assertEqual(client.state, 'CONNECTED')
#         client.create('/anode', 'fred')
#         eq_(client.get('/anode')[0], 'fred')
#         eq_(client.delete('/anode'), True)
#         eq_(client.exists('/anode'), None)
#         client.stop()
#
#     def test_failures(self):
#         client = self._get_client(handler=self._makeOne())
#         client.start()
#         self.assertRaises(NoNodeError, client.get, '/none')
#         client.stop()
#
#     def test_data_watcher(self):
#         client = self._get_client(handler=self._makeOne())
#         client.start()
#         client.ensure_path('/some/node')
#         ev = self._getEvent()()
#
#         @client.DataWatch('/some/node')
#         def changed(d, stat):
#             ev.set()
#
#         ev.wait()
#         ev.clear()
#         client.set('/some/node', 'newvalue')
#         ev.wait()
#         client.stop()
#
#
# class TestGeventClient(test_client.TestClient):
#
#     def setUp(self):
#         try:
#             import tornado  # NOQA
#         except ImportError:
#             raise SkipTest('tornado not available.')
#         from tornado.ioloop import IOLoop
#
#     def _makeOne(self, *args):
#         from kazoo.handlers.gevent import SequentialGeventHandler
#         return SequentialGeventHandler(*args)
#
#     def _get_client(self, **kwargs):
#         kwargs["handler"] = self._makeOne()
#         return KazooClient(self.hosts, **kwargs)
