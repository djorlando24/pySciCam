# Compiling ImageJ Plugin Filters
Dr Daniel Duke
Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
Monash University

24 April 2021

## Overview
While `pySciCam` is much faster than ImageJ, it is handy to be able to quickly interrogate images when they are collected. To this end, a set of plugin filters for ImageJ is provided here that will allow importing of Chronos RAW data, demosaicing of RAW Bayer filtered images, etc. 

## Installation instructions

### Windows

These instructions were created using ImageJ 1.53i from https://imagej.nih.gov/ij/download.html
This version comes with Java built-in which is easiest on Windows.

Extract the zip file into the Program Files directory.

Right click on the ImageJ directory and open the Security tab. Click Edit. Select "Users" from the top box. Then select 'Full control' checkbox under 'Allow' at the bottom. Click OK. 

Start ImageJ by opening the ImageJ application from Program Files\ImageJ directory. Go to `Help` -> `Update ImageJ...` to check for any updates. Restart if asked to.

Select `Plugins` -> `Install` and select the `.java` file you want to install. Save the file into the `ImageJ\plugins` directory, which ought to be the default. The plugin will attempt to run immediately, if you have images already loaded.

The plugin should appear under the Plugins menu for the next time you want to use it.

### MacOS

These instructions were created using ImageJ2 version 1.53 from https://imagej.net/Downloads
This ImageJ2 doesn't come with a Java compiler. I used homebrew to install a seperate JDK:

    brew install --cask adoptopenjdk
    
Don't put the plugins into the plugins directory yet - keep them somewhere seperate. You can use `javac` manually in terminal to check that the `.java` file compiles without problems. Checking compile-time errors with the ImageJ installation script is a bit painful, so it's much faster to use this:

    javac -source 1.8 -target 1.8 -g -cp "/Applications/ImageJ.app/jars/*" your_plugin.java

Note the 1.8 version is deliberately chosen to be compatible with ImageJ 1.52.    
You may see these warnings, which you can ignore:

    warning: [options] bootstrap class path not set in conjunction with -source 8
    warning: Supported source version 'RELEASE_6' from annotation processor 'org.scijava.annotations.AnnotationProcessor' less than -source '8'

You can delete the `.class` file; ImageJ will remake it during installation anyway.    

Plugin installation is performed using ImageJ's menus:  `Plugins` -> `Install...` and selecting the `.java` file (not the `.class` file) to import. Save it into `/Applications/ImageJ.app/plugins`

You will likely see errors because the ImageJ jars directory is not in ImageJ's `java.class.path` , and the new javac won't know where ij.jar is when it first attempts to run. This is not a problem.
    
    ImageJ 2.0.0-rc-43/1.52n; Java 1.8.0_162 [64-bit]; Mac OS X 10.16; 49MB of 22120MB (<1%)
     
    warning: Supported source version 'RELEASE_6' from annotation processor 'org.scijava.annotations.AnnotationProcessor' less than -source '1.8'
    /Applications/ImageJ.app/plugins/your_script.java:8: error: package ij does not exist
    import ij.*;
    ^
    ......
    8 errors
    1 warning
    
Quit and reopen ImageJ.  The plugin ought to now appear in the `Plugins` menu and should run without the above error.

If you want to update/reinstall, make sure to delete or overwrite the old `.java` file in `/Applications/ImageJ.app/plugins` so you don't accidentally run the "old" version.

### Ubuntu

Using the imagej provided by the package manager:

    sudo apt install imagej
    
Now launch ImageJ, open the stack/images to work on, and then go to `Plugins`  -> `Install...` and select the `.java` file for your plugin. It will automatically save into  `$HOME/.imagej/plugins`.  The plugin will attempt to run immediately, if you have images already loaded.

The plugin should appear under the Plugins menu for the next time you want to use it.
