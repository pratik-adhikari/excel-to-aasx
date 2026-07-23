"""Excel-to-AASX generation pipeline."""

try:
    from importlib.metadata import PackageNotFoundError, version as _version
    __version__ = _version("excel-to-aasx")
except PackageNotFoundError:
    # Source checkouts may be imported before the editable package is installed.
    __version__ = "unknown"
