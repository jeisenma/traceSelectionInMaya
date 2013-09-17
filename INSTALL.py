##################
# Install Script #
##################

import maya.cmds as mc
import maya.mel as mm

## Trace Select Tool ##
if mc.shelfButton("createTrace",q=True,exists=True):
    # Remove UI object
    mc.deleteUI("createTrace")
shelfTopLevel = mm.eval("global string $gShelfTopLevel;$temp = $gShelfTopLevel")
mc.setParent("%s|MotionSelection" % shelfTopLevel)
mc.shelfButton("createTrace", label="create trace", i1="traceCreate.png", command="""
import traceSelectTool as tst
tst = reload(tst)
traceSelect = tst.main()""")
pm = mc.popupMenu( button=1, sh=True )
mc.menuItem( label="Use selected as traceables", command="""
import traceSelectTool as tst

tst = reload(tst)
traceSelect = tst.main(mc.ls(sl=True))
""", p=pm)

## Trace Move Tool ##
if mc.shelfButton("moveTrace",q=True,exists=True):
    # Remove UI objects
    mc.deleteUI("moveTrace")

shelfTopLevel = mm.eval("global string $gShelfTopLevel;$temp = $gShelfTopLevel")
mc.setParent("%s|MotionSelection" % shelfTopLevel)
mc.shelfButton("moveTrace", label="move trace", i1="traceMove.png", command="""mc.loadPlugin("traceMoveTool.py", quiet=True)
try:    # does tool exist?
    mc.toolHasOptions("traceMoveToolContext1")
except:
    mc.traceMoveToolContext("traceMoveToolContext1")
mc.setToolTo("traceMoveToolContext1")""")

