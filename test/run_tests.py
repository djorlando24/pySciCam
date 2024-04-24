#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Tests for pySciCam
    
    Try reading several sample file formats.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2022 LTRAC
    @license GPL-3.0+
    @version 0.5
    @date 24/04/2024
   
    Department of Mechanical & Aerospace Engineering
    Monash University, Australia
    
    Code in this directory is subject to the GPL-3.0+ license, please see ../LICENSE

    IMAGES, MOVIES and BINARY GRAPHICS FILES in this directory are subject to the Creative Commons Attribution-NonCommerical 4.0 International License. In short, this means you may adapt and share copies of these images provided that they carry the same license, but that you may NOT use these images for commerical purposes. Please see: https://creativecommons.org/licenses/by-nc/4.0/
    
"""

__author__="Daniel Duke <daniel.duke@monash.edu>"
__version__="0.5"
__license__="GPL-3.0+"
__copyright__="Copyright (c) 2018-2024 D.Duke"


import pySciCam
from pySciCam.pySciCam import ImageSequence
import numpy as np
import glob
import os
import matplotlib.pyplot as plt

def raw_tests():
    """ Try each RAW format handler and attempt to load a frame
    """
    # All Rawtypes
    types = pySciCam.raw_handler.raw_types
    
    # Restricting types for debugging
    #types = [ t for t in pySciCam.raw_handler.raw_types if 'chronos14_' in t ]
    #types = [ t for t in pySciCam.raw_handler.raw_types if 'photron_mraw_color_12' in t ]
    
    # Check for existence of test files -- how many to run.
    missing_types = [ t for t in types if not os.path.exists(generate_test_filename(t)) ]
    types = [ t for t in types if os.path.exists(generate_test_filename(t)) ]
    
    # Set up figure
    fig=plt.figure(figsize=(15,8.5))
    plt.subplots_adjust(wspace=0.1,hspace=0.5)
    plt.suptitle("RAW format tests")
    i=1
    passed=0
    nh, nv = plot_arrangement(len(types))
    
    for rawtype in types:
        
        print("\n*** %s RAW FORMAT ***" % rawtype)
        filename = generate_test_filename(rawtype)
        ax=None
        
        try:
            # Use what we know about the test cases to determine width and height
            # for raw formats that don't specify it.
            if 'chronos14' in rawtype:
                height=1024; width=1280
            elif 'photron' in rawtype:
                height=2048; width=2048
            else:
                height=1; width=1
            
            # Attempt to load test data. The height and width parameters are
            # ignored when not required. Only read the first few frames.
            data = ImageSequence(filename,rawtype=rawtype,\
                                          height=height,width=width,frames=(0,3))
            
            # B16 images have huge dynamic range. Clip the range so we can
            # clearly see if something has been loaded.
            if 'b16' in rawtype:
                data.arr[data.arr>3e3]=3e3
                data.arr[data.arr<1e3]=1e3

            # Make a location for the plot.
            ax=fig.add_subplot(nv,nh,i)
            plt.title(filename)

            # For grayscale images, take first frame.
            if not 'color' in rawtype.lower():
                if len(data.shape()) == 2: oneFrame = data.arr
                elif len(data.shape()) == 3: oneFrame = data.arr[0,:,:]
                elif len(data.shape()) == 4: oneFrame = data.arr[0,0,:,:]
                else: print("I don't know what to do with a grayscale array of shape %s" % data.shape)
                plotHandle=ax.imshow(oneFrame,cmap=plt.cm.gray)
                #plt.colorbar(plotHandle)
            else:
                if len(data.shape()) == 3: oneFrame = data.arr.swapaxes(0,2).swapaxes(0,1)
                elif len(data.shape()) == 4: oneFrame = data.arr[0,...].swapaxes(0,2).swapaxes(0,1)
                else: print("I don't know what to do with a color array of shape %s" % data.shape)
                # make to float with range of values 0 to 1
                oneFrame = oneFrame.astype(np.float32)
                oneFrame -= np.nanmin(oneFrame)
                oneFrame /= np.nanmax(oneFrame)
                if 'chronos' in rawtype: oneFrame *= 5
                oneFrame[oneFrame<0]=0
                oneFrame[oneFrame>1]=1
                #for ch in range(3): oneFrame[...,ch] /= np.nanmax(oneFrame[...,ch])
                #oneFrame = oneFrame.astype(np.uint8)
                plotHandle=ax.imshow(oneFrame)

            passed+=1
        
        except IOError as e:
            print(e)
            if ax is not None:
                plt.text(0.1,0.5,"Test failed - I/O error")
            
        #except:
        #    plt.text(0.1,0.5,"Test failed")
        
        i+=1
    
    if len(missing_types)>0:
        print("\nTHE FOLLOWING RAW TYPES DID NOT HAVE MATCHING TEST FILES:")
        for t in missing_types: print('\t%s' % t)
    
    return passed, i-1




def movie_tests():
    """ Try each movie format listed by the handler and attempt to show a frame
    """

    fig=plt.figure()
    plt.subplots_adjust(wspace=0.2,hspace=0.5)
    plt.suptitle("movie format tests")
    i=1
    passed=0
    nh, nv = plot_arrangement(len(pySciCam.movie_handler.movie_formats))
    
    for movie_ext in pySciCam.movie_handler.movie_formats:
    
        print("\n*** %s MOVIE ***" % movie_ext.strip('.').upper())
        
        filename=glob.glob('*%s' % movie_ext)
        if len(filename) == 0:
            print("Test file not found")
            plt.text(0.1,0.5,"Test failed - no file found")
        else:
            filename=filename[0]
        
        try:
            ax=fig.add_subplot(nv,nh,i)
            plt.title(filename)
            
            # Attempt to load test data. The height and width parameters are
            # ignored when not required.
            data = ImageSequence(filename)
            
            if len(data.shape()) == 2: oneFrame = data.arr
            elif len(data.shape()) == 3: oneFrame = data.arr[0,:,:]
            elif len(data.shape()) == 4: oneFrame = data.arr[0,0,:,:]
            else: print("I don't know what to do with an array of shape %s" % data.shape)
            
            plotHandle=ax.imshow(oneFrame)
            plt.colorbar(plotHandle)
            passed += 1
        
        except IOError as e:
            print(e)
            plt.text(0.1,0.5,"Test failed - I/O error")
    
        except:
            plt.text(0.1,0.5,"Test failed")
            #raise # debugging only

        i+=1
    
    return passed, i-1




def image_sequence_tests(IO_threads=1):
    """ Try each directory inside 'test' and look for still image sequences.
        Pass each directory to the handler and see what happens.
    """

    fig=plt.figure(figsize=(10,8))
    plt.subplots_adjust(wspace=0.5,hspace=0.1)
    plt.suptitle("still image sequences - %i I/O threads" % IO_threads)
    i=1
    passed=0
    directories = [d for d in glob.glob("*") if os.path.isdir(d)]
    nh, nv = plot_arrangement(len(directories))
    
    for dirname in directories:
        
        print("\n*** `%s' sample image set ***" % dirname)
        
        try:
            ax=fig.add_subplot(nv,nh,i)
            plt.title(dirname)
            
            # Attempt to load test data. The height and width parameters are
            # ignored when not required.
            if 'rgb' in dirname: monochrome=False
            else: monochrome=True
            data = ImageSequence(dirname,IO_threads=IO_threads,monochrome=monochrome,\
                                          use_magick=False)
            if data.shape() is None: raise IOError
            if len(data.shape()) == 2: oneFrame = data.arr
            elif monochrome:
                if len(data.shape()) == 3: oneFrame = data.arr[0,:,:]
                elif len(data.shape()) == 4: oneFrame = data.arr[0,0,:,:]
                else: print("I don't know what to do with an array of shape %s" % data.shape)
            else:
                if len(data.shape()) == 3: oneFrame = data.arr
                elif len(data.shape()) == 4: oneFrame = data.arr[0,...]
                else: print("I don't know what to do with an array of shape %s" % data.shape)
                oneFrame = np.rollaxis(oneFrame,0,3) # put color axis last
                oneFrame = np.roll(oneFrame,1,2)    # get RGB in right order for matplotlib
                
                # For colour images > 8 bits, we must reduce the bit depth as imshow likes only 8 bit image previews.
                if np.nanmax(oneFrame) > 255:
                    oneFrame -= np.nanmin(oneFrame)
                    rescaleIntensity = 256.0/float(np.nanmax(oneFrame))
                    print(oneFrame.min(),oneFrame.max(),rescaleIntensity)
                    oneFrame = oneFrame.astype(np.float32)*rescaleIntensity
                    oneFrame = oneFrame.astype(np.uint8)
                    oneFrame = np.roll(oneFrame,1,2)    # get RGB in right order for matplotlib
                
            
            
            if monochrome:
                plotHandle=ax.imshow(oneFrame, cmap=plt.cm.gray)
                plt.colorbar(plotHandle)
            else:
                ax.imshow(oneFrame)
            passed +=1
        
        except IOError as e:
            print(e)
            plt.text(0.1,0.5,"Test failed - I/O error")
    
        # Disable generic exceptions to capture bugs.
        #except:
        #    plt.text(0.1,0.5,"Test failed")

        i+=1
    
    return passed, i-1

# Determine how to arrange plots semi-neatly
def plot_arrangement(n):
    nv = int(np.sqrt(n))
    nh = int(np.ceil(n/float(nv)))
    return nh,nv

# Autogenerate file names from rawtypes
def generate_test_filename(rawtype):
    if rawtype == 'b16': filename='sample.b16'
    elif rawtype == 'b16dat': filename='sample.b16dat'
    elif 'photron_mraw' in rawtype: filename='%s.mraw' % rawtype
    else: filename='%s.raw' % rawtype
    return filename

#################################
if __name__=='__main__':
    """ Run the tests when the run_tests.py script is invoked from command line """
    
    # Move to test directory if in parent directory.
    cwd = os.getcwd()
    if os.path.basename(cwd)=='pySciCam': os.chdir('test')
    if os.path.basename(os.getcwd()) != 'test': raise IOError("Tests must be run from pySciCam or pySciCam/test")
    
    # Run tests.
    p1,n1 = image_sequence_tests()
    p2,n2 = movie_tests()
    p3,n3 = raw_tests()
    
    print('*'*80)
    print("Passed %i of %i tests with serial I/O\nClose windows to continue\n" % (p1+p2+p3,n1+n2+n3))
    
    plt.show()
    
    # Now try with parallel file I/O
    p1,n1 = image_sequence_tests(4) # 4 threads
    print('*'*80)
    print("Passed %i of %i tests with parallel I/O\nClose windows to exit" % (p1,n1))
    
    plt.show()
    exit()

