# pySciCam
Class to read images from high speed and scientific cameras in Python
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.4.0
    @date 08/05/2020
        __   ____________    ___    ______    
       / /  /_  ____ __  \  /   |  / ____/    
      / /    / /   / /_/ / / /| | / /         
     / /___ / /   / _, _/ / ___ |/ /_________ 
    /_____//_/   /_/ |__\/_/  |_|\__________/ 

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia

    Many scientific cameras have 10 or 12 bit sensors. Most camera APIs/software require
    the user to choose between 8 or 16 bit depth when saving to an easily-readable format
    such as TIFF. Saving a 10-bit depth pixel value into a 16-bit unsigned int can rapidly
    blow out the file size, leading to wasted storage space and much slower rates of file
    transfer off the camera and onto a local drive ( a major laboratory bottleneck! )  

    Most cameras have an ability to save data to raw binary or to unusual, compact file
    formats such as 12-bit TIFF. This is by far the fastest way of getting lots of data
    off a camera, as no bits are wasted. I've had trouble finding software that can read 
    these files, and most graphics packages (even ImageJ!) struggle to correctly read
    files like 16/32 bit RGB TIFF for example. This Python package solves that problem.
    
    pySciCam is an attempt to build an easy to use, all in one solution to allow
    researchers to quickly convert their camera's binary files or unusual / native TIFF
    and bitmap formats into NumPy arrays in a single line of code.
    It achieves this by using cython (C) modules for fast reading of RAW blobs, and
    parallelized ImageMagick / Pillow for standardised formats like TIFF. Movie support
    via ffmpeg library is also included.
    
    Current support for:
        - 8, 12, 16, 32 & 64-bit RGB or Mono TIFF using PythonMagick (most cameras)
        - 12 & 16 bit packed RAW (Chronos monochrome and color cameras)
          both pre-0.3 firmware and >= 0.3 firmware 12-bit packing modes supported
	- Photron MRAW formats (mono, color Bayer and RGB encoding)
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

    V0.4.0 RELEASE NOTES

    - pySciCam python3 support improved and tested working on MacOS.
    - fixed a bug with importing a single TIFF image.
    
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
            setting True will sum all the colour channels together during
            the reading process to reduce the size of the array.
            The flag is ignored for grayscale source files.

        IO_threads:
            Number of I/O threads for parallel reading of sets of still
            images. Default is 4. Set to 1 to disable parallel I/O.
            
        use_magick:
            Manually disable use of PythonMagick, if not installed. Falls
            back to PIL, which is easier to install but supports fewer formats.
            
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

	old_packing_order: (chronos formats only)
            unpack 12-bit RAW data from Chronos firmware 0.2
    
    Future support planned for:
    - Header scanline in Chronos RAW, when firmware supports it.
    - Fluke IR camera .IS2 files
    - Shimadzu HPV custom format
    - Other Photron raw exporter formats
    - Other PCO DIMAX raw exporter formats
    - Motion Pro / Redlake raw formats
    contact me if you have any specific suggestions. Please provide a sample file!

    