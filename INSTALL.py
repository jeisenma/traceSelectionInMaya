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
mc.shelfButton("createTrace", label="create trace", i1="traceCreate.png", command="import traceSelectTool as tst; tst = reload(tst); traceSelect = tst.main()")

## Trace Move Tool ##
if mc.toolButton("spMoveTool1",q=True,exists=True):
    # Remove UI objects
    mc.deleteUI("spMoveToolContext1")
    mc.deleteUI("spMoveTool1")

mc.loadPlugin("traceMoveTool.py", quiet=True)
mc.traceMoveToolContext("traceMoveToolContext")
mc.setToolTo("traceMoveToolContext")

shelfTopLevel = mm.eval("global string $gShelfTopLevel;$temp = $gShelfTopLevel")
mc.setParent("%s|MotionSelection" % shelfTopLevel)
mc.shelfButton("moveTrace", label="move trace", i1="traceMove.png", command="""mc.loadPlugin("traceMoveTool.py", quiet=True)
try:    # does tool exist?
    mc.toolHasOptions("traceMoveToolContext1")
except:
    mc.traceMoveToolContext("traceMoveToolContext1")
mc.setToolTo("traceMoveToolContext1")""")

