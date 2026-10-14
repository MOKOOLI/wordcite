"""A tiny template language for bibliography entries.

    {var}        insert variable              {var|i} italic  {var|b} bold
    {a+b}        join the non-empty values of a and b with ", "
    {t:term}     insert a localised term ({t:Term} capitalises it)
    <...>        group: rendered only if every variable directly inside it is non-empty
                 (a group without variables renders if any child group rendered)
    \\<  \\{      literal characters

Example (Vancouver journal article):
    <{authors}. ><{title}. ><{container_short}. ><{year}><;{volume}><({issue})><:{pages}>.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Union

from .richtext import RichText


@dataclass
class Text:
    text: str


@dataclass
class Var:
    name: str
    fmt: frozenset


@dataclass
class Group:
    children: List["Node"] = field(default_factory=list)


Node = Union[Text, Var, Group]

_FMT = {"i": "i", "b": "b", "sup": "sup"}


def parse(template: str) -> List[Node]:
    stack: List[List[Node]] = [[]]
    buf: List[str] = []

    def flush():
        if buf:
            stack[-1].append(Text("".join(buf)))
            buf.clear()

    i = 0
    while i < len(template):
        c = template[i]
        if c == "\\" and i + 1 < len(template):
            buf.append(template[i + 1])
            i += 2
            continue
        if c == "<":
            flush()
            stack.append([])
        elif c == ">":
            flush()
            if len(stack) == 1:
                raise ValueError(f"unbalanced '>' in template: {template}")
            children = stack.pop()
            stack[-1].append(Group(children))
        elif c == "{":
            flush()
            j = template.index("}", i)
            spec = template[i + 1:j]
            name, _, fmt = spec.partition("|")
            flags = frozenset(_FMT[f] for f in fmt.split(",") if f)
            stack[-1].append(Var(name.strip(), flags))
            i = j
        else:
            buf.append(c)
        i += 1
    flush()
    if len(stack) != 1:
        raise ValueError(f"unclosed '<' in template: {template}")
    return stack[0]


def _lookup(name: str, values: Dict[str, str]) -> str:
    if "+" in name:
        return ", ".join(v for v in (values.get(n.strip(), "") for n in name.split("+")) if v)
    return values.get(name, "") or ""


def _render(nodes: List[Node], values: Dict[str, str], term: Callable[[str], str],
            is_group: bool) -> Optional[RichText]:
    out = RichText()
    direct_vars = 0
    missing = False
    has_groups = False
    any_child = False
    for node in nodes:
        if isinstance(node, Text):
            out.append(node.text)
        elif isinstance(node, Var):
            if node.name.startswith("t:"):
                out.append(term(node.name[2:]), node.fmt)
                continue
            direct_vars += 1
            val = _lookup(node.name, values)
            if not val:
                missing = True
            else:
                out.append(val, node.fmt)
        else:
            has_groups = True
            sub = _render(node.children, values, term, True)
            if sub is not None:
                any_child = True
                out.extend(sub)
    if is_group:
        if direct_vars and missing:
            return None
        if not direct_vars and has_groups and not any_child:
            return None
    return out


def render(nodes: List[Node], values: Dict[str, str], term: Callable[[str], str]) -> RichText:
    return _render(nodes, values, term, False) or RichText()
