from collections import defaultdict
import importlib
import mock
from typing import Callable
import uuid


class MockTrace:
    events = {}
    call_stack = []
    call_graph = defaultdict(list)

    @classmethod
    def calls_count(cls):
        return sum(len(v) for v in cls.call_graph.values())

    @classmethod
    def graph_shape(cls, hide_modules: bool = False) -> list:
        ordered_graph = []
        call_graph = cls.call_graph.copy()

        def reorder(from_vertex):
            if from_vertex not in call_graph:
                return
            next_vs = call_graph.pop(from_vertex)
            ordered_graph.append((from_vertex, next_vs))
            for v in next_vs:
                reorder(v)

        def cid2func(cid):
            if cid is None:
                return None

            ev = cls.events[cid]
            args = str(ev['args']) if ev['args'] else ""
            args += str(ev['kwargs']) if ev['kwargs'] else ""

            f = ev['function']
            if hide_modules:
                f = f.split(".")[-1]
            return f"{f}({args})"

        reorder(None)

        return [(cid2func(k), list(map(cid2func, v))) for k, v in ordered_graph]

    def __init__(self, path: str, mocker: Callable = None, obj: object = None, verbose: bool = False, re_init_cls=True):
        if re_init_cls:
            MockTrace.events = {}
            MockTrace.call_stack = []
            MockTrace.call_graph = defaultdict(list)

        self.obj = obj

        self.path = path
        cls, func = self._func_or_method(path)
        self.mocked_class = cls
        self.mocked_func = func.__name__

        if mocker is None:
            mocker = self._passthru(path, verbose=verbose)
        self.mocker = mocker
        self.verbose = verbose

        self.calls_count = 0

    def __str__(self):
        return f"MockTrace(function={self.path}, mocker={self.mocker.__name__}) called {self.calls_count} times"

    @classmethod
    def _passthru(cls, path: str, verbose: bool = False):
        _, func = cls._func_or_method(path)
        return func

    @classmethod
    def _func_or_method(cls, path):
        splits = path.split('.')
        mod, func = '.'.join(splits[:-1]), splits[-1]
        try:
            func = getattr(importlib.import_module(mod), func)
            return None, func
        except ModuleNotFoundError:
            splits = mod.split('.')
            mod, cls = '.'.join(splits[:-1]), splits[-1]
            cls = getattr(importlib.import_module(mod), cls)
            method = getattr(cls, func)

            return cls, method

    def __call__(self, *args, **kwargs):
        parent_id = self.call_stack[-1] if self.call_stack else None
        caller_id = uuid.uuid4()
        self.call_stack.append(caller_id)
        self.call_graph[parent_id].append(caller_id)
        return_value = self.mocker(self.obj, *args, **kwargs) if self.obj else self.mocker(*args, **kwargs)
        event = {
            'caller_id': caller_id,
            'function': self.path,
            'mocker': f"{self.mocker.__module__}.{self.mocker.__name__}",
            'args': args,
            'kwargs': kwargs,
            'return_value': return_value,
        }
        if self.verbose:
            print(f'event={event}')

        self.calls_count += 1
        self.events[caller_id] = event
        assert caller_id == self.call_stack.pop()
        return return_value

    @classmethod
    def patch(cls, path: str, mocker: Callable = None, obj: object = None, verbose: bool = False):
        mt = cls(path, mocker=mocker, obj=obj, verbose=verbose)
        if mt.mocked_class:
            # return mock.patch(mt.mocked_class, mt.mocked_func, side_effect=mt)
            return mock.patch(mt.path, mt)

        return mock.patch(mt.path, mt)
