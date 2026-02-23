from .fastapi_react_monorepo import FastAPIReactMonorepoAdapter
from .python_pytest import PythonPytestAdapter
from .rust_cargo import RustCargoAdapter
from .node_ts import NodeAdapter

ALL_ADAPTERS = [
    # More specific adapters first
    FastAPIReactMonorepoAdapter(),
    PythonPytestAdapter(),
    RustCargoAdapter(),
    NodeAdapter(),
]
