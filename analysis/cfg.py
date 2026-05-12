import os
import re
import subprocess
import glob
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class CFGResult:
    generated: bool
    reason: str
    dot_path: Optional[str] = None
    svg_path: Optional[str] = None


def _covered_lines_from_gcov(gcov_path: str) -> Set[int]:
    covered: Set[int] = set()
    if not os.path.exists(gcov_path):
        return covered
    with open(gcov_path, "r", encoding="utf-8") as f:
        for raw in f:
            parts = raw.split(":", 2)
            if len(parts) < 3:
                continue
            count_str = parts[0].strip()
            line_str = parts[1].strip()
            if count_str in {"-", "#####", "====="}:
                continue
            try:
                line_num = int(line_str)
            except ValueError:
                continue
            if line_num == 0:
                continue
            try:
                int(count_str.replace("*", ""))
                covered.add(line_num)
            except ValueError:
                continue
    return covered


def _collect_branch_lines_with_clang(source_file: str) -> Tuple[Optional[List[int]], str]:
    try:
        from clang import cindex
    except Exception:
        return None, "python clang bindings not installed (run: pip install clang)"

    # Make libclang discovery robust on macOS/Homebrew and CI environments.
    try:
        libclang_file = os.environ.get("LIBCLANG_FILE")
        libclang_path = os.environ.get("LIBCLANG_PATH")
        if libclang_file:
            cindex.Config.set_library_file(libclang_file)
        elif libclang_path:
            cindex.Config.set_library_path(libclang_path)
        else:
            candidates: List[str] = []
            # Apple Silicon + Intel Homebrew canonical locations.
            candidates.extend(glob.glob("/opt/homebrew/opt/llvm/lib/libclang.dylib"))
            candidates.extend(glob.glob("/usr/local/opt/llvm/lib/libclang.dylib"))
            # Versioned Cellar installs.
            candidates.extend(sorted(glob.glob("/opt/homebrew/Cellar/llvm/*/lib/libclang.dylib"), reverse=True))
            candidates.extend(sorted(glob.glob("/usr/local/Cellar/llvm/*/lib/libclang.dylib"), reverse=True))
            for cand in candidates:
                if os.path.exists(cand):
                    cindex.Config.set_library_file(cand)
                    break
    except Exception:
        # Fall back to default loader behavior.
        pass

    try:
        idx = cindex.Index.create()
        tu = idx.parse(source_file, args=["-std=c++17"])
    except Exception as exc:
        return None, (
            "clang parse failed. Ensure LLVM/Clang is installed and libclang is discoverable "
            f"(optional env var: LIBCLANG_PATH). Error: {exc}"
        )

    branch_kinds = {
        "IF_STMT",
        "FOR_STMT",
        "WHILE_STMT",
        "DO_STMT",
        "SWITCH_STMT",
        "CONDITIONAL_OPERATOR",
    }

    lines: List[int] = []

    def walk(node):
        kind_name = getattr(node.kind, "name", "")
        if kind_name in branch_kinds:
            loc = node.location
            if loc and getattr(loc, "line", None):
                lines.append(int(loc.line))
        for c in node.get_children():
            walk(c)

    walk(tu.cursor)
    return sorted(set(lines)), "ok"


def _render_cfg_dot(source_file: str, branch_lines: List[int], covered_lines: Set[int], out_dot: str) -> None:
    with open(out_dot, "w", encoding="utf-8") as f:
        f.write("digraph CFG {\n")
        f.write("  rankdir=TB;\n")
        f.write("  node [shape=box, style=rounded, fontname=Helvetica];\n")
        f.write("  entry [label=\"ENTRY\", shape=oval];\n")
        f.write("  exit [label=\"EXIT\", shape=oval];\n")

        prev = "entry"
        if not branch_lines:
            f.write("  n0 [label=\"No branch nodes found\"];\n")
            f.write("  entry -> n0;\n")
            f.write("  n0 -> exit;\n")
        else:
            for i, ln in enumerate(branch_lines):
                node = f"b{i}"
                color = "#16a34a" if ln in covered_lines else "#dc2626"
                label = f"L{ln}: branch"
                f.write(f"  {node} [label=\"{label}\", color=\"{color}\", penwidth=2];\n")
                edge_color = "#16a34a" if ln in covered_lines else "#9ca3af"
                f.write(f"  {prev} -> {node} [color=\"{edge_color}\", penwidth=2];\n")
                prev = node
            f.write(f"  {prev} -> exit;\n")

        f.write("  legend_cov [label=\"Covered branch\", color=\"#16a34a\", shape=box];\n")
        f.write("  legend_uncov [label=\"Uncovered branch\", color=\"#dc2626\", shape=box];\n")
        f.write("}\n")


def generate_cfg_visual(source_file: str, gcov_path: str, output_dir: str) -> CFGResult:
    os.makedirs(output_dir, exist_ok=True)

    branch_lines, reason = _collect_branch_lines_with_clang(source_file)
    if branch_lines is None:
        return CFGResult(generated=False, reason=reason)

    # We infer traversed branches by whether branch line is absent from uncovered lines
    # from latest gcov parsing context. Since that context is upstream, we fallback to
    # highlighting none if unavailable; caller can pass richer data in future.
    covered_lines = _covered_lines_from_gcov(gcov_path)

    base = os.path.splitext(os.path.basename(source_file))[0]
    dot_path = os.path.join(output_dir, f"{base}_cfg.dot")
    svg_path = os.path.join(output_dir, f"{base}_cfg.svg")

    _render_cfg_dot(source_file, branch_lines, covered_lines, dot_path)

    try:
        subprocess.run(["dot", "-Tsvg", dot_path, "-o", svg_path], check=True, capture_output=True, text=True)
    except Exception as exc:
        return CFGResult(generated=False, reason=f"graphviz dot not available: {exc}", dot_path=dot_path)

    return CFGResult(generated=True, reason="ok", dot_path=dot_path, svg_path=svg_path)
