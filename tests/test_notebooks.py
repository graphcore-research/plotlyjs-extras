from pathlib import Path

import nbformat
from nbclient import NotebookClient


def test_legend_highlight_demo_notebook_runs():
    repo_root = Path(__file__).resolve().parents[1]
    notebook_path = repo_root / "examples" / "legend_highlight_demo.ipynb"

    with notebook_path.open(encoding="utf-8") as handle:
        notebook = nbformat.read(handle, as_version=4)

    client = NotebookClient(
        notebook,
        timeout=180,
        allow_errors=False,
        resources={"metadata": {"path": str(notebook_path.parent)}},
    )
    client.execute()
