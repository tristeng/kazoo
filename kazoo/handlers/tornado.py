from __future__ import absolute_import

import threading
from kazoo.handlers.utils import create_tcp_socket, create_tcp_connection
from tornado.concurrent import TracebackFuture
from tornado.ioloop import IOLoop
import select
import socket
import time
import functools


class KazooTimeoutError(Exception):
    pass


class TornadoHandler(object):
    name = "tornado_handler"
    timeout_exception = KazooTimeoutError
    sleep_func = staticmethod(time.sleep)

    def __init__(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def select(self, *args, **kwargs):
        return select.select(*args, **kwargs)

    def socket(self):
        return create_tcp_socket(socket)

    def create_connection(self, *args, **kwargs):
        return create_tcp_connection(socket, *args, **kwargs)

    def event_object(self):
        return threading.Event()

    def lock_object(self):
        return threading.Lock()

    def rlock_object(self):
        return threading.RLock()

    def async_result(self):
        return AsyncResult()

    def spawn(self, func, *args, **kwargs):
        IOLoop.current().add_callback(func, *args, **kwargs)

    def dispatch_callback(self, callback):
        IOLoop.current().add_callback(callback.func, *callback.args)


def async_result_complete(async_result):
    async_result.notify()


class AsyncResult(object):
    """
    Essentially a wrapper for a Tornado TracebackFuture
    """
    def __init__(self, future=None):
        if future is not None:
            self._future = future
        else:
            self._future = TracebackFuture()
            self._future.add_done_callback(functools.partial(async_result_complete, self))
        self._condition = threading.Condition()

    def ready(self):
        """Return `True` if and only if it holds a value or an
        exception"""
        return self._future.done()

    def successful(self):
        """Return `True` if and only if it is ready and holds a
        value"""
        return self._future.exception() is None

    @property
    def exception(self):
        return self._future.exception()

    def set(self, value=None):
        """Store the value. Wake up the waiters.

        :param value: Value to store as the result.

        Any waiters blocking on :meth:`get` or :meth:`wait` are woken
        up. Sequential calls to :meth:`wait` and :meth:`get` will not
        block at all."""
        with self._condition:
            self._future.set_result(value)

    def set_exception(self, exception):
        """Store the exception. Wake up the waiters.

        :param exception: Exception to raise when fetching the value.

        Any waiters blocking on :meth:`get` or :meth:`wait` are woken
        up. Sequential calls to :meth:`wait` and :meth:`get` will not
        block at all."""
        with self._condition:
            self._future.set_exception(exception)

    def get(self, block=True, timeout=None):
        """Return the stored value or raise the exception

        :param block: Whether this method should block or return
                      immediately.
        :type block: bool
        :param timeout: How long to wait for a value when `block` is
                        `True`.
        :type timeout: float

        If this instance already holds a value / an exception, return /
        raise it immediately. Otherwise, block until :meth:`set` or
        :meth:`set_exception` has been called or until the optional
        timeout occurs."""
        with self._condition:
            if self.ready():
                return self._future.result()
            elif block:
                self._condition.wait(timeout)
                return self._future.result()

            # if we get to this point we timeout
            raise KazooTimeoutError()

    def get_nowait(self):
        """Return the value or raise the exception without blocking.

        If nothing is available, raise the Timeout exception class on
        the associated :class:`IHandler` interface."""
        return self._future.result()

    def wait(self, timeout=None):
        """Block until the instance is ready.

        :param timeout: How long to wait for a value
        :type timeout: float

        If this instance already holds a value / an exception, return /
        raise it immediately. Otherwise, block until :meth:`set` or
        :meth:`set_exception` has been called or until the optional
        timeout occurs."""
        with self._condition:
            self._condition.wait(timeout)
        return self.ready()

    def rawlink(self, callback):
        """Register a callback to call when a value or an exception is
        set

        :param callback:
            A callback function to call after :meth:`set` or
            :meth:`set_exception` has been called. This function will
            be passed a single argument, this instance.
        :type callback: func

        """
        def on_callback(future):
            callback(AsyncResult(future))

        IOLoop.current().add_future(self._future, on_callback)

    def unlink(self, callback):
        """Remove the callback set by :meth:`rawlink`

        :param callback: A callback function to remove.
        :type callback: func

        """

    def notify(self):
        self._condition.notify_all()