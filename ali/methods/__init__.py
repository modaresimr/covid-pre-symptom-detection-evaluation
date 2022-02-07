import sys
import importlib
from os.path import dirname, basename, isfile
import glob
modules = glob.glob(dirname(__file__)+"/*.py")
__all__ = [basename(f)[:-3] for f in modules if isfile(f) and not basename(f).startswith('__')]  # exclude __init__.py
# importlib.import_module(__all__[0])

from . import * 

