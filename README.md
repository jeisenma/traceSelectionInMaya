traceSelectionInMaya
====================

A set of Maya tools that enable the user to trace-select motion and then move the resulting trace to edit the motion.

Demo Video
----------
http://youtu.be/2pdZmbSkrtU

Installation Steps
-------------------
1. copy the icon images from "icons" (traceCreate.png and traceMove.png) to your "maya/VERSION/prefs/icons/" directory
2. copy all the python scripts from "scripts" to your maya/VERSION/scripts/ directory
3. copy the python scripted plug-in from "plug-ins" to your "maya/VERSION/plug-ins/" directory (make sure you set the "MAYA_PLUG_IN_PATH" environment variable!)
4. run Maya and create an empty shelf called "MotionSelection"
5. run the INSTALL.py script from Maya's Command Window


The Trace Create Tool
---------------------

This tool will create visualizations of motion trajectories for the end effectors and roots of each skeleton in your scene.  

If you want to choose which parts of your rig(s) get motion trajectories, you can select the parts you are interested in, and then Shift+RMB click on the shelf button to get the option of setting your own traceables.

Once the tool has been activated, you may trace the motion of any part of a trajectory vizualization to select that part of the motion.  A new curve will be created to show you what you selected.

Note: Selecting motion works best when playback is looping.

If you want to make a different selection on that same skeleton, simply select something else.  The new selection will replace the previous one (unless you hold down the Shift key).


The Trace Move Tool
-------------------

This is a mock-up created to demonstrate what direct-manipulation motion editing could be like.  After you have created a trace using the Trace Create Tool, you may use this tool to move that trace as a means of editing the original IK animation.  

Limitations:
 - This tool only works with IK handles.
 - It currently only works in an orthographic view (front, top, or side).
 - The motion editing process does not create new keyframes or edit keyframe tangents -- it only moves the keyframes that exist within the timespan defined by your trace selection.
 
 
