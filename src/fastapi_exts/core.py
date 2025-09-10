import logging
from collections.abc import Sequence
from typing import (
    Final,
    NamedTuple,
    NotRequired,
    ParamSpec,
    Protocol,
    TypedDict,
)

from fastapi import FastAPI


P = ParamSpec("P")

logger = logging.getLogger("fastapi-exts")


class DependencyInfo(TypedDict):
    name: str
    required: NotRequired[bool]


class ExtensionProtocol(Protocol):
    name: str

    def setup(self, app: FastAPI) -> None: ...


class ExtensionWithDepsProtocol(ExtensionProtocol):
    dependencies: Sequence[DependencyInfo]


class _AnalyzeResult(NamedTuple):
    init_order: list[str]
    missing_optional: list[str]


class _ExtensionDependencyResolver:
    """扩展依赖解析器"""

    def __init__(self, extensions: dict[str, ExtensionProtocol]):
        self.extensions = extensions
        self._dependency_graph: dict[str, list[str]] = {}
        self._dependency_info: dict[str, list[DependencyInfo]] = {}
        self._cached = None

    def __call__(self) -> _AnalyzeResult:
        self._build_dependency_graph()

        missing_required, missing_optional = self._check_missing_dependencies()

        if missing_required:
            msg = f"Missing required dependencies: {missing_required}"
            raise RuntimeError(msg)

        init_order = self._topological_sort()

        result = _AnalyzeResult(init_order, missing_optional)
        self._cached = result

        return result

    def _build_dependency_graph(self) -> None:
        """构建依赖图"""
        for ext_name, extension in self.extensions.items():
            self._dependency_graph[ext_name] = []

            deps: list = list(getattr(extension, "dependencies", ()))
            self._dependency_info[ext_name] = deps

            for dep in deps:
                if dep["name"] in self.extensions:
                    self._dependency_graph[ext_name].append(dep["name"])

    def _check_missing_dependencies(self) -> tuple[list[str], list[str]]:
        """检查缺失的依赖"""
        missing_required = []
        missing_optional = []

        for ext_name, deps in self._dependency_info.items():
            for dep in deps:
                name = dep["name"]
                if name not in self.extensions:
                    if dep.get("required"):
                        missing_required.append(f"{ext_name} -> {name}")
                    else:
                        missing_optional.append(f"{ext_name} -> {name}")
                        msg = (
                            f"Optional dependency '{name}' "
                            f"not found for {ext_name}"
                        )
                        logger.warning(msg)

        return missing_required, missing_optional

    def _topological_sort(self) -> list[str]:
        visited = set()
        temp_visited = set()
        order = []

        def visit(ext_name: str, path: list[str]):
            if ext_name in temp_visited:
                cycle = " -> ".join([*path[path.index(ext_name) :], ext_name])
                msg = f"Circular dependency detected: {cycle}"
                raise RuntimeError(msg)

            if ext_name in visited:
                return

            temp_visited.add(ext_name)
            path.append(ext_name)

            for dep_name in self._dependency_graph.get(ext_name, []):
                visit(dep_name, path.copy())

            temp_visited.remove(ext_name)
            visited.add(ext_name)
            order.append(ext_name)

        # 访问所有扩展
        for ext_name in self.extensions:
            if ext_name not in visited:
                visit(ext_name, [])

        return order


class ExtensionManager:
    STATE_KEY: Final[str] = "fastapi_extension_manager"

    def __init__(self) -> None:
        self._extensions: dict[str, ExtensionProtocol] = {}
        self._deps_resolver = _ExtensionDependencyResolver(self._extensions)

    def get(self, name: str):
        return self._extensions.get(name)

    def register(self, extension: ExtensionProtocol):
        self._extensions.update({extension.name: extension})
        return self

    def remove(self, extension: ExtensionProtocol):
        self._extensions.pop(extension.name)

    def list(self):
        return list(self._extensions)

    def install(self, app: FastAPI):
        exts, _missing_options = self._deps_resolver()
        setattr(app.state, self.STATE_KEY, self)

        for e in exts:
            ext = self._extensions[e]
            logger.info(f"Setting up extension '{ext.name}'")
            ext.setup(app)
            logger.debug(f"Extension '{ext.name}' setup completed")

        logger.info(f"Successfully initialized {len(exts)} extensions")
