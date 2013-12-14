# -*- coding:utf-8 -*-
import unittest
from pyramid import testing
from functools import partial
from pyramid.httpexceptions import HTTPFound

def call_view(view, *args, **kwargs):
    request = testing.DummyRequest(*args, **kwargs)
    context = testing.DummyResource(request=request)
    request.context = context
    return view(context, request)


def add_login_user(c, context, request):
    c.user = "user"
def add_actions(c, context, request):
    c.actions = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
def add_login_message(c, context, request):
    c.message = "*login message*"



class Tests(unittest.TestCase):
    def _makeLoop(self, *args, **kwargs):
        from block.loop import Loop, ViewLoopStrategy
        return Loop(strategy=ViewLoopStrategy())

    def _makeView(self, *args, **kwargs):
        from block.loop import ViewFromLoop
        return ViewFromLoop(*args, **kwargs)

    def test_it(self):
        loop = (self._makeLoop()
                .add(add_login_user)
                .add(add_actions)
                .add(add_login_message))
        view = self._makeView(loop)
        result = call_view(view)

        self.assertEqual(result["user"], "user")
        self.assertEqual(result["message"], "*login message*")
        self.assertEqual(result["actions"], list(range(1, 11)))

    def test_break(self):
        loop = (self._makeLoop()
                .add(add_login_user)
                .add(add_actions)
                .add(add_login_message))
        @loop.lift
        def intercept(context, request):
            raise HTTPFound("feeeh")
        @loop.lift
        def dont_call(context, request):
            raise Exception("dont_call")

        loop = loop.add(intercept).add(dont_call)

        view = self._makeView(loop)
        with self.assertRaises(HTTPFound):
            call_view(view)

    def test_redirect(self):
        loop = (self._makeLoop()
                .add(add_login_user)
                .add(add_actions)
                .add(add_login_message))
        @loop.lift
        def intercept(context, request):
            return HTTPFound("feeeh")
        @loop.lift
        def dont_call(context, request):
            raise Exception("dont_call")

        loop = loop.add(intercept).add(dont_call)

        view = self._makeView(loop)
        result = call_view(view)
        self.assertTrue(isinstance(result, HTTPFound))

    def test_use_prev(self):
        def add_session(c, context, request):
            c.session = []
        def use_session(c, context, request):
            c.session.append("foo")

        loop = (self._makeLoop()
                .add(add_session)
                .add(use_session))
        view = self._makeView(loop)

        result = call_view(view)
        self.assertEqual(result, {"session": ["foo"]})

    def test__it__for_lazy_person(self):
        def one(c):
            c.one = "one"
        def two(c):
            c.two = "two"
        def message(c, fmt="{}"):
            c.message = fmt.format(c.request.matchdict["name"])

        loop = (self._makeLoop()
                .add(one)
                .add(two)
                .add(partial(message, fmt="hello: {}")))
        from block.loop import ViewFromLoopForLazy
        view = ViewFromLoopForLazy(loop)

        result = call_view(view, matchdict={"name": "foo"})
        self.assertEqual(result["one"], "one")
        self.assertEqual(result["two"], "two")
        self.assertEqual(result["message"], "hello: foo")

    def test__constract_view__i_dont_like_this(self):
        from block.loop import LoopViewConstractMeta
        class MyView(object, metaclass=LoopViewConstractMeta):
            """heh"""
            action = [
                add_login_user,
                add_actions,
                add_login_message,
            ]

        self.assertEqual(MyView.__doc__, """heh""")
        self.assertIn("MyView", repr(MyView))

        result = call_view(MyView)

        self.assertEqual(result["user"], "user")
        self.assertEqual(result["message"], "*login message*")
        self.assertEqual(result["actions"], list(range(1, 11)))

if __name__ == '__main__':
    unittest.main()
