import json
import os

# wildcards retrieval

WILDCARDS_DIR = os.environ.get(
    "WILDCARDS_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "wildcards"),
)

_wildcard_cache: dict[str, list[str]] = {}


def _load_wildcard(name: str) -> list[str]:
    if name in _wildcard_cache:
        return _wildcard_cache[name]
    path = os.path.join(WILDCARDS_DIR, f"{name}.txt")
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        _wildcard_cache[name] = lines
        return lines
    _wildcard_cache[name] = []
    return []


def resolve_wildcards(text: str, seed: int = -1) -> str:
    """Recursively expand __wildcard__ tokens in text."""
    if not text:
        return text
    rng = random.Random(seed) if seed >= 0 else random.Random()

    def _expand(t: str, depth: int = 0) -> str:
        if depth > 16:
            return t
        pattern = r"__([a-zA-Z0-9_/\-]+)__"
        def _replace(m):
            entries = _load_wildcard(m.group(1))
            if not entries:
                return m.group(0)  # leave token intact if file missing
            chosen = rng.choice(entries)
            return _expand(chosen, depth + 1)
        return re.sub(pattern, _replace, t)

    return _expand(text)


# load line from file

