from flake8.formatting import base
import importlib_metadata
import os


class Plugin(base.BaseFormatter):
    name = "flake8-bbannotations"
    version = importlib_metadata.version(__name__)