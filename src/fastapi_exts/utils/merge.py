from collections.abc import Iterable, Mapping
from typing import overload


def _merge_dict(
    target: dict,
    source: Mapping,
):
    for ok, ov in source.items():
        v = target.get(ok)
        # 如果两边都是映射类型, 就可以合并
        if isinstance(v, dict) and isinstance(ov, Mapping):
            _merge_dict(v, ov)
        elif isinstance(v, list) and isinstance(ov, Iterable):
            _merge_list(v, ov)
        # 如果当前值允许进行相加的操作
        # 并且不是字符串和数字
        # 并且旧字典与当前值类型相同
        elif (
            hasattr(v, "__add__")
            and not isinstance(v, str | int)
            and type(v) is type(ov)
        ):
            target[ok] = v + ov
        # 否则使用有效的值
        else:
            target[ok] = v or ov


def _merge_list(target: list, source: Iterable):
    for oi, ov in enumerate(source):
        try:
            v = target[oi]
        except IndexError:
            target[oi] = ov
            break

        if isinstance(v, dict) and isinstance(ov, Mapping):
            merge(v, ov)

        elif isinstance(v, list) and isinstance(ov, Iterable):
            _merge_list(v, ov)
        # 如果当前值允许进行相加的操作
        # 并且不是字符串和数字
        # 并且旧字典与当前值类型相同
        elif (
            hasattr(v, "__add__")
            and not isinstance(v, str | int)
            and type(v) is type(ov)
        ):
            target[oi] = v + ov
        else:
            target[oi] = v or ov


@overload
def merge(target: list, source: Iterable): ...
@overload
def merge(target: dict, source: Mapping): ...


def merge(target, source):
    for ok, ov in source.items():
        v = target.get(ok)

        # 如果两边都是映射类型, 就可以合并
        if isinstance(v, dict) and isinstance(ov, Mapping):
            _merge_dict(v, ov)
        elif isinstance(v, list) and isinstance(ov, Iterable):
            _merge_list(v, ov)
        # 如果当前值允许进行相加的操作
        # 并且不是字符串和数字
        # 并且旧字典与当前值类型相同
        elif (
            hasattr(v, "__add__")
            and not isinstance(v, str | int)
            and type(v) is type(ov)
        ):
            target[ok] = v + ov

        # 否则使用有效的值
        else:
            target[ok] = v or ov
