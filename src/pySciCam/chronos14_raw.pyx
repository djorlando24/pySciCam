# -*- coding: UTF-8 -*-
"""
    Read monochrome 12-bit and 16-bit RAW files from Chronos 1.4 cameras.
    Chronos 1.4 software 0.2.3 beta.

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2017 LTRAC
    @license GPL-3.0+
    @version 0.1.0
    @date 30/12/2017

    Currently, software 0.2.3 beta is supported (little-endian, no header frame).

    Please see help(pySciCam) for more information.
"""
from __future__ import division

__author__="Daniel Duke <daniel.duke@monash.edu>"
__version__="0.1.0"
__license__="GPL-3.0+"
__copyright__="Copyright (c) 2017 LTRAC"

import numpy as np
import os
import time
cimport cython
cimport numpy as np
from libc.math cimport floor, ceil
from libc.stdio cimport FILE, fopen, fclose, fread, fseek, SEEK_END, SEEK_SET
from libc.stdlib cimport malloc, free
cdef FILE * cfile

# this is the type of the output array.
# should be 16 bit or greater.
DTYPE = np.uint16
ctypedef np.uint16_t DTYPE_t

@cython.cdivision(True)
#@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
def read_chronos_raw(filename, int width, int height, tuple frames=None, int bits_per_pixel=12, int quiet = 0):

    cdef long t0 = time.time()
    cdef double bytes_per_pixel = bits_per_pixel/8.0

    # width and height MUST be specified.
    if (width is None) or (height is None):
        raise ValueError("RAW reader requires height and width")

    # Get size of binary file before we start reading
    # (it might be smaller than we think)
    cdef long nbytes = os.path.getsize(filename)

    # Given the supplied width and height, determine number of frames
    cdef int nframes =  int(floor(nbytes/bytes_per_pixel/width/height))

    if nframes < 1 : raise IOError("File has no frames at specified resolution")

    if quiet == 0: print "File contains %i frames (%i x %i)" % (nframes,width,height)
    cdef int remainder_bytes = np.mod(nbytes,bytes_per_pixel*width*height)
    if remainder_bytes > 0:
        print "Incomplete file truncated - %i bytes at end of file ignored" % remainder_bytes

    # Limit number of frames loaded from file (good for testing)
    cdef int start = 0 # bytes
    cdef int end = nbytes
    if frames is not None:
        if frames[1] > 0:
            start = int(height*width*bytes_per_pixel*frames[0])
            end = int(height*width*bytes_per_pixel*frames[1])
        if start > nbytes:
            raise ValueError("frame range: Cannot start reading beyond end of file!")
        if end > nbytes:
            print "Warning: requested number of frames too large, truncating"
            end = nbytes
        if quiet == 0: print "Reading frames %i to %i" % frames
        nframes = frames[1]-frames[0]

    # make new image array (flattened)
    cdef np.ndarray[DTYPE_t, ndim=1] images = np.zeros(int(nframes*height*width),dtype=DTYPE)

    # read array in
    cdef int i
    cdef int npixels = int(ceil((end-start)/bytes_per_pixel))
    filename_byte_string = filename.encode("UTF-8")
    cdef char * fname = filename_byte_string
    cdef unsigned char * buffer = <unsigned char*>malloc(3)
    cdef unsigned int mb
    cfile = fopen(fname, "rb")
    if cfile:
        if start>0: fseek (cfile, start, SEEK_SET)
        if bits_per_pixel==12: # loop every 3 bytes, write 2 pixels
            for i in xrange(0,len(images),2):
                fread (&buffer, 1, 3, cfile)
                mb = <int>buffer
                images[i]   = <DTYPE_t>(((mb & 0xFF) << 4) | ((mb & 0xF000) >> 12)  )
                images[i+1] = <DTYPE_t>(((mb & 0xFF0000) >> 16) | (mb & 0xF00) )
        elif bits_per_pixel==16: # loop every 2 bytes, write 1 pixel
            for i in xrange(0,len(images)):
                fread (&buffer, 1, 2, cfile)
                mb = <int>buffer
                images[i]   = <DTYPE_t>(mb & 0xFFFF)

    fclose(cfile)

    if quiet == 0: print 'Read %.1f MiB in %.1f sec' % ((end-start)/1048576,time.time()-t0)

    # Return 3D array (un-flatten the output)
    return images.reshape((nframes,height,width))

