#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Read images from high speed and scientific cameras in Python
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.1.3
    @date 16/6/2018
    
    Please see help(pySciCam) for more information.
"""

__author__="Daniel Duke <daniel.duke@monash.edu>"
__version__="0.1.3"
__license__="GPL-3.0+"
__copyright__="Copyright (c) 2018 LTRAC"


from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
import numpy

long_description = """Scientific and High speed camera file importer for Python. The aim of this code is to get your movie, imageset or binary blob into a usable NumPy array as quickly as possible. Uses a range  of libraries (PythonMagick, imageio, Pillow) to achieve widest compatibility and best performance for generic image and movie formats, with parallel file I/O where possible. Supports custom binary file formats for a range of scientific cameras."""

cython_modules = [
    Extension(
        "pySciCam.chronos14_mono_raw",
        ["src/pySciCam/chronos14_mono_raw.pyx"],
    ),
    Extension(
        "pySciCam.b16_raw",
        ["src/pySciCam/b16_raw.pyx"],
    ),
    Extension(
        "pySciCam.photron_mraw",
        ["src/pySciCam/photron_mraw.pyx"],
    )
]

c_libraries = [
    Extension("libbayer", sources = ["src/bayer/bayer.c"])
]

setup(name="pySciCam",
      version="0.1.0",
      description="Scientific and High speed camera file importer for Python.",
      author="Daniel Duke",
      author_email="daniel.duke@monash.edu",
      license="GPL-3.0+",
      long_description=long_description,
      packages=['pySciCam'],
      package_dir={'': 'src'},
      url='daniel-duke.net',
      install_requires=['numpy','tqdm','natsort','joblib','glob','itertools','ctypes'],
      ext_modules=cythonize(cython_modules) + c_libraries,
      include_dirs=[numpy.get_include()]
)
