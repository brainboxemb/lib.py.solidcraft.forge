"""Translate changed paths into module/library execution selection."""
from fnmatch import fnmatchcase
from .config import BuildSelection, full_selection


def changed_selection(*, branch, paths, modules):
    if "ci.yml" in paths:
        return full_selection(branch)
    selected = []
    for module in modules:
        if any(fnmatchcase(path, pattern) for path in paths for pattern in module.watch):
            if module.impact == "full":
                return full_selection(branch)
            selected.append(module.id)
    return BuildSelection(
        branch,
        tuple(sorted(selected)),
        (),
        library=any(path.startswith("cadlib/") for path in paths),
    )
