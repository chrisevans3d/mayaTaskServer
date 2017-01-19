'''
serverUtils
Christopher Evans, Oct 2016
@author = Chris Evans

This was meant to be a lib of utilities for the server, I should move more of the utils out of server.py and place them here.

This was created in 'Epic Friday' time when Epic Games encourages us to work on whatever we are excited about.

'''

import tempfile
import os
import subprocess
import sys
import socket
import multiprocessing as mp

from PySide import QtGui, QtCore
from cStringIO import StringIO
import xml.etree.ElementTree as xml
import pysideuic

# -------------------------------------------------------
def spawnMaya(task, args=None, stdout=False, stderr=True):
    runMe = '''import sys
sys.path.append(r"D:\Build\usr\jeremy_ernst\MayaTools\General\Scripts")
import maya.standalone
import maya.mel as mel
import maya.cmds as cmds
import epic.internal.mayaTaskServer

maya.standalone.initialize( name='python' )
cmds.upAxis(ax='z') # Sets the up axis to Z

'''

    f = open(task['pyFile'], "rb") # Python task file (this contains the code for the task)
    script = f.read()
    f.close()
    runMe += script

    f, fPath = tempfile.mkstemp()
    os.write(f, runMe)

    #set stdout
    sout = subprocess.STDOUT
    if not stdout:
        sout = subprocess.PIPE
    eout = subprocess.STDOUT
    if not stderr:
        eout = subprocess.PIPE

    #TODO: find maya version
    mayapy = 'C:\\Program Files\\Autodesk\\Maya2016\\bin\\mayapy.exe'
    #mayaTaskProc = subprocess.Popen(mayapy + ' -u ' + fPath, stdout=sout, stderr=eout)
    #TODO: Make windows stay open
    mayaTaskProc = subprocess.Popen(mayapy + ' -u ' + fPath)
    mayaTaskProc.wait()

    return


# -------------------------------------------------------
def sendFile(file, server, port):
    HOST = 'localhost'
    CPORT = 9091
    MPORT = 9090
    FILE = sys.argv[1]

    cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cs.connect((HOST, CPORT))
    cs.send("SEND " + file)
    cs.close()

    ms = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ms.connect((HOST, MPORT))

    f = open(FILE, "rb")
    data = f.read()
    f.close()

    ms.send(data)
    ms.close()

# -------------------------------------------------------
def loadUiType(uiFile):
    """
    Pyside lacks the "loadUiType" command, so we have to convert the ui file to py code in-memory first
    and then execute it in a special frame to retrieve the form_class.
    http://tech-artists.org/forum/showthread.php?3035-PySide-in-Maya-2013
    """
    parsed = xml.parse(uiFile)
    widget_class = parsed.find('widget').get('class')
    form_class = parsed.find('class').text

    with open(uiFile, 'r') as f:
        o = StringIO()
        frame = {}

        pysideuic.compileUi(f, o, indent=0)
        pyc = compile(o.getvalue(), '<string>', 'exec')
        exec pyc in frame

        #Fetch the base_class and form class based on their type in the xml from designer
        form_class = frame['Ui_%s'%form_class]
        base_class = eval('QtGui.%s'%widget_class)
    return form_class, base_class

if __name__ == "__main__":
    pool = mp.Pool()
    #ports = [6666661,6666662,6666663,6666664,6666665,6666666,6666667,6666668]
    ports = [6666667,6666668]
    for i in range(0, len(ports)):
        pool.apply_async(spawnMaya(ports[i]), args = (i))
