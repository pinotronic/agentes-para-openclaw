from .python_pytest import PythonPytestAdapter
from .rust_cargo import RustCargoAdapter
from .node_ts import NodeAdapter

ALL_ADAPTERS = [
    PythonPytestAdapter(),
    RustCargoAdapter(),
    NodeAdapter(),
]
