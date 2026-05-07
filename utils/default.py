import json
import traceback
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from typing import Any


CONFIG_PATH = Path("config.json")


def json_to_namespace(data: Any) -> Any:
    """
    Recursively convert dictionaries into SimpleNamespace objects.
    """

    if isinstance(data, dict):
        return SimpleNamespace(
            **{
                key: json_to_namespace(value)
                for key, value in data.items()
            }
        )

    if isinstance(data, list):
        return [json_to_namespace(item) for item in data]

    return data


@lru_cache(maxsize=1)
def load_config() -> SimpleNamespace:
    """
    Load and cache the application config file.

    Returns:
        SimpleNamespace:
            Parsed configuration object.

    Raises:
        FileNotFoundError:
            If config.json does not exist.

        ValueError:
            If the JSON format is invalid.
    """

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {CONFIG_PATH}"
        )

    try:
        with CONFIG_PATH.open(
            mode="r",
            encoding="utf-8"
        ) as config_file:
            config_data = json.load(config_file)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON format in {CONFIG_PATH}: {error}"
        ) from error

    return json_to_namespace(config_data)


def format_traceback(
    error: Exception,
    advanced: bool = True
) -> str:
    """
    Return a formatted traceback string.

    Args:
        error (Exception):
            The exception to format.

        advanced (bool):
            If True, returns full traceback.
            Otherwise returns a short error message.

    Returns:
        str:
            Formatted traceback output.
    """

    if not advanced:
        return f"{type(error).__name__}: {error}"

    traceback_output = "".join(
        traceback.format_exception(
            type(error),
            error,
            error.__traceback__,
        )
    )

    return f"```py\n{traceback_output}\n```"


def is_owner(ctx: Any) -> bool:
    """
    Check whether the command author is a bot owner.

    Args:
        ctx:
            Discord command context object.

    Returns:
        bool:
            True if the author is an owner.
    """

    config = load_config()

    owners = getattr(config, "owners", [])

    return ctx.author.id in owners


def reload_config() -> SimpleNamespace:
    """
    Clear cached config and reload it.

    Returns:
        SimpleNamespace:
            Reloaded configuration object.
    """

    load_config.cache_clear()

    return load_config()
