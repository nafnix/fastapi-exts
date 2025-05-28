import ast
import inspect
from collections.abc import Callable, Generator
from functools import partial
from typing import Annotated, TypeGuard, get_args, get_origin

from fastapi import params


def iter_class_functions(
    cls: type,
) -> Generator[tuple[str, Callable], None, None]:
    """迭代类的函数, 并且能够提取父类的函数"""

    yield from inspect.getmembers_static(
        cls,
        lambda obj: (inspect.isfunction(obj) or inspect.ismethod(obj)),
    )


def get_dependency_from_annotated(
    annotated: Annotated,
) -> tuple[type, params.Depends] | None:
    """获取注解中的依赖"""

    args = list(get_args(annotated))
    typ = args[0]
    # 因为 FastAPI 好像也是取最后的依赖运行的, 所以这里也将参数反转
    args.reverse()
    for arg in args:
        if isinstance(arg, params.Depends):
            return typ, arg

    return None


_Dependency = params.Param | params.Body | params.Depends


def _get_class_dependencies(
    cls: type,
) -> dict[
    str,
    tuple[
        _Dependency | inspect.Parameter.empty, type | inspect.Parameter.empty
    ],
]:
    dependencies = dict[
        str,
        tuple[
            _Dependency | inspect.Parameter.empty,
            type | inspect.Parameter.empty,
        ],
    ]()
    annotations = dict[str, type]()

    def is_annotated(obj) -> TypeGuard[Annotated]:
        return get_origin(obj) is Annotated

    for name, type_ in inspect.get_annotations(cls).items():
        if is_annotated(type_) and (
            dependency := get_dependency_from_annotated(type_)
        ):
            dependencies.setdefault(name, (dependency[1], dependency[0]))
        else:
            annotations.setdefault(name, type_)

    for name, obj in inspect.getmembers(cls):
        if isinstance(obj, _Dependency):
            dependencies.setdefault(
                name,
                (obj, annotations.pop(name, inspect.Parameter.empty)),
            )
    for name, typ in annotations.items():
        value = tuple[
            _Dependency | inspect.Parameter.empty,
            type | inspect.Parameter.empty,
        ]([inspect.Parameter.empty, typ])
        dependencies.setdefault(name, value)
    return dependencies


def iter_class_dependency(
    cls: type,
) -> Generator[
    tuple[
        str,
        _Dependency | inspect.Parameter.empty,
        type | inspect.Parameter.empty,
    ],
    None,
    None,
]:
    dependencies = _get_class_dependencies(cls)

    for c in inspect.getmro(cls):
        if c is object:
            return

        source = inspect.getsource(c)
        tree = ast.parse(source)
        class_def = next(
            (i for i in tree.body if isinstance(i, ast.ClassDef)),
            None,
        )

        if class_def is None:
            continue

        for stmt in class_def.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(
                stmt.target, ast.Name
            ):
                token = stmt.target.id
                if token in dependencies:
                    dep, typ = dependencies[token]
                    yield token, dep, typ

            elif (
                isinstance(stmt, ast.Assign)
                and stmt.targets
                and isinstance(stmt.targets[0], ast.Name)
            ):
                token = stmt.targets[0].id
                if token in dependencies:
                    dep, typ = dependencies[token]
                    yield token, dep, typ


class ClassFunctionDecorator:
    # 装饰时执行
    def __init__(self, fn) -> None:
        self.fn = fn

    # cls 执行 __new__ 时执行
    def __set_name__(self, cls: type, name: str): ...

    # 调用时执行
    def __get__(self, instance, cls):
        if isinstance(self.fn, staticmethod):
            return self.fn
        if isinstance(self.fn, classmethod):
            return partial(self.fn.__func__, cls)
        return partial(self.fn, instance)
