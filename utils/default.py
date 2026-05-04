import json
import traceback
from pathlib import Path
from types import SimpleNamespace
from functools import lru_cache


CONFIG_PATH = Path("config.json")


@lru_cache(maxsize=1)
def load_config():
    """Load and cache config.json"""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"{CONFIG_PATH} not found")

    try:
        with CONFIG_PATH.open(encoding="utf-8") as f:
            data = json.load(f)
            return json_to_namespace(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}") from e


def json_to_namespace(data):
    """Recursively convert dicts to SimpleNamespace"""
    if isinstance(data, dict):
        return SimpleNamespace(**{k: json_to_namespace(v) for k, v in data.items()})
    elif isinstance(data, list):
        return [json_to_namespace(i) for i in data]
    return data


def format_traceback(err, advanced: bool = True):
    """Return formatted traceback"""
    if advanced:
        tb = ''.join(traceback.format_exception(type(err), err, err.__traceback__))
        return f"```py\n{tb}\n```"
    return f"{type(err).__name__}: {err}"


def is_owner(ctx):
    """Check if user is in owners list"""
    config = load_config()
    owners = getattr(config, "owners", [])
    return ctx.author.id in owners
