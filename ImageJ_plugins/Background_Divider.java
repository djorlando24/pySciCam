/*
    IMAGEJ PLUGIN - BACKGROUND DIVISION
    
        Takes the average of the first few images and divides all other stack
        images by that background. Converts data to float.
        
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

*/

import ij.*;
import ij.process.*;
import ij.gui.*;
import java.awt.*;
import ij.plugin.filter.*;

public class Background_Divider implements PlugInFilter {

    static String versionString = "24/04/2021";
    int bkgnd_start = 1;
    int bkgnd_end = 10;
    int fg_start = 11;
    int fg_end = -1;
    float out_min = (float)-10.;
    float out_max = (float)10.;
    boolean clip_output = false;
    boolean invert_output = false;
    static float one = (float)1.0;
    
    ImagePlus imp;
        
    // Setup function ////////////////////////////////////////////////////////////
	public int setup(String arg, ImagePlus imp) {
        IJ.register(Background_Divider.class);
        if(IJ.versionLessThan("1.32c")) return DONE;
        if (arg.equals("about")) {showAbout(); return DONE;}
        imp.unlock();
		this.imp = imp;
		return STACK_REQUIRED+DOES_ALL; // don't use DOES_STACKS, this will re-run the program on every frame!
	}

    // Main function called. ////////////////////////////////////////////////////////////
	public void run(ImageProcessor ip) {
    
        // default frame numbers
        if (imp.getStackSize() < bkgnd_end) bkgnd_end = 2;
        if (imp.getStackSize() < fg_start) fg_start = bkgnd_end + 1;
        if (imp.getStackSize() < fg_end) fg_end = imp.getStackSize();
        
        if (!optionsDialog()) return; // dialog box
        
        // sanitize frame numbers
        if (bkgnd_end==-1) bkgnd_end=imp.getStackSize();
        if (fg_end==-1) fg_end=imp.getStackSize();
        if ((imp.getStackSize() < bkgnd_start) || (bkgnd_start<1) || (bkgnd_start>bkgnd_end)) {
            IJ.error("Background start frame out of range");
            return;
        }
        if ((imp.getStackSize() < bkgnd_end) || (bkgnd_end<1)) {
            IJ.error("Background end frame out of range");
            return;
        }
        if ((imp.getStackSize() < fg_start) || (fg_start<1) || (fg_start>fg_end)) {
            IJ.error("Foreground start frame out of range");
            return;
        }
        if ((imp.getStackSize() < fg_end) || (fg_end<1)) {
            IJ.error("Foreground end frame out of range");
            return;
        }
        
        // Make background
        ImagePlus bkgnd = NewImage.createFloatImage(imp.getTitle() + "_AVG_BKGND",
                          imp.getWidth(), imp.getHeight(),
                            1, NewImage.FILL_BLACK);
        
        ImageStack input = imp.getStack();
        
        // Sum all background frames. Ok to avoid overflow since destination is float-type.
        for (int n=bkgnd_start; n<=bkgnd_end; n++) {
            bkgnd.getStack().getProcessor(1).copyBits(input.getProcessor(n),0,0,Blitter.ADD);
        }
        
        // Divide intensities by n frames to get average intensity
        float n_bkgnd = (float)(bkgnd_end - bkgnd_start+1);
        float[] p;
        p = (float[])bkgnd.getStack().getProcessor(1).getPixels();
        for (int n=0; n<p.length; n++) p[n] /= n_bkgnd;
        bkgnd.getStack().getProcessor(1).setPixels(p);
        
        // Show bkgnd to the user
        bkgnd.show();
        bkgnd.updateAndDraw();
        
        
        // Make foreground
        ImagePlus output = NewImage.createFloatImage(imp.getTitle() + "_BKGND_REMOVED",
                            imp.getWidth(), imp.getHeight(),
                            fg_end-fg_start+1, NewImage.FILL_BLACK);
        
        // Loop frames in foreground
        int n2=1;
        for (int n=fg_start; n<fg_end; n++) {
            // First copy the foreground
            output.getStack().getProcessor(n2).copyBits(input.getProcessor(n),0,0,Blitter.COPY);
            // Now divide out the background
            output.getStack().getProcessor(n2).copyBits(bkgnd.getStack().getProcessor(1),0,0,Blitter.DIVIDE);
            
            // these pixel operations will slow things down a fair bit, so only do them if required.
            if (invert_output || clip_output) {
                p = (float[])output.getStack().getProcessor(n2).getPixels();
                if (invert_output) {
                    for (int m=0; m<p.length; m++) p[m] = one - p[m];
                }
                if (clip_output) {
                    for (int m=0; m<p.length; m++) {
                        if (p[m] > out_max) p[m]=out_max;
                        if (p[m] < out_min) p[m]=out_min;
                    }
                }
                output.getStack().getProcessor(n2).setPixels(p);
            }
            
            IJ.showProgress(n,fg_end-fg_start+1);
            n2+=1;
        }
            
        
        // Draw the newly created windows
        output.show();
        output.updateAndDraw();
        
        
        return;
	}
 
    // Dialog to allow selection of options. ////////////////////////////////////////////////////////////
    boolean optionsDialog() {
        GenericDialog window = new GenericDialog("Background_Divider");
        window.addMessage("Dr Daniel Duke, LTRAC, Monash Uni");
        window.addMessage(versionString);
        window.addNumericField("Background start frame #",bkgnd_start,0);
        window.addNumericField("Background end frame #",bkgnd_end,0);
        window.addNumericField("Foreground start frame #",fg_start,0);
        window.addNumericField("Foreground end frame #",fg_end,0);
        window.addCheckbox("Invert output",invert_output);
        window.addCheckbox("Clip output intensity",clip_output);
        window.addNumericField("Output minimum intensity",out_min,2);
        window.addNumericField("Output maximum intensity",out_max,2);
        window.addMessage("Put '-1' to use the last frame. Frame numbers must be >= 1.");
        window.showDialog();
        if (window.wasCanceled()) return false;
        invert_output = window.getNextBoolean();
        clip_output = window.getNextBoolean();
        bkgnd_start = (int)window.getNextNumber();
        bkgnd_end = (int)window.getNextNumber();
        fg_start = (int)window.getNextNumber();
        fg_end = (int)window.getNextNumber();
        out_min = (int)window.getNextNumber();
        out_max = (int)window.getNextNumber();
        return true;
    }
 
    void showAbout() {
        IJ.showMessage("About Background_Divider...",
                       "Takes the average of the first few images and divides all other stack images by that background. Converts data to float."
                      );
    }

}
