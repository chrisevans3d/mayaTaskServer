'''
serverTasks
Christopher Evans, Oct 2016
@author = Chris Evans

The purpose of this file is to wrap arbitrary tasks (from the 'tasks' lib) in a 'jobDict' and send them to the task server.

This was created in 'Epic Friday' time when Epic Games encourages us to work on whatever we are excited about.

'''

import maya.mel as mel
import maya.cmds as cmds
import socket, os, tempfile


# -------------------------------------------------------
# For running anythign we give it.
def runScript(filePath, script, description=None, mayaPyPath=None, sysPathAppend=None, CPU=None, debug=1, server='localhost', ignoreVersion=False):

	runMe = '''
tStart = cmds.playbackOptions(animationStartTime=1, q=1)
tEnd = cmds.playbackOptions(animationEndTime=1, q=1)

cmds.file({0!r}, o=1, f=1, iv={2!r})


print {0!r}, 'loaded.'
print {1!r}
cmds.quit()
	'''.format(filePath, script, ignoreVersion)

	if debug: print runMe

	f, fPath = tempfile.mkstemp()
	os.write(f, runMe)
	if debug: print 'Temp script file written to:', fPath

	if not description:
		description = 'runScript'

	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client_socket.connect((server, 6006))
	jobDict = {'user':os.environ.get("USERNAME"), 'mayaFile':filePath, 'pyFile':fPath,'mayapy':mayaPyPath, 'description':description}
	client_socket.send('runTask >> ' + str(jobDict))
	client_socket.close()

# -------------------------------------------------------
# Specific to ARTv1 FBX Anim Export
def fbxAnimExport(filePath, exportPath=None, mayaPyPath=None, description=None, sysPathAppend=None, CPU=None, debug=1, server='localhost', ignoreVersion=False):

    runMe = '''
from epic.internal.mayaTaskServer import tasks

#load the maya file
cmds.file({0!r}, o=1, f=1, iv={2!r})
print {0!r}, 'loaded.'
uNode = tasks.getExportNodes()[0]
if uNode:
    tasks.fbxAnimExport(uNode, exportPath={1!r})

cmds.quit()
        '''.format(filePath, exportPath, ignoreVersion)

    if debug: print runMe

    f, fPath = tempfile.mkstemp()
    os.write(f, runMe)
    if debug: print 'Temp script file written to:', fPath

    if not description:
        description = 'fbxAnimExport'

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server, 6006))
    jobDict = {'user': os.environ.get("USERNAME"), 'mayaFile': filePath, 'pyFile': fPath, 'mayapy': mayaPyPath, 'description': description}
    client_socket.send('runTask >> ' + str(jobDict))
    client_socket.close()
