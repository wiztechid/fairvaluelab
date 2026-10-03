def resolve(snapshot, disclosure=None, **_ignored):
    """Legacy compatibility boundary.

    Single-source filing evidence is no longer authorized to promote PIT quality.
    Kept only so historical callers fail closed without breaking imports.
    """
    return dict(snapshot)
