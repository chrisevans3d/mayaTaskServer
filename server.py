'''
mayaTaskServer
Christopher Evans, Oct 2016
@author = Chris Evans

This is a simple task server that allows you to batch tasks in multiple headless/background maya instances.
I cannot think of any game project that doesn't need the ability to batch large sets of data to export and validate.
I hope this is useful and that people feel free to add to it in meaningful ways.

This was created in 'Epic Friday' time when Epic Games encourages us to work on whatever we are excited about.

'''

import tempfile
import os
import subprocess
import threading
import multiprocessing as mp
import socket
import sys
import datetime
import time
from cStringIO import StringIO

from PySide import QtGui, QtCore

import serverUtils

selfDirectory = os.path.dirname(__file__)
uiFile = selfDirectory + '/server.ui'
if os.path.isfile(uiFile):
    form_class, base_class = serverUtils.loadUiType(uiFile)
else:
    print('Cannot find UI file: ' + uiFile)


def show():
    global mayaTaskServerWindow
    try:
        mayaTaskServerWindow.close()
    except:
        pass

        mayaTaskServerWindow = mayaTaskServer()
        mayaTaskServerWindow.show()
    return mayaTaskServerWindow


## TASK SERVER
####################################################################
class MayaTaskServer(base_class, form_class):
    refreshSignal = QtCore.Signal()

    def __init__(self):
        super(MayaTaskServer, self).__init__()

        self.setupUi(self)

        self.mainJobServer = None

        self.start = time.time()

        self.refreshSignal.connect(self.refreshUI)
        self.startLocalCoresBTN.clicked.connect(self.startLocalCoresFn)
        self.killLocalCoresBTN.clicked.connect(self.killLocalCoresFn)
        self.jobTree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.jobTree.customContextMenuRequested.connect(self.openMenu)

        self.startJobServer(6006)

        # set the default temp folder
        filepath = os.path.realpath(__file__)
        self.localTempFolderEDT.setText(filepath.replace(filepath.split('\\')[-1], ''))

        #color tabs
        self.bottomTabs.setAutoFillBackground(True)
        palette = self.bottomTabs.palette()
        palette.setColor(self.bottomTabs.backgroundRole(), QtCore.Qt.darkGray)
        self.bottomTabs.setPalette(palette)

        self.bottomTabs.setStyleSheet('QTabBar::tab {background-color: darkGray;}')
        self.bottomTabs.setStyleSheet('QTabBar::tab {color: gray;}')

        #maya and fbx versions

        self.fbxVersionLBL.setText('  FbxVer: 2016.1.2')
        self.mayaVersionLBL.setText('MayaVer: 2016 SP5')

    ## START SERRVER
    def startJobServer(self, port):
        self.mainJobServer = JobServer(port)
        self.mainJobServer.start()

    ## USER INTERFACE
    ####################################################################

    def startLocalCoresFn(self):
        self.mainJobServer.bootUpLocalWorkers(self.coresSPIN.value())
        self.refreshUI()

    def killLocalCoresFn(self):
        # kill the MP pool
        print 'Terminating local MAYAPY workers.'
        if self.mainJobServer:
            self.mainJobServer.mpPool.close()
            self.mainJobServer.mpPool.terminate()

    def closeEvent(self, e):
        print 'Terminating local MAYAPY workers.'
        # kill the MP pool
        if self.mainJobServer:
            self.mainJobServer.mpPool.close()
            self.mainJobServer.mpPool.terminate()

    def refreshUI(self):
        self.refreshJobTree()
        self.refreshQueueTree()

        uptime = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.start))
        timeWorked = 0
        for worker in self.mainJobServer.workerDict:
            timeWorked += self.mainJobServer.workerDict[worker].timeWorked
        self.serverInfoLBL.setText('SERVER INFO: uptime: ' + uptime + ' total CPU time: ' + time.strftime("%H:%M:%S", time.gmtime(timeWorked)))

    def refreshJobTree(self):
        self.jobTree.clear()
        # build jobTree
        wid1 = QtGui.QTreeWidgetItem()
        wid1.setText(0, 'LOCAL WORKERS')
        self.jobTree.addTopLevelItem(wid1)
        font = wid1.font(0)
        font.setWeight(QtGui.QFont.Bold)
        font.setPointSize(12)
        wid1.setFont(0, font)
        wid1.setFont(1, font)
        wid1.setFont(2, font)

        if self.mainJobServer.workerDict.keys():
            for worker in self.mainJobServer.workerDict.keys():
                worker = self.mainJobServer.workerDict[worker]

                wid2 = QtGui.QTreeWidgetItem()
                wid1.addChild(wid2)

                # attach the actual worker
                wid2.worker = worker

                wNum = 'MAYAPY WORKER CORE #' + str(worker.cpuID)
                wid2.setText(0, wNum)
                if worker.task:
                    wNum = worker.timeStartString + ' MAYAPY WORKER CORE #' + str(worker.cpuID)

                    wid2.setText(0, wNum)

                    wid2.setText(1, worker.task['description'])
                    wid2.setText(2, worker.task['mayaFile'].split('\\')[-1])
                    green = QtGui.QColor(140, 200, 150, 255)
                    wid2.setForeground(0, green)
                    wid2.setForeground(1, green)
                    wid2.setForeground(2, green)
                    wid2.setText(4, worker.task['user'])
                else:
                    wid2.setText(1, '<None>')
                wid2.setText(3, 'LOCALHOST')

                font = wid2.font(0)
                font.setWeight(QtGui.QFont.Bold)
                font.setPointSize(10)
                wid2.setFont(0, font)
                wid2.setFont(1, font)

                #how many jobs completed?
                wid2.setText(4, str(len(worker.taskHistory)))

                #how many seconds worked?
                wid2.setText(5, str(len(worker.taskHistory)))
                wid2.setText(6, time.strftime("%H:%M:%S", time.gmtime(worker.timeWorked)))

        else:
            wid2 = QtGui.QTreeWidgetItem()
            wid3 = QtGui.QTreeWidgetItem()
            wid1.addChild(wid2)
            widNet.addChild(wid3)
            wid2.setText(0, 'No MAYAPY cores found.')
            wid3.setText(0, 'No MAYAPY network services found.')
            font = wid2.font(0)
            font.setWeight(QtGui.QFont.Bold)
            font.setPointSize(10)
            wid2.setFont(0, font)
            wid3.setFont(0, font)

        self.jobTree.expandAll()
        self.jobTree.header().resizeSections(QtGui.QHeaderView.ResizeToContents)

    def refreshQueueTree(self):
        self.queTree.clear()
        if self.mainJobServer.q:
            for task in self.mainJobServer.q:
                wid = QtGui.QTreeWidgetItem()
                wid.setText(0, task['user'])
                wid.setText(1, task['description'] + ' - ' + task['mayaFile'])
                self.queTree.addTopLevelItem(wid)
            self.queTree.header().resizeSections(QtGui.QHeaderView.ResizeToContents)
        self.bottomTabs.setTabText(0, 'JOB QUEUE [' + str(len(self.mainJobServer.q)) + ']')

    def openMenu(self, position):
        menu = QtGui.QMenu()
        revoke = menu.addAction('Kill worker')
        action = menu.exec_(self.jobTree.mapToGlobal(position))
        if action == revoke:
            item = self.jobTree.itemAt(position)
            print item


    def createWorkerTab(self, worker):
        new_tab = QtGui.QWidget(self.bottomTabs)
        new_tab.tabNum = worker.cpuID

        self.bottomTabs.addTab(new_tab, 'Worker' + str(worker.cpuID))
        new_tab.setAutoFillBackground(True)
        palette = new_tab.palette()
        palette.setColor(new_tab.backgroundRole(), QtCore.Qt.darkGray)
        new_tab.setPalette(palette)

        new_tab.outputText = QtGui.QTextEdit()
        verticalLayout = QtGui.QVBoxLayout()
        verticalLayout.addWidget(new_tab.outputText)
        new_tab.outputText.setText('Initialized logging for Worker' + str(worker.cpuID))
        new_tab.setLayout(verticalLayout)

        return new_tab

## WORKER CLASS
####################################################################
class MayaWorker(object):
    def __init__(self, host, port, cpuID):
        self.host = host
        self.port = port
        self.location = None
        self.cpuID = cpuID

        self.location = self.host

        self.timeStartString = None
        self.timeEndString = None

        self.timeStart = None

        self.timeWorked = 0

        self.busy = False
        self.task = None
        self.taskHistory = []

        self.log = ''
        self.process = None
        self.output = None

        #create worker tab
        self.workerTab = win.createWorkerTab(self)

    def startTask(self):
        #time
        now = datetime.datetime.now()
        self.timeStartString = now.strftime("%H:%M")
        self.timeStart = time.time()

        if self.task:
            outputText = 'WORKER #' + str(self.cpuID) + ': Starting task - ' + self.task['description'] + ' - ' + self.task['mayaFile']
            self.workerTab.outputText.append(str(outputText))
            self.busy = True
            win.refreshSignal.emit()
            log = self.task['description'] + '_' + self.task['mayaFile'].split('\\')[-1].split('.')[0]
            #self.task['log'] = log
            self.process = win.mainJobServer.mpPool.apply_async(serverUtils.spawnMaya, (self.task), callback=self.taskComplete)

    def taskComplete(self, arg):
        # updating the task history with the completed task
        self.taskHistory.append(self.task)

        elapsed = time.time() - self.timeStart
        self.timeWorked += elapsed
        outputText = 'WORKER #' + str(self.cpuID) + ': completed task - ' + self.task['description'] + ' in ' + str(elapsed) + ' seconds.'

        self.workerTab.outputText.append(outputText)

        # checking if there is a task to take from the queue
        if len(win.mainJobServer.q) > 0:
            print 'SERVER: Pulling task from queue [size', str(len(win.mainJobServer.q)), ']: ', self.task['description'], '-', self.task['mayaFile']
            self.task = win.mainJobServer.q[0]
            win.mainJobServer.q.pop(0)
            self.startTask()
        else:
            self.busy = False
            self.task = None
            print 'SERVER: Queue empty WORKER #' + str(self.cpuID) + ' sleeping.'
        win.refreshSignal.emit()


## JOB LISTENER / SERVER
####################################################################
class JobServer(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', port))
        self.server_socket.listen(5)

        self.workerDict = {}

        self.port = port
        self.running = True
        self.q = []

    def bootUpLocalWorkers(self, numProcs):
        self.mpPool = mp.Pool(processes=numProcs)
        for i in range(0, numProcs):
            mw = MayaWorker('localhost', 6006, i)
            self.workerDict['CPU_' + str(i)] = mw

    def findLocalWorker(self):
        if self.workerDict:
            for worker in self.workerDict.keys():
                if self.workerDict[worker].busy == False:
                    return self.workerDict[worker]
            else:
                return False
        else:
            print 'No workerDict!'
            return False

    def run(self, debug=1):
        print 'Starting Task Server @' + socket.gethostbyname(socket.gethostname()) + ':' + str(self.port)
        while self.running:
            client_socket, address = self.server_socket.accept()
            ip = str(address[0])
            data = client_socket.recv(512)
            if 'runTask' in data:
                worker = self.findLocalWorker()
                taskDict = eval(data.split(' >> ')[-1])
                if worker:
                    print 'SERVER>> Received task:', str(taskDict)
                    worker.task = taskDict
                    worker.startTask()
                else:
                    print 'SERVER: failed to find a worker, sending to queue. [' + taskDict['description'] + '] QUE:[' + str(len(self.q)) + ']'
                    self.q.append(taskDict)
                    win.refreshSignal.emit()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    win = MayaTaskServer()
    win.show()
    sys.exit(app.exec_())
