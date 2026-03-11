import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACT_DIR = PROJECT_ROOT / "artifacts"


def save_artifact(stage: str, name: str, data: dict):
    """
    Save structured artifact as JSON.
    """
    stage_dir = ARTIFACT_DIR / stage
    stage_dir.mkdir(parents=True, exist_ok=True)

    path = stage_dir / f"{name}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return path


def load_artifact(stage: str, name: str):
    """
    Load artifact JSON.
    """
    path = ARTIFACT_DIR / stage / f"{name}.json"

    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)