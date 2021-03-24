from collections import defaultdict
import importlib
import mock
from typing import Callable
import uuid


def stringify(obj: object) -> str:
    if isinstance(obj, list):
        return [stringify(o) for o in obj]

    if isinstance(obj, dict):
        return {str(k): stringify(v) for k, v in obj.items()}

    if isinstance(obj, tuple):
        return [stringify(o) for o in obj]

    return str(obj)


class MockTrace:
    events = {}
    call_stack = []
    call_graph = defaultdict(list)

    @classmethod
    def calls_count(cls):
        return sum(len(v) for v in cls.call_graph.values())

    @classmethod
    def graph_shape(cls) -> list:
        def cid2func(cid):
            if cid is None:
                return None

            ev = cls.events[cid]
            args = ev['args'] if ev['args'] else ""
            args += ev['kwargs'] if ev['kwargs'] else ""
            return f"{ev['function']}({args})"

        ordered_graph = []
        call_graph = cls.call_graph.copy()

        def reorder(from_vertex):
            if from_vertex not in call_graph:
                return
            next_vs = call_graph.pop(from_vertex)
            ordered_graph.append((from_vertex, next_vs))
            for v in next_vs:
                reorder(v)
        reorder(None)
        return [(cid2func(k), list(map(cid2func, v))) for k, v in ordered_graph]

    def __init__(self, path: str, mocker: Callable = None, verbose: bool = False, re_init_cls=True):
        if re_init_cls:
            MockTrace.events = {}
            MockTrace.call_stack = []
            MockTrace.call_graph = defaultdict(list)

        self.path = path
        if mocker is None:
            mocker = self._passthru(path, verbose=verbose)
        self.mocker = mocker
        self.verbose = verbose

    @classmethod
    def _passthru(cls, path: str, verbose: bool = False):
        splits = path.split('.')
        mod, func = '.'.join(splits[:-1]), splits[-1]
        func = getattr(importlib.import_module(mod), func)

        return func

    def __call__(self, *args, **kwargs):
        parent_id = self.call_stack[-1] if self.call_stack else None
        caller_id = uuid.uuid4()
        self.call_stack.append(caller_id)
        self.call_graph[parent_id].append(caller_id)
        return_value = self.mocker(*args, **kwargs)
        event = {
            'caller_id': caller_id,
            'function': self.path,
            'mocker': f"{self.mocker.__module__}.{self.mocker.__name__}",
            'args': stringify(args),
            'kwargs': stringify(kwargs),
            'return_value': stringify(return_value),
        }
        if self.verbose:
            print(f'event={event}')

        self.events[caller_id] = event
        assert caller_id == self.call_stack.pop()
        return return_value

    @classmethod
    def patch(cls, path: str, mocker: Callable = None, verbose: bool = False):
        mt = cls(path, mocker=mocker, verbose=verbose)
        return mock.patch(mt.path, mt)


class FunctionTracer:
    history = []

    def __init__(self, func, mocked, verbose=False):
        FunctionTracer.history = []
        self.mocked = mocked
        self.func = func
        self.calls = []
        self.verbose = verbose

    def num_calls(self):
        return len(self.calls)

    def __call__(self, *args, **kwargs):
        return_value = self.func(*args, **kwargs)
        event = {
            'function': self.mocked,
            'mocker': self.func.__name__,
            'args': stringify(args),
            'kwargs': stringify(kwargs),
            'return_value': stringify(return_value),
        }
        FunctionTracer.history.append(event)
        self.calls.append(event)
        if self.verbose:
            print("event=%s" % event)
        return return_value

    def __str__(self):
        return "FunctionTracer(function={0.func.__name__}) called {1} times. Call History: {0.calls}".format(self, self.num_calls())
