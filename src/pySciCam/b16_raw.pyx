# -*- coding: UTF-8 -*-
"""
    Read monochrome 16-bit raw data from PCO scientific cameras into NumPy arrays.

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.1.2
    @date 07/04/2018

    support single & double exposed B16 (single image pair) and B16dat (multiple pairs).

    Please see help(pySciCam) for more information.
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

"""
from __future__ import division

__author__="Daniel Duke <daniel.duke@monash.edu>"
__version__="0.1.2"
__license__="GPL-3.0+"
__copyright__="Copyright (c) 2017 LTRAC"

import numpy as np
import os
import time
cimport cython
cimport numpy as np
from libc.math cimport floor
from libc.stdio cimport FILE, fopen, fclose, ftell, fread, fseek,\
                        SEEK_END, SEEK_SET, SEEK_CUR
from libc.stdlib cimport malloc, free
cdef FILE * cfile

# this is the type of the output array.
# should be 16 bit or greater.
DTYPE = np.uint16
ctypedef np.uint16_t DTYPE_t

def b16_read_header(char* fname):
    cfile = fopen(fname, "rb")
    cdef unsigned char * buffer = <unsigned char*>malloc(4)
    cdef int height, width, flag
    cdef unsigned int skipext = 0
    cdef long nbytes, hbytes

    # Read header
    fseek (cfile, 4, SEEK_CUR)

    flag = fread (&buffer, 1, 4, cfile)
    hb = <long>buffer & 0xFFFFFFFF
    nbytes = hb
    flag = fread (&buffer, 1, 4, cfile)
    hb = <long>buffer & 0xFFFFFFFF
    hbytes = hb
    nbytes -= hb

    flag = fread (&buffer, 1, 4, cfile)
    hb = <long>buffer & 0xFFFFFFFF
    width = int(hb)

    flag = fread (&buffer, 1, 4, cfile)
    hb = <long>buffer & 0xFFFFFFFF
    height = int(hb)

    flag = fread (&buffer, 1, 4, cfile)
    hb = <long>buffer & 0xFFFFFFFF
    if hb != 0xFFFFFFFF: skipext=1

    fclose(cfile)
    return height, width, nbytes, hbytes, skipext



def b16_reader(filename,doubleExposure=True,quiet=0):
    """ Read B16 or B16dat file specified by filename """

    cdef long t0 = time.time()
    cdef int width=1, height=1
    cdef np.ndarray[DTYPE_t, ndim=1] images
    cdef long nbytes = 0, nbytes_from_header = 0
    cdef long hbytes = 0
    cdef int nframes

    is_b16dat = False
    if os.path.splitext(filename)[1].lower() == '.b16':
        # b16 file. Either 1 or 2 frames
        if doubleExposure: nframes = 2
        else: nframes = 1
    else:
        # nframes determined by file size!
        is_b16dat = True

    filename_byte_string = filename.encode("UTF-8")
    cdef char * fname = filename_byte_string
    cdef unsigned char * buffer = <unsigned char*>malloc(4)
    cdef long hb
    cdef unsigned int mb, i, skipext, block, npixels, flag

    height, width, nbytes_from_header, hbytes, skipext = b16_read_header(fname)
    nbytes = nbytes_from_header


    if (skipext==1) and (quiet==0):
        print "\nSkipping extended header"

    # div by 2 for double exposure!
    if doubleExposure:
        height /= 2
        if (quiet == 0) and not is_b16dat:
            print "Reading double exposure of %i x %i pixels" % (width,height)
    else:
        if (quiet == 0) and not is_b16dat:
            print "Reading single exposure of %i x %i pixels" % (width,height)

    cfile = fopen(fname, "rb")
    if cfile:

        if is_b16dat:
            # Find true length of file
            fseek (cfile, 0, SEEK_END)
            nbytes = ftell(cfile)

            # Find total num frames
            if doubleExposure:
                nframes = int(floor((nbytes-hbytes/2)/2/height/width))
            else:
                nframes = int(floor((nbytes-hbytes)/2/height/width))

            if quiet == 0:
                if doubleExposure:
                    print "Reading %i double exposed image pairs of %i x %i pixels"\
                            % (nframes/2,width,height)
                else:
                    print "Reading %i images of %i x %i pixels" % (nframes,width,height)

        # Skip to end of (first) header
        fseek (cfile, 1024, SEEK_SET)

        # make new image array (flattened)
        images = np.zeros(int(nframes*height*width),dtype=DTYPE)

        # Size of b16 pixel blocks in b16dat
        block = int(nbytes_from_header/2)
        # Total number of pixels
        npixels = int(nframes*height*width)

        # Read pixel buffer
        for i in xrange(npixels):
            flag = fread (&buffer, 1, 2, cfile)
            mb = <int>buffer & 0xFFFF
            images[i] = <DTYPE_t>mb

            # B16dat - skip concatenated header
            if is_b16dat:
                if (i%block == 0) and (i>0):
                    fseek (cfile, 2014, SEEK_CUR)

    fclose(cfile)

    if quiet == 0: print 'Read %.1f MiB in %.1f sec' % (nbytes/1048576,time.time()-t0)

    # Return 3D array (un-flatten the output)
    if is_b16dat and doubleExposure:
        return images.reshape((int(nframes/2),2,height,width))
    else:
        return images.reshape((nframes,height,width))
