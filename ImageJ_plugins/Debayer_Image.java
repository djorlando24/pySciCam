/*
    IMAGEJ PLUGIN
    BAYER DEMOSAIC OF RAW 16-BIT COLOUR CAMERA IMAGES
    
        Default settings are good for Chronos 1.4 colour cameras.
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
        23/04/2021 - First version.
        24/04/2021 - Comments on pixel ordering.

*/

import ij.*;
import ij.process.*;
import ij.gui.*;
import java.awt.*;
import ij.plugin.filter.*;

public class Debayer_Image implements PlugInFilter {

    static String versionString = "23/04/2021";

    ImagePlus imp;
    ImageProcessor ip;
    int width;
    int height;
    
    // Defaults.
    boolean normalize = false;
    boolean equalize = false;
    boolean stackHist = false;
    boolean median = false;
    boolean gauss = false;
    int radius = 2;
    
    static String[] orders = {"R-G-R-G", "B-G-B-G", "G-R-G-R", "G-B-G-B"};
    int row_order = 3;
    
    static String[] algorithms = {"Replication", "Bilinear", "Smooth Hue", "Adaptive Smooth Hue"};
    int algorithm = 0;
    
    static String[] outputTypes = {"Colour RGB 8 bits", "Mono seperate channels 16 bits", "Mono summed channels 16 bits"};
    int outputType = 0;
    
    //static String[] modes = {"replicate_decode", "average_decode", "adaptive_decode", "smooth_decode"};
    //int mode = 0;
    
    // Setup function ////////////////////////////////////////////////////////////
    public int setup(String arg, ImagePlus imp) {
        IJ.register(Debayer_Image.class);
        if(IJ.versionLessThan("1.32c"))
            return DONE;
        imp.unlock();
        this.imp = imp;
        return DOES_16;
    }

    // Main function called. ////////////////////////////////////////////////////////////
    public void run(ImageProcessor ip) {
    
        if (!optionsDialog()) return; // dialog box
    
        width = imp.getWidth();
        height = imp.getHeight();
        ImagePlus outputG = new ImagePlus();
        ImagePlus outputB = new ImagePlus();
        ImagePlus output = new ImagePlus();
        
        if (imp.getStackSize() > 1) { // Process stack ///////////////////////////////////////////////
            
            
            if (outputType == 0) { // 8bit RGB out
                output = NewImage.createRGBImage(imp.getTitle() + "_DEMOSAIC",
                        imp.getWidth(), imp.getHeight(),
                        imp.getStackSize(), NewImage.FILL_BLACK);
            }
            
            if (outputType == 1) { // 3x 16bit mono out
                output  = NewImage.createShortImage(imp.getTitle() + "_RED",
                        imp.getWidth(), imp.getHeight(),
                        imp.getStackSize(), NewImage.FILL_BLACK);
                outputG = NewImage.createShortImage(imp.getTitle() + "_GREEN",
                        imp.getWidth(), imp.getHeight(),
                        imp.getStackSize(), NewImage.FILL_BLACK);
                outputB = NewImage.createShortImage(imp.getTitle() + "_BLUE",
                        imp.getWidth(), imp.getHeight(),
                        imp.getStackSize(), NewImage.FILL_BLACK);
            }
            
            if (outputType == 2) { // 1x 16bit mono out
                output = NewImage.createShortImage(imp.getTitle() + "_DEMOSAIC",
                        imp.getWidth(), imp.getHeight(),
                        imp.getStackSize(), NewImage.FILL_BLACK);
            }
    
            ImageStack rawStack = imp.getStack();
            ImageStack rgb = new ImageStack(width, height, imp.getProcessor().getColorModel());
    
            int x, y;
            int intensityScaling = 1;
            if (ip.getMax()>256) intensityScaling = (int)(ip.getMax()/256.);
            int[] vals = {0,0,0};
            IJ.showProgress(0,imp.getStackSize());
            
            // loop slices in stack
            for (int n=1; n<=imp.getStackSize(); n++) {
                
                rgb = do_demosaic(rawStack.getProcessor(n), algorithm);
                
                if (outputType == 0) {
                    // convert each image in stack to 8bit RGB
                    for (x=0; x<width; x++) {
                        for (y=0; y<height; y++) {
                            vals[0] = (int)(rgb.getProcessor(1).getPixel(x,y)/intensityScaling);
                            vals[1] = (int)(rgb.getProcessor(2).getPixel(x,y)/intensityScaling);
                            vals[2] = (int)(rgb.getProcessor(3).getPixel(x,y)/intensityScaling);
                            output.getStack().getProcessor(n).putPixel(x,y,vals);
                        }
                    }
                    
                }
                
                if (outputType == 1) {
                    // save each image in stack into 3 seperate output stacks for R,G,B.
                    output.getStack().getProcessor(n).copyBits(rgb.getProcessor(1),0,0,Blitter.COPY); //Red
                    outputG.getStack().getProcessor(n).copyBits(rgb.getProcessor(2),0,0,Blitter.COPY); //Green
                    outputB.getStack().getProcessor(n).copyBits(rgb.getProcessor(3),0,0,Blitter.COPY); //Blue
                }
                
                if (outputType == 2) {
                    // save each image in stack into one output stack with summed channels
                    for (int m=1; m<=3; m++) {
                        output.getStack().getProcessor(n).copyBits(rgb.getProcessor(m), 0, 0, Blitter.ADD);
                    }
                }
                
                IJ.showProgress(n,imp.getStackSize());
            }
      
        } else { // Process single image into 3 channels as stack ////////////////////////////////////////
        
            ImageStack rgb = do_demosaic(imp.getProcessor(), algorithm);
            
            if (outputType == 2) {
                // Sum channels
                output = NewImage.createShortImage(imp.getTitle() + "_DEMOSAIC", width, height, 1, NewImage.FILL_BLACK);
                for (int n=1; n<=3; n++) {
                    output.getProcessor().copyBits(rgb.getProcessor(n), 0, 0, Blitter.ADD);
                }
            } else {
                // Keep rgb as-is (seperate channels)
                output = new ImagePlus(imp.getTitle() + "_DEMOSAIC", rgb);
            }
        }
                
        // draw output
        output.show();
        output.updateAndDraw();
        if ((outputType == 1) && (imp.getStackSize() > 1)) {
            outputG.show();
            outputG.updateAndDraw();
            outputB.show();
            outputB.updateAndDraw();
        }
        
        // Apply filters for any case except where multiple stacks are drawn.
        if (outputType != 1) {
            String options = "saturated=0.5";
            if (normalize) options = options + " normalize";
            if (equalize) options = options + " equalize";
            options = options + " normalize_all";
            if (stackHist) options = options + " use";
            
            if (median) IJ.run("Median...", "radius="+radius+" stack");
            if (gauss) IJ.run("Median...", "radius="+radius+" stack");
            if (normalize || equalize) IJ.run("Enhance Contrast", options);
        }
        
        // Convert a single image's 3 channels to 8 bit RGB colour if requested.
        if ((outputType == 0)  && (imp.getStackSize() <= 1))  IJ.run("Convert Stack to RGB");
        
    }

    // Dialog to allow selection of options. ////////////////////////////////////////////////////////////
    boolean optionsDialog() {
        GenericDialog window = new GenericDialog("Debayer_Image");
        window.addMessage("Dr Daniel Duke, LTRAC, Monash Uni");
        window.addMessage(versionString);
        window.addCheckbox("Normalize",normalize);
        window.addCheckbox("Equalize",equalize);
        window.addCheckbox("Stack Histogram",stackHist);
        //window.addCheckbox("Convert to 8-bit colour",showColour);
        window.addCheckbox("Apply median filter",median);
        window.addCheckbox("Apply Gauss filter",gauss);
        window.addNumericField("Median/Gauss Radius",radius,0);
        window.addChoice("Bayer filter type",orders,orders[row_order]);
        window.addChoice("Demosaic algorithm",algorithms,algorithms[algorithm]);
        window.addChoice("Output type",outputTypes,outputTypes[outputType]);
        //window.addChoice("Mode",modes,modes[mode]);
        window.showDialog();
        
        if (window.wasCanceled()) return false;
        
        normalize = window.getNextBoolean();
        equalize = window.getNextBoolean();
        stackHist = window.getNextBoolean();
        //showColour = window.getNextBoolean();
        median = window.getNextBoolean();
        gauss = window.getNextBoolean();
        radius = (int)window.getNextNumber();
        row_order = window.getNextChoiceIndex();
        algorithm = window.getNextChoiceIndex();
        outputType = window.getNextChoiceIndex();
        //mode = window.getNextChoiceIndex();
        
        if((row_order<0) || (row_order>3)) {
            IJ.error("Invalid selection for Bayer filter type (row_order)");
            return false;
        }
        
        if((outputType<0) || (outputType>2)) {
            IJ.error("Invalid selection for Output type");
            return false;
        }
        
        return true;
    }
    
    // Function to pick correct algorithm and apply to one image only ////////////////////
    ImageStack do_demosaic(ImageProcessor ip, int algorithm) {
        ImageStack rgb = new ImageStack(width, height, imp.getProcessor().getColorModel());
        switch (algorithm) {
            case 0: rgb = replicate_decode(ip, row_order); break;
            case 1: rgb  = average_decode(ip, row_order); break;
            case 2: rgb  = smooth_decode(ip, row_order); break;
            case 3: rgb  = adaptive_decode(ip, row_order); break;
            default: IJ.error("Invalid selection for algorithm");
        }
        return rgb;
    }
    
    // Replication algorithm  ////////////////////////////////////////////////////////////
    ImageStack replicate_decode(ImageProcessor ip, int row_order) {
        //ip = imp.getProcessor();
        width = ip.getWidth();
        height = ip.getHeight();
        int one = 0;
        ImageStack rgb = new ImageStack(width, height, ip.getColorModel());
        ImageProcessor r = new ShortProcessor(width,height);
        ImageProcessor g = new ShortProcessor(width,height);
        ImageProcessor b = new ShortProcessor(width,height);
        //Short[] pixels = ip.getPixels();


        if (row_order == 0 || row_order == 1) {
            for (int y=0; y<height; y+=2) {
                for (int x=0; x<width; x+=2) {
                    one = ip.getPixel(x,y);
                    b.putPixel(x,y,one);
                    b.putPixel(x+1,y,one);
                    b.putPixel(x,y+1,one);
                    b.putPixel(x+1,y+1,one);
                }
            }

            for (int y=1; y<height; y+=2) {
                for (int x=1; x<width; x+=2) {
                    one = ip.getPixel(x,y);
                    r.putPixel(x,y,one);
                    r.putPixel(x+1,y,one);
                    r.putPixel(x,y+1,one);
                    r.putPixel(x+1,y+1,one);
                }
            }

            for (int y=0; y<height; y+=2) {
                for (int x=1; x<width; x+=2) {
                    one = ip.getPixel(x,y);
                    g.putPixel(x,y,one);
                    g.putPixel(x+1,y,one);
                }
            }

            for (int y=1; y<height; y+=2) {
                for (int x=0; x<width; x+=2) {
                    one = ip.getPixel(x,y);
                    g.putPixel(x,y,one);
                    g.putPixel(x+1,y,one);
                }
            }

            if (row_order == 0) {
                rgb.addSlice("red",b);
                rgb.addSlice("green",g);
                rgb.addSlice("blue",r);
            }
            else if (row_order == 1) {
                rgb.addSlice("red",r);
                rgb.addSlice("green",g);
                rgb.addSlice("blue",b);
            }
        }

        else if (row_order == 2 || row_order == 3) {
            for (int y=1; y<height; y+=2) {
                for (int x=0; x<width; x+=2) {
                    one = ip.getPixel(x,y);
                    b.putPixel(x,y,one);
                    b.putPixel(x+1,y,one);
                    b.putPixel(x,y+1,one);
                    b.putPixel(x+1,y+1,one);
                }
            }

            for (int y=0; y<height; y+=2) {
                for (int x=1; x<width; x+=2) {
                    one = ip.getPixel(x,y);
                    r.putPixel(x,y,one);
                    r.putPixel(x+1,y,one);
                    r.putPixel(x,y+1,one);
                    r.putPixel(x+1,y+1,one);
                }
            }

            for (int y=0; y<height; y+=2) {
                for (int x=0; x<width; x+=2) {
                    one = ip.getPixel(x,y);
                    g.putPixel(x,y,one);
                    g.putPixel(x+1,y,one);
                }
            }

            for (int y=1; y<height; y+=2) {
                for (int x=1; x<width; x+=2) {
                    one = ip.getPixel(x,y);
                    g.putPixel(x,y,one);
                    g.putPixel(x+1,y,one);
                }
            }

            if (row_order == 2) {
                rgb.addSlice("red",b);
                rgb.addSlice("green",g);
                rgb.addSlice("blue",r);
            }
            else if (row_order == 3) {
                rgb.addSlice("red",r);
                rgb.addSlice("green",g);
                rgb.addSlice("blue",b);
            }
        }

        return rgb;


    }

    // Bilinear algorithm  ////////////////////////////////////////////////////////////
    ImageStack average_decode(ImageProcessor ip, int row_order) {
        //ip = imp.getProcessor();
        width = ip.getWidth();
        height = ip.getHeight();
        int one = 0;
        int two = 0;
        int three = 0;
        int four = 0;
        ImageStack rgb = new ImageStack(width, height, ip.getColorModel());
        ImageProcessor r = new ShortProcessor(width,height);
        ImageProcessor g = new ShortProcessor(width,height);
        ImageProcessor b = new ShortProcessor(width,height);
        //Short[] pixels = ip.getPixels();


        if (row_order == 0 || row_order == 1) {
            for (int y=0; y<height; y+=2) {
                for (int x=0; x<width; x+=2) {
                    one = ip.getPixel(x,y);
                    two = ip.getPixel(x+2,y);
                    three = ip.getPixel(x,y+2);
                    four = ip.getPixel(x+2,y+2);

                    b.putPixel(x,y,one);
                    b.putPixel(x+1,y,(one+two)/2);
                    b.putPixel(x,y+1,(one+three)/2);
                    b.putPixel(x+1,y+1,(one+two+three+four)/4);
                }
            }

            for (int y=1; y<height; y+=2) {
                for (int x=1; x<width; x+=2) {
                    one = ip.getPixel(x,y);
                    two = ip.getPixel(x+2,y);
                    three = ip.getPixel(x,y+2);
                    four = ip.getPixel(x+2,y+2);

                    r.putPixel(x,y,one);
                    r.putPixel(x+1,y,(one+two)/2);
                    r.putPixel(x,y+1,(one+three)/2);
                    r.putPixel(x+1,y+1,(one+two+three+four)/4);
                }
            }

            for (int y=0; y<height; y+=2) {
                for (int x=1; x<width; x+=2) {
                    one = ip.getPixel(x,y);
                    two = ip.getPixel(x+2,y);
                    three = ip.getPixel(x+1,y+1);
                    four = ip.getPixel(x+1,y-1);

                    g.putPixel(x,y,one);
                    g.putPixel(x+1,y,(one+two+three+four)/4);
                }
            }

            for (int y=1; y<height; y+=2) {
                for (int x=0; x<width; x+=2) {
                    one = ip.getPixel(x,y);
                    two = ip.getPixel(x+2,y);
                    three = ip.getPixel(x+1,y+1);
                    four = ip.getPixel(x+1,y-1);

                    g.putPixel(x,y,one);
                    g.putPixel(x+1,y,(one+two+three+four)/4);
                }
            }

            if (row_order == 0) {
                rgb.addSlice("red",b);
                rgb.addSlice("green",g);
                rgb.addSlice("blue",r);
            }
            else if (row_order == 1) {
                rgb.addSlice("red",r);
                rgb.addSlice("green",g);
                rgb.addSlice("blue",b);
            }
        }

        else if (row_order == 2 || row_order == 3) {
            for (int y=1; y<height; y+=2) {
                for (int x=0; x<width; x+=2) {
                    one = ip.getPixel(x,y);
                    two = ip.getPixel(x+2,y);
                    three = ip.getPixel(x,y+2);
                    four = ip.getPixel(x+2,y+2);

                    b.putPixel(x,y,one);
                    b.putPixel(x+1,y,(one+two)/2);
                    b.putPixel(x,y+1,(one+three)/2);
                    b.putPixel(x+1,y+1,(one+two+three+four)/4);
                }
            }

            for (int y=0; y<height; y+=2) {
                for (int x=1; x<width; x+=2) {
                    one = ip.getPixel(x,y);
                    two = ip.getPixel(x+2,y);
                    three = ip.getPixel(x,y+2);
                    four = ip.getPixel(x+2,y+2);

                    r.putPixel(x,y,one);
                    r.putPixel(x+1,y,(one+two)/2);
                    r.putPixel(x,y+1,(one+three)/2);
                    r.putPixel(x+1,y+1,(one+two+three+four)/4);
                }
            }

            for (int y=0; y<height; y+=2) {
                for (int x=0; x<width; x+=2) {
                    one = ip.getPixel(x,y);
                    two = ip.getPixel(x+2,y);
                    three = ip.getPixel(x+1,y+1);
                    four = ip.getPixel(x+1,y-1);

                    g.putPixel(x,y,one);
                    g.putPixel(x+1,y,(one+two+three+four)/4);
                }
            }

            for (int y=1; y<height; y+=2) {
                for (int x=1; x<width; x+=2) {
                    one = ip.getPixel(x,y);
                    two = ip.getPixel(x+2,y);
                    three = ip.getPixel(x+1,y+1);
                    four = ip.getPixel(x+1,y-1);

                    g.putPixel(x,y,one);
                    g.putPixel(x+1,y,(one+two+three+four)/4);
                }
            }

            if (row_order == 2) {
                rgb.addSlice("red",b);
                rgb.addSlice("green",g);
                rgb.addSlice("blue",r);
            }
            else if (row_order == 3) {
                rgb.addSlice("red",r);
                rgb.addSlice("green",g);
                rgb.addSlice("blue",b);
            }
        }

        return rgb;


    }

    // Smooth hue algorithm  ////////////////////////////////////////////////////////////
    ImageStack smooth_decode(ImageProcessor ip, int row_order) {
        //ip = imp.getProcessor();
        width = ip.getWidth();
        height = ip.getHeight();
        double G1 = 0;
        double G2 = 0;
        double G3 = 0;
        double G4 = 0;
        double G5 = 0;
        double G6 = 0;
        double G7 = 0;
        double G8 = 0;
        double G9 = 0;
        double B1 = 0;
        double B2 = 0;
        double B3 = 0;
        double B4 = 0;
        double R1 = 0;
        double R2 = 0;
        double R3 = 0;
        double R4 = 0;
        ImageStack rgb = new ImageStack(width, height, ip.getColorModel());
        ImageProcessor r = new ShortProcessor(width,height);
        ImageProcessor g = new ShortProcessor(width,height);
        ImageProcessor b = new ShortProcessor(width,height);
        //Short[] pixels = ip.getPixels();


        if (row_order == 0 || row_order == 1) {
            //Solve for green pixels first
            for (int y=0; y<height; y+=2) {
                for (int x=1; x<width; x+=2) {
                    G1 = ip.getPixel(x,y);
                    G2 = ip.getPixel(x+2,y);
                    G3 = ip.getPixel(x+1,y+1);
                    G4 = ip.getPixel(x+1,y-1);

                    g.putPixel(x,y,(int)G1);
                    if (y==0) g.putPixel(x+1,y,(int)((G1+G2+G3)/3));
                    else g.putPixel(x+1,y,(int)((G1+G2+G3+G4)/4));
                    if (x==1) g.putPixel(x-1,y,(int)((G1+G4+ip.getPixel(x-1,y+1))/3));
                }
            }

            for (int x=0; x<width; x+=2) {
                for (int y=1; y<height; y+=2) {

                    G1 = ip.getPixel(x,y);
                    G2 = ip.getPixel(x+2,y);
                    G3 = ip.getPixel(x+1,y+1);
                    G4 = ip.getPixel(x+1,y-1);

                    g.putPixel(x,y,(int)G1);
                    if (x==0) g.putPixel(x+1,y,(int)((G1+G2+G3)/3));
                    else g.putPixel(x+1,y,(int)((G1+G2+G3+G4)/4));
                }
            }

            g.putPixel(0,0,(int)((ip.getPixel(0,1)+ip.getPixel(1,0))/2));


            for (int y=0; y<height; y+=2) {
                for (int x=0; x<width; x+=2) {
                    B1 = ip.getPixel(x,y);
                    B2 = ip.getPixel(x+2,y);
                    B3 = ip.getPixel(x,y+2);
                    B4 = ip.getPixel(x+2,y+2);
                    G1 = g.getPixel(x,y);
                    G2 = g.getPixel(x+2,y);
                    G3 = g.getPixel(x,y+2);
                    G4 = g.getPixel(x+2,y+2);
                    G5 = g.getPixel(x+1,y);
                    G6 = g.getPixel(x,y+1);
                    G9 = g.getPixel(x+1,y+1);
                    if(G1==0) G1=1;
                    if(G2==0) G2=1;
                    if(G3==0) G3=1;
                    if(G4==0) G4=1;

                    b.putPixel(x,y,(int)(B1));
                    b.putPixel(x+1,y,(int)((G5/2 * ((B1/G1) + (B2/G2)) )) );
                    b.putPixel(x,y+1,(int)(( G6/2 * ((B1/G1) + (B3/G3)) )) );
                    b.putPixel(x+1,y+1, (int)((G9/4 *  ((B1/G1) + (B3/G3) + (B2/G2) + (B4/G4)) )) );

                }
            }

            for (int y=1; y<height; y+=2) {
                for (int x=1; x<width; x+=2) {
                    R1 = ip.getPixel(x,y);
                    R2 = ip.getPixel(x+2,y);
                    R3 = ip.getPixel(x,y+2);
                    R4 = ip.getPixel(x+2,y+2);
                    G1 = g.getPixel(x,y);
                    G2 = g.getPixel(x+2,y);
                    G3 = g.getPixel(x,y+2);
                    G4 = g.getPixel(x+2,y+2);
                    G5 = g.getPixel(x+1,y);
                    G6 = g.getPixel(x,y+1);
                    G9 = g.getPixel(x+1,y+1);
                    if(G1==0) G1=1;
                    if(G2==0) G2=1;
                    if(G3==0) G3=1;
                    if(G4==0) G4=1;

                    r.putPixel(x,y,(int)(R1));
                    r.putPixel(x+1,y,(int)((G5/2 * ((R1/G1) + (R2/G2) )) ));
                    r.putPixel(x,y+1,(int)(( G6/2 * ((R1/G1) + (R3/G3) )) ));
                    r.putPixel(x+1,y+1, (int)((G9/4 *  ((R1/G1) + (R3/G3) + (R2/G2) + (R4/G4)) ) ));
                }
            }


            if (row_order == 0) {
                rgb.addSlice("red",b);
                rgb.addSlice("green",g);
                rgb.addSlice("blue",r);
            }
            else if (row_order == 1) {
                rgb.addSlice("red",r);
                rgb.addSlice("green",g);
                rgb.addSlice("blue",b);
            }
        }

        else if (row_order == 2 || row_order == 3) {

            for (int y=0; y<height; y+=2) {
                for (int x=0; x<width; x+=2) {
                    G1 = ip.getPixel(x,y);
                    G2 = ip.getPixel(x+2,y);
                    G3 = ip.getPixel(x+1,y+1);
                    G4 = ip.getPixel(x+1,y-1);

                    g.putPixel(x,y,(int)G1);
                    if (y==0) g.putPixel(x+1,y,(int)((G1+G2+G3)/3));
                    else g.putPixel(x+1,y,(int)((G1+G2+G3+G4)/4));
                    if (x==1) g.putPixel(x-1,y,(int)((G1+G4+ip.getPixel(x-1,y+1))/3));
                }
            }

            for (int y=1; y<height; y+=2) {
                for (int x=1; x<width; x+=2) {
                    G1 = ip.getPixel(x,y);
                    G2 = ip.getPixel(x+2,y);
                    G3 = ip.getPixel(x+1,y+1);
                    G4 = ip.getPixel(x+1,y-1);

                    g.putPixel(x,y,(int)G1);
                    if (x==0) g.putPixel(x+1,y,(int)((G1+G2+G3)/3));
                    else g.putPixel(x+1,y,(int)((G1+G2+G3+G4)/4));
                }
            }

            g.putPixel(0,0,(int)((ip.getPixel(0,1)+ip.getPixel(1,0))/2));

            for (int y=1; y<height; y+=2) {
                for (int x=0; x<width; x+=2) {
                    B1 = ip.getPixel(x,y);
                    B2 = ip.getPixel(x+2,y);
                    B3 = ip.getPixel(x,y+2);
                    B4 = ip.getPixel(x+2,y+2);
                    G1 = g.getPixel(x,y);
                    G2 = g.getPixel(x+2,y);
                    G3 = g.getPixel(x,y+2);
                    G4 = g.getPixel(x+2,y+2);
                    G5 = g.getPixel(x+1,y);
                    G6 = g.getPixel(x,y+1);
                    G9 = g.getPixel(x+1,y+1);
                    if(G1==0) G1=1;
                    if(G2==0) G2=1;
                    if(G3==0) G3=1;
                    if(G4==0) G4=1;

                    b.putPixel(x,y,(int)(B1));
                    b.putPixel(x+1,y,(int)((G5/2 * ((B1/G1) + (B2/G2)) )) );
                    b.putPixel(x,y+1,(int)(( G6/2 * ((B1/G1) + (B3/G3)) )) );
                    b.putPixel(x+1,y+1, (int)((G9/4 *  ((B1/G1) + (B3/G3) + (B2/G2) + (B4/G4)) )) );

                }
            }

            for (int y=0; y<height; y+=2) {
                for (int x=1; x<width; x+=2) {
                    R1 = ip.getPixel(x,y);
                    R2 = ip.getPixel(x+2,y);
                    R3 = ip.getPixel(x,y+2);
                    R4 = ip.getPixel(x+2,y+2);
                    G1 = g.getPixel(x,y);
                    G2 = g.getPixel(x+2,y);
                    G3 = g.getPixel(x,y+2);
                    G4 = g.getPixel(x+2,y+2);
                    G5 = g.getPixel(x+1,y);
                    G6 = g.getPixel(x,y+1);
                    G9 = g.getPixel(x+1,y+1);
                    if(G1==0) G1=1;
                    if(G2==0) G2=1;
                    if(G3==0) G3=1;
                    if(G4==0) G4=1;

                    r.putPixel(x,y,(int)(R1));
                    r.putPixel(x+1,y,(int)((G5/2 * ((R1/G1) + (R2/G2) )) ));
                    r.putPixel(x,y+1,(int)(( G6/2 * ((R1/G1) + (R3/G3) )) ));
                    r.putPixel(x+1,y+1, (int)((G9/4 *  ((R1/G1) + (R3/G3) + (R2/G2) + (R4/G4)) ) ));
                }
            }



            if (row_order == 2) {
                rgb.addSlice("red",b);
                rgb.addSlice("green",g);
                rgb.addSlice("blue",r);
            }
            else if (row_order == 3) {
                rgb.addSlice("red",r);
                rgb.addSlice("green",g);
                rgb.addSlice("blue",b);
            }
        }

        return rgb;


    }

    // Adaptive Smooth Hue algorithm (Edge detecting) ////////////////////////////////////////////////////////////
    ImageStack adaptive_decode(ImageProcessor ip, int row_order) {
        //ip = imp.getProcessor();
        width = ip.getWidth();
        height = ip.getHeight();
        double G1 = 0;
        double G2 = 0;
        double G3 = 0;
        double G4 = 0;
        double G5 = 0;
        double G6 = 0;
        double G7 = 0;
        double G8 = 0;
        double G9 = 0;
        double B1 = 0;
        double B2 = 0;
        double B3 = 0;
        double B4 = 0;
        double B5 = 0;
        double R1 = 0;
        double R2 = 0;
        double R3 = 0;
        double R4 = 0;
        double R5 = 0;
        double N = 0;
        double S = 0;
        double E = 0;
        double W = 0;
        ImageStack rgb = new ImageStack(width, height, ip.getColorModel());
        ImageProcessor r = new ShortProcessor(width,height);
        ImageProcessor g = new ShortProcessor(width,height);
        ImageProcessor b = new ShortProcessor(width,height);
        //Short[] pixels = ip.getPixels();


        if (row_order == 0 || row_order == 1) {
            //Solve for green pixels first
            for (int y=0; y<height; y+=2) {
                for (int x=1; x<width; x+=2) {
                    G1 = ip.getPixel(x,y);
                    G2 = ip.getPixel(x+2,y);
                    G3 = ip.getPixel(x+1,y+1);
                    G4 = ip.getPixel(x+1,y-1);
                    R1 = ip.getPixel(x-1,y);
                    R2 = ip.getPixel(x+3,y);
                    R3 = ip.getPixel(x+1,y+2);
                    R4 = ip.getPixel(x+1,y-2);
                    R5 = ip.getPixel(x+1,y+1);

                    N = Math.abs(R4-R5)*2 + Math.abs(G4-G3);
                    S = Math.abs(R5-R3)*2 + Math.abs(G4-G3);
                    E = Math.abs(R5-R2)*2 + Math.abs(G1-G2);
                    W = Math.abs(R1-R5)*2 + Math.abs(G1-G2);

                    if(N<S && N<E && N<W) {
                        g.putPixel(x+1,y,(int)((G4*3 + R5 + G3 - R4)/4));
                    }

                    else if(S<N && S<E && S<W) {
                        g.putPixel(x+1,y,(int)((G3*3 + R5 + G4 - R3)/4));
                    }

                    else if(W<N && W<E && W<S) {
                        g.putPixel(x+1,y,(int)((G1*3 + R5 + G2 - R1)/4));
                    }

                    else if(E<N && E<S && E<W) {
                        g.putPixel(x+1,y,(int)((G2*3 + R5 + G1 - R2)/4));
                    }

                    g.putPixel(x,y,(int)G1);

                    if (y==0) g.putPixel(x+1,y,(int)((G1+G2+G3)/3));
                    else g.putPixel(x+1,y,(int)((G1+G2+G3+G4)/4));
                    if (x==1) g.putPixel(x-1,y,(int)((G1+G4+ip.getPixel(x-1,y+1))/3));
                }
            }

            for (int x=0; x<width; x+=2) {
                for (int y=1; y<height; y+=2) {
                    G1 = ip.getPixel(x,y);
                    G2 = ip.getPixel(x+2,y);
                    G3 = ip.getPixel(x+1,y+1);
                    G4 = ip.getPixel(x+1,y-1);
                    R1 = ip.getPixel(x-1,y);
                    R2 = ip.getPixel(x+3,y);
                    R3 = ip.getPixel(x+1,y+2);
                    R4 = ip.getPixel(x+1,y-2);
                    R5 = ip.getPixel(x+1,y+1);

                    N = Math.abs(R4-R5)*2 + Math.abs(G4-G3);
                    S = Math.abs(R5-R3)*2 + Math.abs(G4-G3);
                    E = Math.abs(R5-R2)*2 + Math.abs(G1-G2);
                    W = Math.abs(R1-R5)*2 + Math.abs(G1-G2);

                    if(N<S && N<E && N<W) {
                        g.putPixel(x+1,y,(int)((G4*3 + R5 + G3 - R4)/4));
                    }

                    else if(S<N && S<E && S<W) {
                        g.putPixel(x+1,y,(int)((G3*3 + R5 + G4 - R3)/4));
                    }

                    else if(W<N && W<E && W<S) {
                        g.putPixel(x+1,y,(int)((G1*3 + R5 + G2 - R1)/4));
                    }

                    else if(E<N && E<S && E<W) {
                        g.putPixel(x+1,y,(int)((G2*3 + R5 + G1 - R2)/4));
                    }

                    g.putPixel(x,y,(int)G1);
                    if (x==0) g.putPixel(x+1,y,(int)((G1+G2+G3)/3));
                    else g.putPixel(x+1,y,(int)((G1+G2+G3+G4)/4));
                }
            }

            g.putPixel(0,0,(int)((ip.getPixel(0,1)+ip.getPixel(1,0))/2));


            for (int y=0; y<height; y+=2) {
                for (int x=0; x<width; x+=2) {
                    B1 = ip.getPixel(x,y);
                    B2 = ip.getPixel(x+2,y);
                    B3 = ip.getPixel(x,y+2);
                    B4 = ip.getPixel(x+2,y+2);
                    G1 = g.getPixel(x,y);
                    G2 = g.getPixel(x+2,y);
                    G3 = g.getPixel(x,y+2);
                    G4 = g.getPixel(x+2,y+2);
                    G5 = g.getPixel(x+1,y);
                    G6 = g.getPixel(x,y+1);
                    G9 = g.getPixel(x+1,y+1);
                    if(G1==0) G1=1;
                    if(G2==0) G2=1;
                    if(G3==0) G3=1;
                    if(G4==0) G4=1;

                    b.putPixel(x,y,(int)(B1));
                    b.putPixel(x+1,y,(int)((G5/2 * ((B1/G1) + (B2/G2)) )) );
                    b.putPixel(x,y+1,(int)(( G6/2 * ((B1/G1) + (B3/G3)) )) );
                    b.putPixel(x+1,y+1, (int)((G9/4 *  ((B1/G1) + (B3/G3) + (B2/G2) + (B4/G4)) )) );

                }
            }

            for (int y=1; y<height; y+=2) {
                for (int x=1; x<width; x+=2) {
                    R1 = ip.getPixel(x,y);
                    R2 = ip.getPixel(x+2,y);
                    R3 = ip.getPixel(x,y+2);
                    R4 = ip.getPixel(x+2,y+2);
                    G1 = g.getPixel(x,y);
                    G2 = g.getPixel(x+2,y);
                    G3 = g.getPixel(x,y+2);
                    G4 = g.getPixel(x+2,y+2);
                    G5 = g.getPixel(x+1,y);
                    G6 = g.getPixel(x,y+1);
                    G9 = g.getPixel(x+1,y+1);
                    if(G1==0) G1=1;
                    if(G2==0) G2=1;
                    if(G3==0) G3=1;
                    if(G4==0) G4=1;

                    r.putPixel(x,y,(int)(R1));
                    r.putPixel(x+1,y,(int)((G5/2 * ((R1/G1) + (R2/G2) )) ));
                    r.putPixel(x,y+1,(int)(( G6/2 * ((R1/G1) + (R3/G3) )) ));
                    r.putPixel(x+1,y+1, (int)((G9/4 *  ((R1/G1) + (R3/G3) + (R2/G2) + (R4/G4)) ) ));
                }
            }


            if (row_order == 0) {
                rgb.addSlice("red",b);
                rgb.addSlice("green",g);
                rgb.addSlice("blue",r);
            }
            else if (row_order == 1) {
                rgb.addSlice("red",r);
                rgb.addSlice("green",g);
                rgb.addSlice("blue",b);
            }
        }

        else if (row_order == 2 || row_order == 3) {

            for (int y=0; y<height; y+=2) {
                for (int x=0; x<width; x+=2) {
                    G1 = ip.getPixel(x,y);
                    G2 = ip.getPixel(x+2,y);
                    G3 = ip.getPixel(x+1,y+1);
                    G4 = ip.getPixel(x+1,y-1);
                    R1 = ip.getPixel(x-1,y);
                    R2 = ip.getPixel(x+3,y);
                    R3 = ip.getPixel(x+1,y+2);
                    R4 = ip.getPixel(x+1,y-2);
                    R5 = ip.getPixel(x+1,y+1);

                    N = Math.abs(R4-R5)*2 + Math.abs(G4-G3);
                    S = Math.abs(R5-R3)*2 + Math.abs(G4-G3);
                    E = Math.abs(R5-R2)*2 + Math.abs(G1-G2);
                    W = Math.abs(R1-R5)*2 + Math.abs(G1-G2);

                    if(N<S && N<E && N<W) {
                        g.putPixel(x+1,y,(int)((G4*3 + R5 + G3 - R4)/4));
                    }

                    else if(S<N && S<E && S<W) {
                        g.putPixel(x+1,y,(int)((G3*3 + R5 + G4 - R3)/4));
                    }

                    else if(W<N && W<E && W<S) {
                        g.putPixel(x+1,y,(int)((G1*3 + R5 + G2 - R1)/4));
                    }

                    else if(E<N && E<S && E<W) {
                        g.putPixel(x+1,y,(int)((G2*3 + R5 + G1 - R2)/4));
                    }

                    g.putPixel(x,y,(int)G1);
                    if (y==0) g.putPixel(x+1,y,(int)((G1+G2+G3)/3));
                    else g.putPixel(x+1,y,(int)((G1+G2+G3+G4)/4));
                    if (x==1) g.putPixel(x-1,y,(int)((G1+G4+ip.getPixel(x-1,y+1))/3));
                }
            }

            for (int y=1; y<height; y+=2) {
                for (int x=1; x<width; x+=2) {
                    G1 = ip.getPixel(x,y);
                    G2 = ip.getPixel(x+2,y);
                    G3 = ip.getPixel(x+1,y+1);
                    G4 = ip.getPixel(x+1,y-1);
                    R1 = ip.getPixel(x-1,y);
                    R2 = ip.getPixel(x+3,y);
                    R3 = ip.getPixel(x+1,y+2);
                    R4 = ip.getPixel(x+1,y-2);
                    R5 = ip.getPixel(x+1,y+1);

                    N = Math.abs(R4-R5)*2 + Math.abs(G4-G3);
                    S = Math.abs(R5-R3)*2 + Math.abs(G4-G3);
                    E = Math.abs(R5-R2)*2 + Math.abs(G1-G2);
                    W = Math.abs(R1-R5)*2 + Math.abs(G1-G2);

                    if(N<S && N<E && N<W) {
                        g.putPixel(x+1,y,(int)((G4*3 + R5 + G3 - R4)/4));
                    }

                    else if(S<N && S<E && S<W) {
                        g.putPixel(x+1,y,(int)((G3*3 + R5 + G4 - R3)/4));
                    }

                    else if(W<N && W<E && W<S) {
                        g.putPixel(x+1,y,(int)((G1*3 + R5 + G2 - R1)/4));
                    }

                    else if(E<N && E<S && E<W) {
                        g.putPixel(x+1,y,(int)((G2*3 + R5 + G1 - R2)/4));
                    }

                    g.putPixel(x,y,(int)G1);
                    if (x==0) g.putPixel(x+1,y,(int)((G1+G2+G3)/3));
                    else g.putPixel(x+1,y,(int)((G1+G2+G3+G4)/4));
                }
            }

            g.putPixel(0,0,(int)((ip.getPixel(0,1)+ip.getPixel(1,0))/2));

            for (int y=1; y<height; y+=2) {
                for (int x=0; x<width; x+=2) {
                    B1 = ip.getPixel(x,y);
                    B2 = ip.getPixel(x+2,y);
                    B3 = ip.getPixel(x,y+2);
                    B4 = ip.getPixel(x+2,y+2);
                    G1 = g.getPixel(x,y);
                    G2 = g.getPixel(x+2,y);
                    G3 = g.getPixel(x,y+2);
                    G4 = g.getPixel(x+2,y+2);
                    G5 = g.getPixel(x+1,y);
                    G6 = g.getPixel(x,y+1);
                    G9 = g.getPixel(x+1,y+1);
                    if(G1==0) G1=1;
                    if(G2==0) G2=1;
                    if(G3==0) G3=1;
                    if(G4==0) G4=1;

                    b.putPixel(x,y,(int)(B1));
                    b.putPixel(x+1,y,(int)((G5/2 * ((B1/G1) + (B2/G2)) )) );
                    b.putPixel(x,y+1,(int)(( G6/2 * ((B1/G1) + (B3/G3)) )) );
                    b.putPixel(x+1,y+1, (int)((G9/4 *  ((B1/G1) + (B3/G3) + (B2/G2) + (B4/G4)) )) );

                }
            }

            for (int y=0; y<height; y+=2) {
                for (int x=1; x<width; x+=2) {
                    R1 = ip.getPixel(x,y);
                    R2 = ip.getPixel(x+2,y);
                    R3 = ip.getPixel(x,y+2);
                    R4 = ip.getPixel(x+2,y+2);
                    G1 = g.getPixel(x,y);
                    G2 = g.getPixel(x+2,y);
                    G3 = g.getPixel(x,y+2);
                    G4 = g.getPixel(x+2,y+2);
                    G5 = g.getPixel(x+1,y);
                    G6 = g.getPixel(x,y+1);
                    G9 = g.getPixel(x+1,y+1);
                    if(G1==0) G1=1;
                    if(G2==0) G2=1;
                    if(G3==0) G3=1;
                    if(G4==0) G4=1;

                    r.putPixel(x,y,(int)(R1));
                    r.putPixel(x+1,y,(int)((G5/2 * ((R1/G1) + (R2/G2) )) ));
                    r.putPixel(x,y+1,(int)(( G6/2 * ((R1/G1) + (R3/G3) )) ));
                    r.putPixel(x+1,y+1, (int)((G9/4 *  ((R1/G1) + (R3/G3) + (R2/G2) + (R4/G4)) ) ));
                }
            }



            if (row_order == 2) {
                rgb.addSlice("red",b);
                rgb.addSlice("green",g);
                rgb.addSlice("blue",r);
            }
            else if (row_order == 3) {
                rgb.addSlice("red",r);
                rgb.addSlice("green",g);
                rgb.addSlice("blue",b);
            }
        }

        return rgb;


    }

}
