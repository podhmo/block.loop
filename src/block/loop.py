# -*- coding:utf-8 -*-
from copy import copy
from collections import namedtuple
from functools import partial
from pyramid.response import Response

Break = namedtuple("Break", "v")
Return = namedtuple("Return", "v")

class RunStrategy(object):
    def __init__(self, store_factory):
        self.store_factory = store_factory

    def lift(self, fn):
        def lifted(c, *args, **kwargs):
            return Return(fn(*args, **kwargs))
        return lifted

    def run_composed(self, composed, args, kwargs, store=None):
        store = store or self.store_factory()
        loops = composed.loops
        v = loops[0]._run(args, kwargs, store=store)
        for loop in loops[1:]:
            v = loop._run([v], {}, store=store)
        return v

    def run_one(self, loop, args, kwargs, store=None):
        store = store or self.store_factory()
        q = loop.q
        v = q[0](store, *args, **kwargs)
        if isinstance(v, Break):
            return v.v
        for fn in q[1:]:
            if isinstance(v, Break):
                return v.v
            v = fn(store, v.v)
        return v.v

class AppendStrategy(object):
    def __init__(self, store_factory):
        self.store_factory = store_factory

    def lift(self, fn):
        def lifted(c, *args, **kwargs):
            return fn(*args, **kwargs)
        return lifted

    def run_composed(self, composed, args, kwargs, store=None):
        store = store or self.store_factory()
        loops = composed.loops
        v = loops[0]._run(args, kwargs, store=store)
        for loop in loops[1:]:
            v = loop._run(args, kwargs, store=store)
        return v

    def run_one(self, loop, args, kwargs, store=None):
        store = store or self.store_factory()
        for fn in loop.q:
            fn(store, *args, **kwargs)
        return store


class ComposedLoop(object):
    def __init__(self, loops, strategy):
        self.loops = loops
        self.cur = loops[0]
        self.strategy = strategy

    def __copy__(self):
        return self.__class__(list(self.loops[:]), self.strategy)

    def add(self, e):
        new = copy(self)
        new.loops[-1] = new.loops[-1].add(e)
        return new

    def merge(self, loop):
        new = copy(self)
        new.loops.append(loop)
        return new

    def lift(self, fn):
        return self.cur.lift(fn)

    def run(self, *args, **kwargs):
        return self._run(args, kwargs)

    def _run(self, args, kwargs, **extra):
        return self.strategy.run_composed(self, args, kwargs, **extra)

class Loop(object):
    def __init__(self, q=None, strategy=RunStrategy(dict)):
        self.q = q or []
        self.strategy = strategy

    def __copy__(self):
        return self.__class__(list(self.q[:]), strategy=self.strategy)

    def add(self, e):
        new = copy(self)
        new.q.append(e)
        return new

    def merge(self, loop):
        return ComposedLoop([self, loop], strategy=self.strategy)

    def lift(self, fn):
        return self.strategy.lift(fn)

    def run(self, *args, **kwargs):
        return self._run(args, kwargs)

    def _run(self, args, kwargs, **extra):
        return self.strategy.run_one(self, args, kwargs, **extra)

class PylonsLikeStorage(object):
    def asdict(self):
        return self.__dict__

def as_dict_or_response(response):
    if hasattr(response, "asdict"):
        return response.asdict()
    else:
        return response

class ViewFromLoop(object):
    def __init__(self, loop, name=""):
        self.loop = loop
        self.__name__ = name

    @property
    def __name__(self):
        return self.loop.__name__

    def __call__(self, *args, **kwargs):
        response = self.loop.run(*args, **kwargs)
        return as_dict_or_response(response)

    def __repr__(self):
        return "{self.__class__.__name__!r}: {self.__name__!r}".format(self=self)

class ViewFromLoopForLazy(object):
    def __init__(self, loop, name=""):
        self.loop = copy(loop)
        self.original_factory = self.loop.strategy.store_factory
        self.__name__ = name

    def for_lazy(self, context, request):
        c = self.original_factory()
        c.context = context
        c.request = request
        return c

    def dispose(self, c):
        del c.context

    def __call__(self, context, request, *args, **kwargs):
        self.loop.strategy.store_factory = partial(self.for_lazy, context, request)
        response = self.loop.add(self.dispose).run(*args, **kwargs)
        return as_dict_or_response(response)

    def __repr__(self):
        return "{self.__class__.__name__!r}: {self.__name__!r}".format(self=self)


class ViewLoopStrategy(object):
    def __init__(self, store_factory=PylonsLikeStorage):
        self.store_factory = store_factory

    def lift(self, fn):
        def lifted(c, *args, **kwargs):
            return fn(*args, **kwargs)
        return lifted

    def run_composed(self, composed, args, kwargs, store=None):
        store = store or self.store_factory()
        loops = composed.loops
        v = loops[0]._run(args, kwargs, store=store)
        for loop in loops[1:]:
            v = loop._run(args, kwargs, store=store)
            if isinstance(v, Response):
                return v
        return v

    def run_one(self, loop, args, kwargs, store=None):
        store = store or self.store_factory()
        for fn in loop.q:
            v = fn(store, *args, **kwargs)
            if isinstance(v, Response):
                return v
        return store

class LoopViewConstractMeta(type):
    def __new__(self, name, bases, attrs):
        loop = attrs.get("loop") or Loop(strategy=ViewLoopStrategy())
        for ac in attrs["action"]:
            loop = loop.add(ac)
        view = attrs.get("factory", ViewFromLoop)(loop)
        view.__name__ = name
        view.__doc__ = attrs.get("__doc__")
        return view

def view_loop():
    loop = Loop(strategy=ViewLoopStrategy(store_factory=PylonsLikeStorage))
    return loop

