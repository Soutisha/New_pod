import json
from pathlib import Path

GRAPH_DIR = Path(__file__).parent.parent / "knowledge_graph"
GRAPH_DIR.mkdir(exist_ok=True)

NODES_FILE = GRAPH_DIR / "nodes.json"
EDGES_FILE = GRAPH_DIR / "edges.json"


def _load(path):
    if not path.exists():
        return []

    data = json.loads(path.read_text())

    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return [data]
    else:
        return []


def _save(path, data):
    path.write_text(json.dumps(data, indent=2))


def add_node(node):
    path = GRAPH_DIR / "nodes.json"

    if path.exists():
        data = json.loads(path.read_text())
        if not isinstance(data, list):
            data = [data]
    else:
        data = []

    data.append(node)
    path.write_text(json.dumps(data, indent=2))


def add_edge(edge):
    edges = _load(EDGES_FILE)
    edges.append(edge)
    _save(EDGES_FILE, edges)