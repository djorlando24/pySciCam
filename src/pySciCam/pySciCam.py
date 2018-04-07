#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Class to read images from high speed and scientific cameras in Python
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2017 LTRAC
    @license GPL-3.0+
    @version 0.1.2
    @date 07/04/2018
    
    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
    
    pySciCam is an attempt to build an easy to use, all in one solutiuon to allow
    researchers to convert their scientific camera's binary data file or unusual
    solution to allow researchers to quickly convert their camera's binary files or
    unusual / native TIFF and bitmap formats into NumPy arrays in a single line of code.
    It achieves this by using cython (C) modules for fast reading of RAW blobs, and
    parallelized ImageMagick / Pillow for standardised formats like TIFF. Movie support
    via ffmpeg library is also included.
    
    Current support for:
        - 8, 12, 16, 32 & 64-bit RGB or Mono TIFF using PythonMagick (most cameras)
        - 12 & 16 bit packed RAW (Chronos monochrome and color cameras)
        - Any greyscale movies supported by the ffmpeg library
        - PCO B16 scientific data format for double-exposed (PIV) images
        - 8 & 16 bit RGB TIFF using Pillow library (Most colour cameras)
        - 8 & 16 bit Mono TIFF using Pillow library (Most monochrome cameras)
    
    Multi-file images sequences are read using parallel I/O for best performance
    on machines with very fast read speeds (ie SSD, RAID). If this is detrimental,
    (ie magnetic/tape drive), pass the keyword arg IO_threads=1 for serial I/O.
    
    Wide compatibility for sequences of images is achieved using PythonMagick
    bindings to ImageMagick. If this is not available on the system, Pillow can be
    used, which is easier to install. However, Pillow only supports 8-bit RGB, and
    8,16,32 bit greyscale.
    
    EXAMPLE USAGE:
    
        # Read sequence of images from a directory
        data = pySciCam.ImageSequence("/directory/of/images")
        
        # Read a movie, and get just the first 25 frames
        data = pySciCam.ImageSequence("movie.mp4",frames=(0,25))
        
        # Read a RAW binary blob from a particular camera
        data = pySciCam.ImageSequence("foo.raw",rawtype='bar_cam')
        
        # Print pixel values of the 10th frame of monochrome data
        from matplotlib import pyplot
        pyplot.imshow(data.arr[9,...])
        plt.show()
        
        # Print green channel values for 10th frame of RGB data
        pyplot.imshow(data.arr[9,1,...])
        plt.show()
        
    KEYWORD ARGS FOR ImageSequence CLASS:
        frames:
            2-tuple of form (start,end) to trim a range of frames.
        
        dtype:
            force the destination array to a certain data type, for
            example numpy.uint8 or numpy.uint16.
            The reader will autodetect the dtype based on the
            source file. For very large image sets, upsampling can lead
            to memory issues. In this case the dtype can be restricted
            using this argument.
        
        monochrome:
            boolean. If the image set is from a colour camera,
            this will sum all the colour channels together during
            the reading process to reduce the size of the array.
            
        IO_threads:
            Number of I/O threads for parallel reading of sets of still
            images. Default is 8. Set to 1 to disable parallel I/O.
            
    ADDITIONAL ARGS FOR RAW TYPES:
    
        width, height:
            provide prespecified image dimensions for RAW formats
            that don't specify it
            
        rawtype:
            string describing the format of a RAW (binary) file
            
        b16_doubleExposure:
            boolean. If PCO B16 image, is it a double exposure?
            
        start_offset:
            integer. Bytes offset for RAW blob with unspecified header size.
    
    Future support planned for:
    - Photron raw exporter formats
    - Header scanline in Chronos RAW, when firmware supports it.
    - Shimadzu HPV custom format
    - Other PCO DIMAX raw exporter formats
    - Motion Pro / Redlake raw formats
    contact me if you have any specific suggestions. Please provide a sample file!
    
    TO DO:
    - Make documentation for class.
    - Proper header documentation and README, LICENSE etc.
    - Get distutils working to build as an installable package.
    
"""

__author__="Daniel Duke <daniel.duke@monash.edu>"
__version__="0.1.2"
__license__="GPL-3.0+"
__copyright__="Copyright (c) 2018 LTRAC"

import os, glob, sys, time
from natsort import natsorted
import numpy as np

import raw_handler
import movie_handler
import image_sequence_handler

##########################################################################################
class ImageSequence:
    
    # All tested and working image file extensions.
    all_known_extensions=raw_handler.raw_formats+movie_handler.movie_formats+\
                         image_sequence_handler.still_formats
    
    # Constructor. Load images if path is given.
    def __init__(self,path=None,**kwargs):
        
        if not 'IO_threads' in kwargs.keys():
            # Default is parallel on 8 cores
            self.IO_threads=8
        else:
            self.IO_threads=int(kwargs['IO_threads'])
            del kwargs['IO_threads']
        
        if not 'Joblib_Verbosity' in kwargs.keys():
            self.Joblib_Verbosity=40
        else:
            self.Joblib_Verbosity=int(kwargs['Joblib_Verbosity'])
        
        self.N=0
        self.arr = None
        
        if os.path.exists(path):
            self.open(path,**kwargs)
        else:
            raise IOError("Specified path invalid: `%s'" % path)

        return


    # Read a directory/path or single file, and call appropriate handler for loading images.
    # As a first pass this is done from the file extension(s).
    # Some handlers require some data that isn't autodetected (dtype, width, height, etc).
    def open(self,path,frames=None,monochrome=True,dtype=None,\
                       width=None,height=None,rawtype=None,b16_doubleExposure=True,\
                       start_offset=0):
        
        # Wildcard search
        print "Reading %s" % path
        if os.path.isdir(path):
            path+='/'
            all_images = glob.glob(path+'*')
        else:
            all_images = glob.glob(path)
        
        # Set extension and filter on this.
        self.ext=None
        for f in all_images:
            if os.path.splitext(f)[-1].lower() in self.all_known_extensions:
                self.ext=os.path.splitext(f)[-1].lower()
                break
        if self.ext is None:
            print "** Error, no recognized file extensions found"
            return
        
        # Natural sort and all matching extension
        all_images = [f for f in natsorted(all_images) if os.path.splitext(f)[-1].lower()==self.ext]
        
        # Number of images found
        if len(all_images)<1:
            print "** Error, no images found in path"
            return
        elif len(all_images)>1:
            print "\tFound %i images with extension %s" % (len(all_images),self.ext)

        # Call appropriate loading subroutine
        if self.ext in movie_handler.movie_formats:
            # Movie formats
            movie_handler.load_movie(self,all_images[0],frames,monochrome,dtype)
        
        elif self.ext in raw_handler.raw_formats:
            # Hardware-specific raw formats.
            #  the variable rawtype specifies which reader is to be used,
            #  as the extension does not always tell us enough. For B16,
            #  we can infer it from the extension.
            if self.ext == '.b16': rawtype='b16'
            elif self.ext == '.b16dat': rawtype='b16dat'
            raw_handler.load_raw(self,all_images,rawtype,width,height,frames,dtype,\
                                 b16_doubleExposure,start_offset)

        else:
            # Sequences of images (ie TIFFs, BMPs)
            image_sequence_handler.load_image_sequence(self,all_images,frames,\
                            monochrome,dtype)

        print "\tData in memory:\t",self.shape()
        print "\tIntensity range:\t",self.arr.min(),"to",self.arr.max(),'\t',self.dtype
        self.stored_bits_per_pixel()
        print "\tArray size:\t%.1f MB" % (np.product(self.arr.shape)*self.bpp/1024./1024.)
        return

    # Calculate stored bits per pixel based on self.dtype.
    # the source data may have had a different value (it would be in self.src_bpp)
    def stored_bits_per_pixel(self):
        if self.dtype == np.uint8: self.bpp = 1.
        elif self.dtype == np.uint16: self.bpp = 2.
        elif self.dtype == np.uint32: self.bpp = 4.
        elif self.dtype == np.uint64: self.bpp = 8.
        else: self.bpp=-1
        return
    
    # Increase the bit depth to allow for increased information content
    # ie. when summing RGB
    def increase_dtype(self,quiet=0):
        current_dtype=self.dtype
        if self.dtype==np.uint8: self.dtype=np.uint16
        elif self.dtype==np.uint16: self.dtype=np.uint32
        elif self.dtype==np.uint32: self.dtype=np.uint64
        if quiet==0:
            print "\tIncreasing stored bit depth from %s to %s" % (current_dtype,self.dtype)
        if 'arr' in dir(self):
            if self.arr is not None:
                if self.dtype != self.arr.dtype:
                    self.arr=self.arr.astype(self.dtype)
        return

    # Shape of image array
    def shape(self):
        if isinstance(self.arr,np.ndarray):
            return self.arr.shape
        else:
            return None

    # Perform Bayer decoding on colour data loaded from RAW format
    def bayerDecode(self):
        import site, itertools
        from ctypes import cdll, c_uint, c_uint8, c_uint16, c_uint32, POINTER
        
        print 'Bayer decoding...'
        s=self.shape()
        
        # naive reshaping
        #self.arr = self.arr.reshape(s[0]/3,3,s[1],s[2])
        
        # build empty RGB array
        newarr = np.zeros((s[0],3,s[1],s[2]),dtype=self.dtype)
        
        # load libbayer
        path_to_libbayer = list(itertools.chain.from_iterable([ glob.glob(p+'/libbayer.so')\
                                for p in site.getsitepackages() ]))
        if len(path_to_libbayer)==0: raise IOError("Can't find libbayer.so")
        libbayer= cdll.LoadLibrary(path_to_libbayer[0])
        
        # call appropriate subroutine.
        if self.dtype == np.uint16:
            # args to dc1394_bayer_decoding functions:
            # const uint16_t *restrict bayer, uint16_t *restrict rgb, uint32_t sx, uint32_t sy, dc1394color_filter_t tile, dc1394bayer_method_t method, uint32_t bits
            method = c_uint(0)
            tile = c_uint(512)
            sx = c_uint32(s[1])
            sy = c_uint32(s[2])
            bits = c_uint32(16)
            
            # This runs, but the pixel ordering is wrong.
            bayer_in = self.arr[0,...].ctypes.data_as(POINTER(c_uint16 * (s[1] * s[2])))
            rgb_out = newarr[0,...].ctypes.data_as(POINTER(c_uint16 * (3 * s[1] * s[2])))
            
            flag = libbayer.dc1394_bayer_decoding_16bit(bayer_in, rgb_out, sx, sy, tile, method, bits)
            if flag != 0: raise ValueError("Bayer decode error flag %i" % flag)
        
        elif self.dtype == np.uint8:
            raise ValueError("uint8 not yet supported")
            #if libbayer.dc1394_bayer_decoding_8bit( self.arr, newarr) != 0: raise ValueError
        
        else:
            raise ValueError("Cannot do bayer decoding on image array dtype"+self.dtype)
        
        #        for i in range(s[0]):
        #            for j in range(0,s[1],2):
        #                for k in range(0,s[2],2):
        #
        #                    # RG
        #                    # GB bayer blocks
        #                    newarr[i,0,j:j+2,k:k+2] = self.arr[i,j,k] # red values
        #                    newarr[i,1,j:j+2,k:k+2] = self.arr[i,j+1,k] + self.arr[i,j,k+1] # green values
        #                    newarr[i,2,j:j+2,k:k+2] = self.arr[i,j+1,k+1] # blue values
    
        self.arr= newarr
        return
