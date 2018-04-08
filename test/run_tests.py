#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Tests for pySciCam
    
    Try reading several sample file formats.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2017 LTRAC
    @license GPL-3.0+
    @version 0.1.2
    @date 08/04/2018
    
    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
    
    
    Code in this directory is subject to the GPL-3.0+ license, please see ../LICENSE

    IMAGES, MOVIES and BINARY GRAPHICS FILES in this directory are subject to the Creative Commons Attribution-NonCommerical 4.0 International License. In short, this means you may adapt and share copies of these images provided that they carry the same license, but that you may NOT use these images for commerical purposes. Please see: https://creativecommons.org/licenses/by-nc/4.0/
    
"""

import pySciCam
import numpy as np
import glob
import os
import matplotlib.pyplot as plt

def raw_tests():
    """ Try each RAW format handler and attempt to load a frame
    """
    # All Rawtypes
    #types = pySciCam.raw_handler.raw_types
    
    # RESTRICT TESTS - DEBUGGING !
    types = [ t for t in pySciCam.raw_handler.raw_types if 'chronos14_color' in t ]
    
    fig=plt.figure(figsize=(15,8))
    plt.subplots_adjust(wspace=0.1,hspace=0.2)
    plt.suptitle("RAW format tests")
    i=1
    passed=0
    nh, nv = plot_arrangement(len(types))
    
    for rawtype in types:
        
        print "\n*** %s RAW FORMAT ***" % rawtype
        if rawtype is 'b16': filename='sample.b16'
        elif rawtype is 'b16dat': filename='sample.b16dat'
        else: filename='%s.raw' % rawtype
        
        try:
            ax=fig.add_subplot(nv,nh,i)
            plt.title(filename)
            
            # Attempt to load test data. The height and width parameters are
            # ignored when not required, they apply to the chronos_raw formats only.
            data = pySciCam.ImageSequence(filename,rawtype=rawtype,\
                                          height=1024,width=1280,frames=(0,3))
            
            # B16 images have huge dynamic range. Clip the range so we can
            # clearly see if something has been loaded.
            if 'b16' in rawtype:
                data.arr[data.arr>3e3]=3e3
                data.arr[data.arr<1e3]=1e3
           
            # For grayscale images, take first frame.
            if not 'color' in rawtype.lower():
                if len(data.shape()) == 2: oneFrame = data.arr
                elif len(data.shape()) == 3: oneFrame = data.arr[0,:,:]
                elif len(data.shape()) == 4: oneFrame = data.arr[0,0,:,:]
                else: print "I don't know what to do with a grayscale array of shape %s" % data.shape
                plotHandle=ax.imshow(oneFrame)
                plt.colorbar(plotHandle)
            else:
                if len(data.shape()) == 3: oneFrame = data.arr.swapaxes(0,2).swapaxes(0,1)
                elif len(data.shape()) == 4: oneFrame = data.arr[0,...].swapaxes(0,2).swapaxes(0,1)
                else: print "I don't know what to do with a color array of shape %s" % data.shape
                # make to float with range of values 0 to 1
                oneFrame = oneFrame.astype(np.float32)
                oneFrame -= np.nanmin(oneFrame)
                oneFrame /= np.nanmax(oneFrame) / 5.
                oneFrame[oneFrame<0]=0
                oneFrame[oneFrame>1]=1
                #for ch in range(3): oneFrame[...,ch] /= np.nanmax(oneFrame[...,ch])
                #oneFrame = oneFrame.astype(np.uint8)
                plotHandle=ax.imshow(oneFrame)

            passed+=1
        
        except IOError as e:
            print e
            plt.text(0.1,0.5,"Test failed - I/O error")
            
        #except:
        #    plt.text(0.1,0.5,"Test failed")
        
        i+=1
    
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
    
        print "\n*** %s MOVIE ***" % movie_ext.strip('.').upper()
        
        filename=glob.glob('*%s' % movie_ext)
        if len(filename) == 0:
            print "Test file not found"
            plt.text(0.1,0.5,"Test failed - no file found")
        else:
            filename=filename[0]
        
        try:
            ax=fig.add_subplot(nv,nh,i)
            plt.title(filename)
            
            # Attempt to load test data. The height and width parameters are
            # ignored when not required.
            data = pySciCam.ImageSequence(filename)
            
            if len(data.shape()) == 2: oneFrame = data.arr
            elif len(data.shape()) == 3: oneFrame = data.arr[0,:,:]
            elif len(data.shape()) == 4: oneFrame = data.arr[0,0,:,:]
            else: print "I don't know what to do with an array of shape %s" % data.shape
            
            plotHandle=ax.imshow(oneFrame)
            plt.colorbar(plotHandle)
            passed += 1
        
        except IOError as e:
            print e
            plt.text(0.1,0.5,"Test failed - I/O error")
    
        except:
            plt.text(0.1,0.5,"Test failed")

        i+=1
    
    return passed, i-1




def image_sequence_tests(IO_threads=1):
    """ Try each directory inside 'test' and look for still image sequences.
        Pass each directory to the handler and see what happens.
    """

    fig=plt.figure()
    plt.subplots_adjust(wspace=0.2,hspace=0.5)
    plt.suptitle("still image sequences - %i I/O threads" % IO_threads)
    i=1
    passed=0
    directories = [d for d in glob.glob("*") if os.path.isdir(d)]
    nh, nv = plot_arrangement(len(directories))
    
    for dirname in directories:
        
        print "\n*** %s IMAGES ***" % dirname
        
        try:
            ax=fig.add_subplot(nv,nh,i)
            plt.title(dirname)
            
            # Attempt to load test data. The height and width parameters are
            # ignored when not required.
            data = pySciCam.ImageSequence(dirname,IO_threads=IO_threads)
            
            if len(data.shape()) == 2: oneFrame = data.arr
            elif len(data.shape()) == 3: oneFrame = data.arr[0,:,:]
            elif len(data.shape()) == 4: oneFrame = data.arr[0,0,:,:]
            else: print "I don't know what to do with an array of shape %s" % data.shape
            
            plotHandle=ax.imshow(oneFrame)
            plt.colorbar(plotHandle)
            passed +=1
        
        except IOError as e:
            print e
            plt.text(0.1,0.5,"Test failed - I/O error")
    
        except:
            plt.text(0.1,0.5,"Test failed")

        i+=1
    
    return passed, i-1

# Determine how to arrange plots semi-neatly
def plot_arrangement(n):
    nh = int(np.sqrt(n))
    nv = int(np.ceil(n/float(nh)))
    return nh,nv

#################################
if __name__=='__main__':
    """ Run the tests when the run_tests.py script is invoked from command line """
    
    #p1,n1 = image_sequence_tests()
    #p2,n2 = movie_tests()
    p3,n3 = raw_tests()
    plt.show();exit()
    
    print '*'*80
    print "Passed %i of %i tests with serial I/O\nClose windows to continue\n" % (p1+p2+p3,n1+n2+n3)
    
    plt.show()
    
    # Now try with parallel file I/O
    p1,n1 = image_sequence_tests(4) # 4 threads
    print '*'*80
    print "Passed %i of %i tests with parallel I/O\nClose windows to exit" % (p1,n1)
    
    plt.show()
    exit()

