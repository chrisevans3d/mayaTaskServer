'''
serverTasks
Christopher Evans, Oct 2016
@author = Chris Evans

This is a package of TASKS that can be run by any tool anywhere and are not task server dependent.

This was created in 'Epic Friday' time when Epic Games encourages us to work on whatever we are excited about.
'''

import maya.mel as mel
import maya.cmds as cmds
import socket, os

from epic.rigging import uExport as ue

from Modules.facial import face

def logToDisk():
    pass

# -------------------------------------------------------
# This is the function that exports FBX Animations for ARTv1.
def fbxAnimExport(uExportNode, exportPath=None, bakeRoot=False, mayaPyPath=None, sysPathAppend=None, CPU=None, logPath=None, debug=1):

    uNode = ue.uExport(uExportNode)

    if not exportPath:
        #make it from the maya file next time
        return

    exportPath = exportPath.replace('\\','/')

    tStart = cmds.playbackOptions(animationStartTime=1, q=1)
    tEnd = cmds.playbackOptions(animationEndTime=1, q=1)

    cmds.loadPlugin("fbxmaya.mll")
    setExportFlags(rot='Quat', upAxis='z', animStart=tStart, animEnd=tEnd)

    #find what to export
    toExport = []
    toExport.extend(cmds.listRelatives(uNode.export_root, type='joint', allDescendents=True, f=1))

    unhideSkeleton(uNode)

    #find anim export settings
    settingsDicts = getExportAnimationSettings()

    if settingsDicts:
        if debug:
            print settingsDicts
        for d in settingsDicts:
            # setup export
            cmds.select(toExport)
            #TODO: fps?
            #TODO: Morphs?
            cmds.playbackOptions(min = d['start'], animationStartTime = d['start'])
            cmds.playbackOptions(max = d['end'], animationEndTime = d['end'])
            setExportFlags(animStart=d['start'], animEnd=d['end'])
            new_fpath = exportPath + d['fbx_path'].split('/')[-1]

            # Export!
            print "FBXExport -f \"" + new_fpath + "\" -s"
            mel.eval("FBXExport -f \"" + new_fpath + "\" -s")

            # clear sel and export list
            cmds.select(d=1)
            #toExport = []
    else:
        print 'No settings Dict'

# -------------------------------------------------------
## HELPER FUNCTIONS
###################################################################

def setExportFlags(rot='Quat', upAxis='z', animStart=None, animEnd=None):
    # Mesh
    mel.eval("FBXExportSmoothingGroups -v true")
    mel.eval("FBXExportHardEdges -v false")
    mel.eval("FBXExportTangents -v false")
    mel.eval("FBXExportInstances -v false")
    mel.eval("FBXExportInAscii -v true")
    mel.eval("FBXExportSmoothMesh -v false")

    # Animation
    mel.eval("FBXExportBakeComplexAnimation -v true")
    mel.eval("FBXExportBakeComplexStart -v "+str(animStart))
    mel.eval("FBXExportBakeComplexEnd -v "+str(animEnd))

    mel.eval("FBXExportReferencedAssetsContent -v true")
    mel.eval("FBXExportBakeComplexStep -v 1")
    mel.eval("FBXExportUseSceneName -v false")

    #curves
    if rot == 'euler':
        mel.eval("FBXExportQuaternion -v euler")
    if rot == 'resample':
        mel.eval("FBXExportQuaternion -v resample")
    else:
        mel.eval("FBXExportQuaternion -v quaternion")

    mel.eval("FBXExportShapes -v true")
    mel.eval("FBXExportSkins -v true")


    if upAxis == 'y':
        mel.eval("FBXExportUpAxis y")
    else:
        mel.eval("FBXExportUpAxis z")

    #garbage we don't want
    # Constraints
    mel.eval("FBXExportConstraints -v false")
    # Cameras
    mel.eval("FBXExportCameras -v false")
    # Lights
    mel.eval("FBXExportLights -v false")
    # Embed Media
    mel.eval("FBXExportEmbeddedTextures -v false")
    # Connections
    mel.eval("FBXExportInputConnections -v false")
    # Axis Conversion

# -------------------------------------------------------
def getExportAnimationSettings():
    '''
    Returns dict of info from the ExportAnimationSettings node
    '''
    exportSettingsDicts = []
    if cmds.objExists("ExportAnimationSettings"):
        sequeneces = cmds.listAttr("ExportAnimationSettings", string = "sequence*")
        for sequence in sequeneces:
            exportSettingsDict = {}
            # find data
            data = cmds.getAttr("ExportAnimationSettings.{0}".format(sequence))
            data_list = data.split("::")

            exportSettingsDict['fbx_path'] = data_list[0]
            exportSettingsDict['start'] = int(data_list[1])
            exportSettingsDict['end'] = int(data_list[2])
            exportSettingsDict['fps'] = data_list[3]

            exportSettingsDicts.append(exportSettingsDict)

        return exportSettingsDicts
    else:
        return False

# -------------------------------------------------------
def getExportNodes():
    return cmds.ls('*.uexport_ver', o=1, r=1)

def unhideSkeleton(uNode):
    for node in cmds.listRelatives(uNode.export_root, type='joint', allDescendents=True, f=1):
        cmds.showHidden(node)

