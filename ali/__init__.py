

import importlib

import sys
from os.path import dirname, basename, isfile
import glob
modules = glob.glob(dirname(__file__)+"/*.py")
__all__ = [basename(f)[:-3] for f in modules if isfile(f) and not basename(f).startswith('__')]  # exclude __init__.py
from . import *
# print(__all__)


def reload():
    for module in list(sys.modules.values()):
        if 'ali.' in f'{module}':
            # print(module)
            importlib.reload(module)
