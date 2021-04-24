/*
    IMAGEJ PLUGIN - READ CHRONOS RAW FILE
    
    Tested on ImageJ 1.52 on all OSes. See Readme.md for install instructions.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2021 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 24/04/2021
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

    Version history:
        24/04/2021 - First version.

*/

import ij.*;
import ij.process.*;
import ij.gui.*;
import java.awt.*;
import ij.plugin.filter.*;
import ij.io.*;
import java.io.*;

public class Read_ChronosRaw implements PlugInFilter {
	
    static String versionString = "24/04/2021";
 
    //ImagePlus imp;
    String statusMessage="";
    int width=1280;
    int height=1024;
    int frame_start=1;
    int frame_end=-1;
    static String[] rawFormats = {"12-bit RAW", "16-bit RAW"};
    int rawFormat = 0;
    long nbytes = 0;
    double bpp = 0;
    double nFrames = 0;
    
	public int setup(String arg, ImagePlus imp) {
        if (arg.equals("about"))
            {showAbout(); return DONE;}
		//this.imp = imp;
		return NO_IMAGE_REQUIRED;
	}

	public void run(ImageProcessor ip) {
 
        // Locate the file
        OpenDialog od = new OpenDialog("Select RAW file", null);
        String folder = od.getDirectory();
        String file = od.getFileName();
        String path = folder + file;
        
        // Read length of the file
        File rawfile = new File(path);
        nbytes = rawfile.length();
        double mbytes = nbytes / 1048576.;
        statusMessage += String.format("Read %d bytes, %9.1f Mbytes", nbytes, mbytes);
        
        // Make dialog to figure out the width, height, no frames, etc.
        if (!optionsDialog()) return;
        
        // Calculate nFrames, bpp.
        // Check that size of image + number of frames makes sense.
        if (!checkImageSize()) return;
        
        // Create output as 16-bit mono.
        ImagePlus output = NewImage.createShortImage(file,width,height,
                                                     frame_end-frame_start+1,
                                                    NewImage.FILL_BLACK);
        
        // Start reading in.
        byte[] buffer = new byte[3];
        double offset = (frame_start-1)*width*height*bpp;
        try (FileInputStream fileInputStream = new FileInputStream(rawfile);)
        {
            // Skip starting frames
            if (offset>0) {
                fileInputStream.skip((long)offset);
                statusMessage += String.format(", offset %d bytes", (long)offset);
            }
            
            // Loop frames.
            for (int n=1;n<=frame_end-frame_start+1;n++) {
                // Create array for empty current image.
                //short[] p = (short[])output.getStack().getProcessor(n).getPixels();
                //short[] p = new short[width*height];
                
                // Loop pixel positions in frame, read to buffer p.
                for (int y=0;y<height;y++) {
                
                    if (rawFormat==0) {
                        for (int x=0;x<width;x+=2) {
                            fileInputStream.read(buffer,0,3);
                            
                            // debugging:
                            //output.getStack().getProcessor(n).putPixel(x,y,y+x);
                            //output.getStack().getProcessor(n).putPixel(x+1,y,y+x+1);
                            
                            
                            output.getStack().getProcessor(n).putPixel(x  ,y, (buffer[0]&0xf0)
                                                                            | (buffer[0]&0x0f)
                                                                            | (buffer[1]&0xf0) << 4);
                            
                            output.getStack().getProcessor(n).putPixel(x+1,y, (buffer[1]&0x0f)
                                                                            | (buffer[2]&0xf0) << 4
                                                                            | (buffer[2]&0x0f) << 4);
                                                                            
                        }
                    }
                    
                    if (rawFormat==1) {
                        for (int x=0;x<width;x++) {
                            fileInputStream.read(buffer,0,2);
                            // debugging:
                            //output.getStack().getProcessor(n).putPixel(x,y,y+x);
                            
                            output.getStack().getProcessor(n).putPixel(x,y,(buffer[0]) + (buffer[1]<<8) );
                        }
                    }
                }
                
                // write buffer and update progress bar.
                //output.getStack().getProcessor(n).setPixels(p);
                IJ.showProgress(n,frame_end-frame_start+1);
            }
            
        } catch (FileNotFoundException ex) {
            IJ.error("I/O error");
            return;
        } catch (IOException ex) {
            IJ.error("I/O error");
            return;
        }
        
        // Draw the newly created image's window...
        output.show(statusMessage);
        output.updateAndDraw();
        
	}
 
    void showAbout() {
        IJ.showMessage("About Read_ChronosRaw...",
                       versionString
                      );
    }
    
    boolean optionsDialog() {
        GenericDialog window = new GenericDialog("Chronos RAW Loader");
        window.addMessage("Dr Daniel Duke, LTRAC, Monash Uni");
        window.addMessage(versionString);
        window.addMessage(statusMessage);
        window.addNumericField("Width [pixels]",width,0);
        window.addNumericField("Height [pixels]",height,0);
        window.addNumericField("Start frame",frame_start,0);
        window.addNumericField("End frame",frame_end,0);
        window.addMessage("Setting end frame to -1 will load all frames.");
        window.addMessage("Otherwise, frame numbers must be >= 1");
        window.addChoice("Format",rawFormats,rawFormats[rawFormat]);
        
        window.showDialog();
        if (window.wasCanceled()) return false;
        
        width = (int)window.getNextNumber();
        height = (int)window.getNextNumber();
        frame_start = (int)window.getNextNumber();
        frame_end = (int)window.getNextNumber();
        rawFormat = window.getNextChoiceIndex();
        
        if ((rawFormat<0) || (rawFormat>1)) {
            IJ.error("Invalid selection for Raw format");
            return false;
        }
        
        if ((width<1) || (height<1)) {
            IJ.error("Width / height invalid");
            return false;
        }
        
        if (frame_start<1) {
            IJ.error("Start frame invalid");
            return false;
        }
        
        return true;
    }
    
    boolean checkImageSize() {
        if (rawFormat==0) bpp=1.5;
        if (rawFormat==1) bpp=2.0;
        if (bpp<=0) return false;
        
        nFrames = (double)nbytes/(double)width/(double)height/bpp;
        statusMessage += String.format(", %6.1f frames", nFrames);
        
        if (frame_end==-1) frame_end = (int)Math.floor(nFrames);
        
        if ((frame_end > nFrames) || (frame_start > nFrames)) {
           IJ.error("Requested start/end frame too large for image: "+statusMessage);
            return false;
        }
        
        if (frame_start>frame_end) {
            IJ.error("Start/end frame invalid");
            return false;
        }
        
        if (nFrames < 1.0) {
            IJ.error("Size of image does not match file size: "+statusMessage);
            return false;
        }
        
        return true;
    }

}
