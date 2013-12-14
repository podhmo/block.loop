# -*- coding:utf-8 -*-
import unittest
def double(x):
    return [x, x]

class Tests(unittest.TestCase):
    def _makeOne(self, *args, **kwargs):
        from block.loop import Loop
        return Loop(*args, **kwargs)

    def test__lift(self):
        target = self._makeOne()
        db = target.lift(double)
        result = target.add(db).add(db).run(10)
        self.assertEqual(result, [[10, 10], [10, 10]])

    def test__break(self):
        from block.loop import Break
        target = self._makeOne()
        db = target.lift(double)
        def intercept(c, x):
            return Break(x)
        result = target.add(db).add(intercept).add(db).run(10)
        self.assertEqual(result, [10, 10])

    def test_another(self):
        target = self._makeOne()
        lift = target.lift
        db = lift(double)
        target = target.add(db)

        result1 = target.add(lift(lambda xs: [x+1 for x in xs])).add(db).run(10)
        self.assertEqual(result1, [[11, 11], [11, 11]])

        result2 = target.add(lift(lambda xs: [x+2 for x in xs])).add(db).run(10)
        self.assertEqual(result2, [[12, 12], [12, 12]])


    def test__merge(self):
        target = self._makeOne()
        db = target.lift(double)
        target = target.add(db).add(db)
        result = target.merge(target).run(10)
        self.assertEqual(result, 
                         [[[[10, 10], [10, 10]], [[10, 10], [10, 10]]]
                          , [[[10, 10], [10, 10]], [[10, 10], [10, 10]]]])

    def test__merge_merge(self):
        target = self._makeOne()
        lift = target.lift
        inc = lift(lambda x: x+1)

        plus3 = target.add(inc).add(inc).add(inc)
        self.assertEqual(plus3.run(0), 3)

        plus9 = plus3.merge(plus3).merge(plus3)
        self.assertEqual(plus9.run(0), 9)

        plus14 = plus9.add(inc).merge(plus3).add(inc)
        self.assertEqual(plus14.run(0), 14)

    def test__swap_strategy(self):
        from block.loop import AppendStrategy
        L = []
        target = self._makeOne(strategy=AppendStrategy(lambda : L))
        def add_name(context, name):
            context.append(name)
        target = target.add(add_name).add(add_name)
        target = target.merge(target).add(add_name)
        self.assertEqual(target.run("foo"), ['foo', 'foo', 'foo', 'foo', 'foo'])

if __name__ == '__main__':
    unittest.main()
