# -*- coding: UTF-8 -*-
"""
    Read 8, 12 and 16-bit MRAW files from Photron FastCam Viewer software.

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2024 LTRAC
    @license GPL-3.0+
    @version 0.5.1
    @date 31/08/2024

    Department of Mechanical & Aerospace Engineering
    Monash University, Australia
    
    Please see help(pySciCam) for more information.

"""
from __future__ import division

__author__="Daniel Duke <daniel.duke@monash.edu>"
__version__="0.5"
__license__="GPL-3.0+"
__copyright__="Copyright (c) 2018-2024 D.Duke"

import numpy as np
import os
import time
cimport cython
cimport numpy as np
from libc.math cimport floor, ceil
from libc.stdio cimport FILE, fopen, fclose, fread, fseek, SEEK_END, SEEK_SET, SEEK_CUR
from libc.stdlib cimport malloc, free
cdef FILE * cfile

# this is the type of the output array.
DTYPE = np.uint16
ctypedef np.uint16_t DTYPE_t

@cython.cdivision(True)
#@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
def read_mraw(filename, int width, int height, int rgbmode = 0, tuple frames=None,\
                          int bits_per_pixel=12, long long start_offset = 0, int quiet = 0):

    cdef double t0 = time.time()
    cdef double bytes_per_pixel
    if rgbmode == 1: bytes_per_pixel = 3.0*bits_per_pixel/8.0
    else: bytes_per_pixel = bits_per_pixel/8.0

    # width and height MUST be specified.
    if (width is None) or (height is None):
        raise ValueError("RAW reader requires height and width")

    # Get size of binary file before we start reading
    # (it might be smaller than we think)
    cdef long long nbytes = os.path.getsize(filename)

    # Scanlines are padded to nearest 16 bytes
    cdef unsigned int scanline_pad = int((width*1.5)%16)
    cdef unsigned int scanline_bytes = int(width*1.5) + scanline_pad
    
    # Bytes padding between frames
    cdef int frame_pad =0
    if scanline_pad > 0: frame_pad = 0

    cdef int bytes_per_frame = int(height*width*bytes_per_pixel) \
                            + scanline_pad*height + frame_pad

    # Given the supplied width and height, determine number of frames
    cdef int nframes =  int(floor(nbytes/bytes_per_frame))

    if nframes < 1 : raise IOError("File has no frames at specified resolution")


    # check start_offset
    if start_offset < 0:
        raise ValueError("start_offset cannot be negative")
    elif start_offset > nbytes:
        raise ValueError("start_offset is beyond end of file")
    if (quiet == 0) and (start_offset > 0):
        print('Offset by %i bytes' % start_offset)

    if quiet == 0: print("File contains %i frames (%i x %i)" % (nframes,width,height))
    cdef int remainder_bytes = np.mod(nbytes,bytes_per_pixel*width*height)
    if remainder_bytes > 0:
        print("Incomplete file truncated - %i bytes at end of file ignored" % remainder_bytes)



    # Limit number of frames loaded from file (good for testing)
    cdef long long start = start_offset # bytes
    cdef long long end = nbytes
    if frames is not None:
        if frames[1] > 0:
            start = start_offset + int(bytes_per_frame*frames[0])
            end = start_offset + int(bytes_per_frame*frames[1])
        if start > nbytes:
            raise ValueError("frame range: Cannot start reading beyond end of file!")
        if end > nbytes:
            print("Warning: requested read past EOF, truncating")
            end = nbytes
        if quiet == 0: print("Reading frames %i to %i" % frames)
        nframes = frames[1]-frames[0]

    # make new image array (flattened)
    cdef long long totalpixels
    if rgbmode==1: totalpixels = 3*nframes
    else: totalpixels = nframes
    totalpixels *= height
    totalpixels *= width
    cdef np.ndarray[DTYPE_t, ndim=1] images = np.zeros(int(totalpixels),dtype=DTYPE)

    # read array in
    cdef long long i
    cdef int flag
    cdef int npixels = int(ceil((end-start)/bytes_per_pixel))
    filename_byte_string = filename.encode("UTF-8")
    cdef char * fname = filename_byte_string
    cdef unsigned char * buffer = <unsigned char*>malloc(3)
    cdef unsigned int buf2

    cfile = fopen(fname, "rb")
    if cfile:
        if start>0: fseek (cfile, start, SEEK_SET)
        if bits_per_pixel==12: # loop every 3 bytes, read 2 pixels
            for i in xrange(0,len(images),2):
                flag = fread (&buffer, 1, 3, cfile)
                buf2 = <int>buffer

                # Read two pixels from three bytes
                images[i]   = <DTYPE_t>(((buf2 & 0xFF) << 4) | ((buf2 & 0xF000) >> 12)  )
                images[i+1] = <DTYPE_t>(((buf2 & 0xFF0000) >> 16) | (buf2 & 0xF00) )

                # Scanline padded to nearest 16 bytes
                if (i>0) and (i%width==0):
                    fseek (cfile, scanline_pad, SEEK_CUR)
                    if (i%(width*height)==0):
                        fseek (cfile, frame_pad, SEEK_CUR)

        elif bits_per_pixel==16: # loop every 2 bytes, write 1 pixel
            for i in xrange(0,len(images)):
                flag = fread (&buffer, 1, 2, cfile)
                buf2 = <int>buffer
                images[i]   = <DTYPE_t>(buf2 & 0xFFFF)

        elif bits_per_pixel==8: # loop 1 byte, 1 pixel.
            for i in xrange(0,len(images)):
                flag = fread (&buffer, 1, 1, cfile)
                buf2 = <int>buffer
                images[i]   = <DTYPE_t>(buf2 & 0xFFFF)

    fclose(cfile)

    if quiet == 0: print('Read %.1f MiB in %.1f sec' % ((end-start)/1048576,time.time()-t0))

    # Return 3D array (un-flatten the output)
    if rgbmode==1:
        return np.moveaxis(images.reshape((nframes,height,width,3)),[0,3,1,2],[0,1,2,3])
    else:
        return images.reshape((nframes,height,width))

