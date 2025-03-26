"""Build a markdown file and summary for all Python files in the module."""

from pathlib import Path

import mkdocs_gen_files


def main() -> None:
    """Generate API documentation for all files."""
    nav = mkdocs_gen_files.Nav()

    root = Path(__file__).parent.parent
    src_root = root / "ember_mug"

    for path in sorted(src_root.rglob("*.py")):
        module_path = path.relative_to(src_root).with_suffix("")
        doc_path = path.relative_to(src_root).with_suffix(".md")
        full_doc_path = Path("api", doc_path)
        parts = tuple(module_path.parts)

        # __init__ should create index
        if parts[-1] == "__init__":
            parts = parts[:-1]
            doc_path = doc_path.with_name("index.md")
            full_doc_path = full_doc_path.with_name("index.md")

        # Ignore __init__ and __main__ files
        elif parts[-1].startswith("__"):
            continue

        nav_parts = [f"{part}.py" for part in parts]
        if not nav_parts:
            continue

        nav[tuple(nav_parts)] = doc_path.as_posix()

        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            ident = ".".join(parts)
            fd.write(f"---\ntitle: {ident}\n---\n\n::: {ident}")

        mkdocs_gen_files.set_edit_path(full_doc_path, ".." / path.relative_to(root))

    with mkdocs_gen_files.open("api/SUMMARY.md", "w") as nav_file:
        nav_file.writelines(nav.build_literate_nav())


main()
