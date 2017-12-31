#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
    Image sequence handling routines for pySciCam module
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2017 LTRAC
    @license GPL-3.0+
    @version 0.1.0
    @date 31/12/2017
    
    Please see help(pySciCam) for more information.
"""

__author__="Daniel Duke <daniel.duke@monash.edu>"
__version__="0.1.0"
__license__="GPL-3.0+"
__copyright__="Copyright (c) 2017 LTRAC"


# Known tested still frame file extensions
still_formats = ['.tif','.tiff']

import time
import numpy as np

##########################################################################################
# Parallel wrapper to load a chunk of images using PIL.
def __pil_load_wrapper__(fseq,width,height,dtype_dest,dtype_src,monochrome):
    from PIL import Image
    if monochrome: A = np.zeros((height,width,len(fseq)),dtype=dtype_dest) # MONO
    else: A = np.zeros((height,width,3,len(fseq)),dtype=dtype_dest)        # RGB
    i=0
    for fn in fseq:
        frame = Image.open(fn)
        if monochrome and (frame.mode=='RGB'):
            frame = __make_monochromatic__(np.array(frame),dtype_dest)
        A[...,i]=np.array(frame)
        i+=1
    return A

##########################################################################################
# Parallel wrapper to load a chunk of images using PythonMagick bindings to ImageMagick.
def __magick_load_wrapper__(fseq,width,height,dtype_dest,dtype_src,monochrome):
    import PythonMagick
    if monochrome: A = np.zeros((height,width,len(fseq)),dtype=dtype_dest) # MONO
    else: A = np.zeros((height,width,3,len(fseq)),dtype=dtype_dest)        # RGB
    i=0
    
    for fn in fseq:
    
        imageObj = PythonMagick.Image()
        buffer = PythonMagick.Blob()
        dtype_src_MagickBlob = dtype_src
        
        # Get pixel buffer
        imageObj.read(fn)
        
        # Specify any necessary conversions to make the data readable.
        if dtype_src == 'uint12':
            imageObj.depth(16)
            dtype_src_MagickBlob=np.uint16
        
        # Write converted data into blob buffer
        imageObj.write(buffer)
        
        # Transfer buffer into to numpy array
        if type(dtype_src_MagickBlob) is type:
            frame = np.fromstring(buffer.data, dtype_src_MagickBlob)
        else:
            raise ValueError("Pixel format %s not currently supported!"\
                              % dtype_src_MagickBlob)

        # allocate 3rd dimension for color channels?
        if ('RGB' in str(imageObj.colorSpace())):
            extraPixels = len(frame) - height*width*3
            if extraPixels < 0: raise IndexError("ERROR: insufficient bytes for RGB data"\
                                                +" in frame: %s (%i)" % (fn,extraPixels))
            frame = frame[:-extraPixels].reshape(height,width,3)
        else:
            extraPixels = len(frame) - height*width
            if extraPixels < 0: raise IndexError("ERROR: insufficient bytes for data"\
                                                +" in frame: %s (%i)" % (fn,extraPixels))
            frame = frame[:-extraPixels].reshape(height,width)
    
        # Collapse color channel data on `monochrome' flag.
        if monochrome and ('RGB' in str(imageObj.colorSpace())):
            frame = __make_monochromatic__(frame,dtype_dest)

        del imageObj
        del buffer

        A[...,i]=frame.astype(dtype_dest)
        i+=1
    return A

##########################################################################################
# Summation for RGB channel data into monochrome - no information is lost.
# if overflow, warn user.
def __make_monochromatic__(im,dtype):
    im_newtype = im.astype(dtype)
    mono = np.sum(im_newtype,axis=2)
    if np.any( mono == np.iinfo(dtype).max ) \
    and not np.any( im_newtype == np.iinfo(dtype).max ):
        print "WARNING: Possible overflow/clipping detected when summing RGB channels."
    return mono

####################################################################################
# Read numbered image sequence from list all_images
#
# Use multiple processes to read lots of images at once if
# the disk read speed justifies it (i.e SSD).
def load_image_sequence(ImageSequence,all_images,frames=None,monochrome=False,\
                        dtype=None,use_magick=True):


    # Attempt setup of parallel file I/O.
    if ImageSequence.IO_threads > 1:
        try:
            from joblib import Parallel, delayed
        except ImportError:
            print "Error, joblib is not installed. Multithreaded file I/O will be disabled."
            ImageSequence.IO_threads=1

    # Attempt to import PythonMagick if requested
    if use_magick:
        try:
            from PythonMagick import Image
            imageHandler=__magick_load_wrapper__
        except ImportError:
            print "PythonMagick library is not installed."
            print "Falling back to Pillow (fewer file formats supported)"
            use_magick = False
    
    # Attempt to import Pillow if requested
    if not use_magick:
        try:
            from PIL import Image
            imageHandler=__pil_load_wrapper__
        except ImportError:
            raise ImportError("Pillow library is not installed. Try `pip install pillow'")


    # Reduce range of frames?
    if frames is not None:
        if len(all_images)>frames[1]:
            all_images=all_images[frames[0]:frames[1]]

    # Use first image to set dtype and size.
    # Read with Pillow?
    if not use_magick:
        try:
            I0 = Image.open(all_images[0])
            ImageSequence.mode = I0.mode
            print I0
            I0_dtype = np.array(I0).dtype
            if dtype is None: ImageSequence.dtype = I0_dtype
            else: ImageSequence.dtype=dtype
            print "\tPIL thinks the bit depth is %s" % I0_dtype
            bits_per_pixel = np.dtype(I0_dtype).itemsize*8
            ImageSequence.width = I0.width
            ImageSequence.height = I0.height
        except IOError as e:
            if os.path.isfile(all_images[0]) and not use_magick:
                # Format unrecognized.
                print "The image format was not recognized by PIL! Trying ImageMagick"
                use_magick=True
                from PythonMagick import Image
                imageHandler==__magick_load_wrapper__
            else:
                # Possible filesystem error
                raise IOError("File %s could not be opened." % all_images[0])

    # Read with PythonMagick?
    # Seperate 'if' block allows PIL failure to then try this one.
    if use_magick:
        try:
            I0 = Image(all_images[0])
            ImageSequence.width = I0.size().width()
            ImageSequence.height = I0.size().height()
            ImageSequence.mode = str(I0.colorSpace())
            # Source bit depth
            bits_per_pixel = I0.depth()
            if bits_per_pixel==8: I0_dtype=np.uint8
            elif bits_per_pixel==12: I0_dtype='uint12'
            elif bits_per_pixel==16: I0_dtype=np.uint16
            elif bits_per_pixel==32: I0_dtype=np.uint32
            elif bits_per_pixel==64: I0_dtype=np.uint64
            else: raise ValueError
            print "\tPythonMagick thinks the bit depth is %s" % I0_dtype
            # Determine minimum acceptable destination bit depth
            # (unless overridden by user kwargs)
            if dtype is None:
                if type(I0_dtype) is type: ImageSequence.dtype=I0_dtype
                elif I0_dtype == 'uint12': ImageSequence.dtype=np.uint16
                else: raise ValueError
            else:
                ImageSequence.dtype=dtype
        except IOError as e:
            # Possible filesystem error
            raise IOError("File %s could not be opened." % all_images[0])
        except ValueError:
            # bad bit depth / not supported
            raise ValueError("Bit depth %i for source image not currently supported!" % bits)


    if not monochrome and not 'RGB' in ImageSequence.mode:
        # Force mono flag if there is no colour data
        monochrome=True

    if monochrome and (dtype is None):
        # If mono flag set and dtype unspecified,
        # allow more space for colour information in mono channel
        # so there's no overflowing when we do summation.
        ImageSequence.increase_dtype()


    # Chunk size for parallel I/O
    n_jobs = ImageSequence.IO_threads
    if n_jobs > len(all_images): n_jobs = len(all_images)
    b=len(all_images)/n_jobs
    if b<1: b=1

    print "\tReading files into memory..."
    t0=time.time()
    if n_jobs > 1:
        # Read image sequence in parallel
        L = Parallel(n_jobs=n_jobs,verbose=ImageSequence.Joblib_Verbosity)(delayed(imageHandler)(all_images[a:a+b],ImageSequence.width,ImageSequence.height,ImageSequence.dtype,I0_dtype,monochrome) for a in range(0,len(all_images),b))
    else:
        # Plain list. might have to rearrange this if it consumes too much RAM.
        L = [imageHandler(all_images[a:a+b],ImageSequence.width,ImageSequence.height,ImageSequence.dtype,\
             I0_dtype,monochrome) for a in range(0,len(all_images),b)]

    # Repack list of results into a single numpy array.
    if len(L[0].shape) == 3:
        # monochrome arrays
        ImageSequence.arr = np.dstack(L).swapaxes(2,0).swapaxes(1,2)
    else:
        # colour arrays
        ImageSequence.arr = np.rollaxis(np.rollaxis(np.dstack(L),3,0),3,1)

    ImageSequence.src_bpp = bits_per_pixel
    read_nbytes = bits_per_pixel * np.product(ImageSequence.arr.shape) / 8
    print 'Read %.1f MiB in %.1f sec' % (read_nbytes/1048576,time.time()-t0)

    return
