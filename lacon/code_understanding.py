"""Code understanding: extract meaningful elements from source code using AST."""

import ast
from dataclasses import dataclass
from typing import List, Optional, Set


@dataclass(frozen=True)
class CodeElement:
    """A meaningful element extracted from code."""
    kind: str          # "function", "class", "import", "variable"
    name: str
    signature: str     # e.g., "def foo(a: int) -> str:"
    docstring: str     # empty if none
    line: int
    end_line: int


def extract_code_elements(source: str) -> List[CodeElement]:
    """Extract meaningful code elements from Python source."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    
    elements = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            sig = _func_signature(node)
            doc = ast.get_docstring(node) or ""
            elements.append(CodeElement(
                kind="function",
                name=node.name,
                signature=sig,
                docstring=doc,
                line=node.lineno,
                end_line=node.end_lineno or node.lineno,
            ))
        elif isinstance(node, ast.AsyncFunctionDef):
            sig = _func_signature(node, async_=True)
            doc = ast.get_docstring(node) or ""
            elements.append(CodeElement(
                kind="function",
                name=node.name,
                signature=sig,
                docstring=doc,
                line=node.lineno,
                end_line=node.end_lineno or node.lineno,
            ))
        elif isinstance(node, ast.ClassDef):
            bases = [b.id if isinstance(b, ast.Name) else str(b) for b in node.bases]
            sig = f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}"
            doc = ast.get_docstring(node) or ""
            elements.append(CodeElement(
                kind="class",
                name=node.name,
                signature=sig,
                docstring=doc,
                line=node.lineno,
                end_line=node.end_lineno or node.lineno,
            ))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                elements.append(CodeElement(
                    kind="import",
                    name=alias.name,
                    signature=f"import {alias.name}",
                    docstring="",
                    line=node.lineno,
                    end_line=node.lineno,
                ))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                elements.append(CodeElement(
                    kind="import",
                    name=alias.name,
                    signature=f"from {module} import {alias.name}",
                    docstring="",
                    line=node.lineno,
                    end_line=node.lineno,
                ))
    
    return elements


def _func_signature(node: ast.FunctionDef, async_: bool = False) -> str:
    """Generate a readable function signature."""
    parts = []
    if async_:
        parts.append("async")
    parts.append("def")
    parts.append(node.name + "(")
    
    args = []
    for arg in node.args.args:
        arg_str = arg.arg
        if arg.annotation:
            arg_str += f": {ast.unparse(arg.annotation)}"
        args.append(arg_str)
    if node.args.vararg:
        args.append("*" + node.args.vararg.arg)
    if node.args.kwarg:
        args.append("**" + node.args.kwarg.arg)
    parts.append(", ".join(args) + ")")
    
    if node.returns:
        parts.append(f" -> {ast.unparse(node.returns)}")
    parts.append(":")
    
    return " ".join(parts)


def code_to_sentences(source: str) -> List[str]:
    """Convert code into meaningful sentences for the engine.
    
    Each code element becomes a sentence describing it.
    """
    elements = extract_code_elements(source)
    sentences = []
    
    for elem in elements:
        if elem.kind == "function":
            doc = f" {elem.docstring}" if elem.docstring else ""
            sentences.append(f"Function {elem.signature}{doc}")
        elif elem.kind == "class":
            doc = f" {elem.docstring}" if elem.docstring else ""
            sentences.append(f"Class {elem.signature}{doc}")
        elif elem.kind == "import":
            sentences.append(f"Import {elem.signature}")
    
    return sentences


def is_code_context(text: str) -> bool:
    """Heuristic: does the text look like Python code?
    
    Uses stricter patterns to avoid false positives on natural language.
    """
    # Must have at least one strong code indicator at start of line or after newline
    lines = text.splitlines()
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith(("def ", "class ", "import ", "async def ")):
            return True
        # "from ... import" pattern
        if stripped.startswith("from ") and " import " in stripped:
            return True
        # lambda at start of line (rare in natural language)
        if stripped.startswith("lambda "):
            return True
    return False