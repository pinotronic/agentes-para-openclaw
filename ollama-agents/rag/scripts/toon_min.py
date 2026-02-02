"""Minimal TOON encoder (subset) for uniform arrays + simple objects.

Goal: provide token-efficient, LLM-friendly structured context without heavy deps.
Not a full spec implementation.

Supported:
- dict -> indentation-based mapping
- list[str|int|float|bool] -> name[N]: csv
- list[dict] uniform primitive fields -> name[N]{fields}: rows

Escaping:
- strings containing comma/newline are quoted with double quotes; quotes are escaped.
"""

from __future__ import annotations

from typing import Any


def _is_primitive(x: Any) -> bool:
    return x is None or isinstance(x, (str, int, float, bool))


def _quote(s: str) -> str:
    if s == "":
        return '""'
    needs = ("," in s) or ("\n" in s) or ("\r" in s) or ("\t" in s) or (s.strip() != s)
    if '"' in s:
        s = s.replace('"', '""')
        needs = True
    return f'"{s}"' if needs else s


def _fmt(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return _quote(v)
    # fallback: stringify
    return _quote(str(v))


def toon_object(obj: dict[str, Any], indent: int = 0) -> str:
    pad = " " * indent
    lines: list[str] = []
    for k, v in obj.items():
        if isinstance(v, dict):
            lines.append(f"{pad}{k}:")
            lines.append(toon_object(v, indent=indent + 2))
        elif isinstance(v, list):
            # caller should handle naming; here we just serialize as YAML-ish
            lines.append(f"{pad}{k}:")
            for item in v:
                lines.append(f"{pad}  - {_fmt(item)}")
        else:
            lines.append(f"{pad}{k}: {_fmt(v)}")
    return "\n".join(lines)


def toon_table(name: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return f"{name}[0]{{}}:"  # degenerate

    # Determine uniform primitive fields
    fields = list(rows[0].keys())
    for r in rows:
        if list(r.keys()) != fields:
            raise ValueError("Non-uniform keys; cannot tabularize")
        for v in r.values():
            if not _is_primitive(v):
                raise ValueError("Non-primitive value; cannot tabularize")

    header = f"{name}[{len(rows)}]{{{','.join(fields)}}}:"
    lines = [header]
    for r in rows:
        line = ",".join(_fmt(r[f]) for f in fields)
        lines.append(f"  {line}")
    return "\n".join(lines)


def toon_list(name: str, items: list[Any]) -> str:
    if all(_is_primitive(x) for x in items):
        csv = ",".join(_fmt(x) for x in items)
        return f"{name}[{len(items)}]: {csv}"
    raise ValueError("Only primitive lists supported in toon_list")
