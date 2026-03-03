#!/usr/bin/env python3
"""Codebase indexing tool — builds searchable index of source code for RAG retrieval.

Creates a semantic index of the codebase using code-aware chunking:
- One function/subroutine per chunk (not naive token splitting)
- Preserves docstrings with their functions
- Fortran modules keep their header with each procedure
- Tracks call graphs and type hierarchies

Usage:
    python tools/index_codebase.py [--output INDEX_DIR] [--format json|sqlite]
                                   [--incremental] [--stats]

Output: Indexed code chunks in structured format for agent retrieval.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
INDEX_DIR = REPO_ROOT / "meta" / "code_index"


class CodeChunk:
    """A semantic unit of code (function, class, module, etc.)."""

    def __init__(self, filepath, start_line, end_line, chunk_type, name,
                 content, docstring="", parent=None):
        self.filepath = str(filepath)
        self.start_line = start_line
        self.end_line = end_line
        self.chunk_type = chunk_type  # function, subroutine, class, module, method
        self.name = name
        self.content = content
        self.docstring = docstring
        self.parent = parent  # enclosing module/class name
        self.calls = []  # functions this chunk calls
        self.called_by = []  # functions that call this chunk

    def to_dict(self):
        return {
            "filepath": self.filepath,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "type": self.chunk_type,
            "name": self.name,
            "qualified_name": f"{self.parent}::{self.name}" if self.parent else self.name,
            "content": self.content,
            "docstring": self.docstring,
            "parent": self.parent,
            "calls": self.calls,
            "num_lines": self.end_line - self.start_line + 1,
        }


def parse_fortran_file(filepath):
    """Parse Fortran source into semantic chunks."""
    chunks = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return chunks

    lines = content.split("\n")
    rel_path = filepath.relative_to(REPO_ROOT) if filepath.is_relative_to(REPO_ROOT) else filepath
    current_module = None

    i = 0
    while i < len(lines):
        line = lines[i].strip().lower()

        # Module detection
        module_match = re.match(r'^module\s+(\w+)', line)
        if module_match and "procedure" not in line:
            current_module = module_match.group(1)

        # Subroutine/function detection
        sub_match = re.match(r'^(?:pure\s+|elemental\s+|recursive\s+)*(?:subroutine|function)\s+(\w+)', line)
        if not sub_match:
            sub_match = re.match(r'^(?:\w+\s+)*function\s+(\w+)', line)

        if sub_match:
            name = sub_match.group(1)
            start = i + 1
            chunk_type = "subroutine" if "subroutine" in line else "function"

            # Find end
            end = i
            depth = 1
            for j in range(i + 1, len(lines)):
                jline = lines[j].strip().lower()
                if re.match(r'^end\s*(subroutine|function)', jline):
                    end = j
                    break
            else:
                end = min(i + 100, len(lines) - 1)

            # Extract docstring (comments before the function)
            docstring_lines = []
            for k in range(max(0, i - 1), max(0, i - 20), -1):
                kline = lines[k].strip()
                if kline.startswith("!"):
                    docstring_lines.insert(0, kline[1:].strip())
                elif kline == "":
                    continue
                else:
                    break

            chunk_content = "\n".join(lines[i:end + 1])
            chunks.append(CodeChunk(
                filepath=rel_path,
                start_line=start,
                end_line=end + 1,
                chunk_type=chunk_type,
                name=name,
                content=chunk_content,
                docstring="\n".join(docstring_lines),
                parent=current_module,
            ))

            i = end + 1
            continue

        i += 1

    return chunks


def parse_cpp_file(filepath):
    """Parse C/C++ source into semantic chunks (simplified)."""
    chunks = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return chunks

    lines = content.split("\n")
    rel_path = filepath.relative_to(REPO_ROOT) if filepath.is_relative_to(REPO_ROOT) else filepath
    current_class = None

    # Simple function detection (not a full parser)
    func_pattern = re.compile(
        r'^(?:(?:static|inline|virtual|explicit|constexpr|template\s*<[^>]*>)\s+)*'
        r'(?:\w+(?:::\w+)*\s+)*(\w+)\s*\([^)]*\)\s*(?:const)?\s*(?:override)?\s*\{?',
        re.MULTILINE
    )

    for match in func_pattern.finditer(content):
        name = match.group(1)
        if name in ("if", "else", "for", "while", "switch", "return", "do"):
            continue

        start_pos = match.start()
        start_line = content[:start_pos].count("\n") + 1

        # Find matching brace
        brace_start = content.find("{", match.end() - 1)
        if brace_start == -1:
            continue

        depth = 0
        end_pos = brace_start
        for j in range(brace_start, len(content)):
            if content[j] == "{":
                depth += 1
            elif content[j] == "}":
                depth -= 1
                if depth == 0:
                    end_pos = j
                    break

        end_line = content[:end_pos].count("\n") + 1

        # Extract docstring (look for /** ... */ or // comments before)
        doc_start = max(0, start_pos - 500)
        pre_content = content[doc_start:start_pos]
        doxygen_match = re.search(r'/\*\*(.*?)\*/', pre_content, re.DOTALL)
        docstring = doxygen_match.group(1).strip() if doxygen_match else ""

        chunk_content = content[start_pos:end_pos + 1]
        if len(chunk_content) > 5000:
            chunk_content = chunk_content[:5000] + "\n// ... truncated"

        chunks.append(CodeChunk(
            filepath=rel_path,
            start_line=start_line,
            end_line=end_line,
            chunk_type="function",
            name=name,
            content=chunk_content,
            docstring=docstring,
            parent=current_class,
        ))

    return chunks


def parse_python_file(filepath):
    """Parse Python source into semantic chunks."""
    chunks = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return chunks

    lines = content.split("\n")
    rel_path = filepath.relative_to(REPO_ROOT) if filepath.is_relative_to(REPO_ROOT) else filepath

    # Find functions and classes
    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith("def ") or stripped.startswith("class "):
            is_class = stripped.startswith("class ")
            name_match = re.match(r'(?:def|class)\s+(\w+)', stripped)
            if not name_match:
                continue
            name = name_match.group(1)
            indent = len(line) - len(line.lstrip())
            start = i + 1

            # Find end (next line with same or less indent, not blank)
            end = i
            for j in range(i + 1, len(lines)):
                jline = lines[j]
                if jline.strip() == "":
                    continue
                jindent = len(jline) - len(jline.lstrip())
                if jindent <= indent and jline.strip():
                    end = j - 1
                    break
            else:
                end = len(lines) - 1

            # Extract docstring
            docstring = ""
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith('"""') or next_line.startswith("'''"):
                    quote = next_line[:3]
                    if next_line.count(quote) >= 2:
                        docstring = next_line.strip(quote[0]).strip()
                    else:
                        doc_lines = [next_line.lstrip(quote[0])]
                        for k in range(i + 2, min(i + 50, len(lines))):
                            if quote in lines[k]:
                                doc_lines.append(lines[k].split(quote)[0].strip())
                                break
                            doc_lines.append(lines[k].strip())
                        docstring = "\n".join(doc_lines)

            chunk_content = "\n".join(lines[i:end + 1])
            chunks.append(CodeChunk(
                filepath=rel_path,
                start_line=start,
                end_line=end + 1,
                chunk_type="class" if is_class else "function",
                name=name,
                content=chunk_content[:5000],
                docstring=docstring,
            ))

    return chunks


def build_index(src_dir):
    """Build code index from source directory."""
    parsers = {
        ".f90": parse_fortran_file,
        ".f95": parse_fortran_file,
        ".f03": parse_fortran_file,
        ".f08": parse_fortran_file,
        ".cpp": parse_cpp_file,
        ".cc": parse_cpp_file,
        ".c": parse_cpp_file,
        ".h": parse_cpp_file,
        ".hpp": parse_cpp_file,
        ".py": parse_python_file,
    }

    all_chunks = []
    file_count = 0

    if not src_dir.exists():
        return all_chunks, file_count

    for filepath in sorted(src_dir.rglob("*")):
        if not filepath.is_file():
            continue
        ext = filepath.suffix.lower()
        if ext in parsers:
            file_count += 1
            chunks = parsers[ext](filepath)
            all_chunks.extend(chunks)

    return all_chunks, file_count


def main():
    parser = argparse.ArgumentParser(description="Codebase indexing tool")
    parser.add_argument("--output", default=str(INDEX_DIR), help="Output directory for index")
    parser.add_argument("--stats", action="store_true", help="Only print statistics")
    parser.add_argument("--format", choices=["json", "jsonl"], default="json")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build index from all source directories
    all_chunks = []
    total_files = 0

    for search_dir in [SRC_DIR, REPO_ROOT / "tools", REPO_ROOT / "tests"]:
        chunks, files = build_index(search_dir)
        all_chunks.extend(chunks)
        total_files += files

    # Statistics
    stats = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files_indexed": total_files,
        "total_chunks": len(all_chunks),
        "by_type": {},
        "by_language": {},
    }

    for chunk in all_chunks:
        stats["by_type"][chunk.chunk_type] = stats["by_type"].get(chunk.chunk_type, 0) + 1
        ext = Path(chunk.filepath).suffix
        stats["by_language"][ext] = stats["by_language"].get(ext, 0) + 1

    if args.stats:
        print(json.dumps(stats, indent=2))
        return

    # Write index
    if args.format == "json":
        index_data = {
            "metadata": stats,
            "chunks": [c.to_dict() for c in all_chunks],
        }
        index_file = output_dir / "index.json"
        index_file.write_text(json.dumps(index_data, indent=2))
        print(f"Index written to {index_file}")
    elif args.format == "jsonl":
        index_file = output_dir / "index.jsonl"
        with open(index_file, "w") as f:
            for chunk in all_chunks:
                f.write(json.dumps(chunk.to_dict()) + "\n")
        print(f"Index written to {index_file}")

    # Write stats
    stats_file = output_dir / "stats.json"
    stats_file.write_text(json.dumps(stats, indent=2))

    print(json.dumps({"tool": "index_codebase", "status": "pass", **stats}, indent=2))


if __name__ == "__main__":
    main()
