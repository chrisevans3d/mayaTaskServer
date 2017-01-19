mayaTaskServer
============

This is a simple multi-threaded task server that allows you to batch tasks in multiple headless/background maya instances.
I cannot think of any game project that doesn't need the ability to batch large sets of data to export and validate.
I hope this is useful and that people feel free to add to it in meaningful ways.

This was created in 'Epic Friday' time when Epic Games encourages us to work on whatever we are excited about and share knowledge with the community.

![alt tag](http://chrisevans3d.com/files/github/MayaTaskServer_github.gif)

Here's an example of sending a batch of tasks:

```python
from mayaTaskServer import serverTasks

animDir = 'D:\\Game\\Characters\\Heroes\\Femme\\Animation\\'
for f in os.listdir(animDir):
    if ".mb" in f:
        serverTasks.fbxAnimExport(animDir+f,exportPath='d:/FBX/femme/')
```

It currently only works on local host, pending code to xfer the maya file to the server to it can operate on it.