#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
runkeeper2endomondogui.py
Portions Copyright Conor O'Neill 2013, cwjoneill@gmail.com - See http://conoroneill.net
Portions Copyright Jan Bodnar 2011 - See http://zetcode.com/gui/pysidetutorial/dialogs/
Portions Copyright (c) 2012, Urban Skudnik <urban.skudnik@gmail.com> - See https://github.com/uskudnik/gpxjoin

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

import sys
from PySide import QtGui, QtCore
from BeautifulSoup import BeautifulStoneSoup
import datetime
import glob
import os.path
import platform

gpx_time_format = "%Y-%m-%dT%H:%M:%SZ"
sportstracker_time_format = "%Y-%m-%dT%H:%M:%S"

class Runkeeper2Endomondo(QtGui.QMainWindow):
    
    def __init__(self):
        super(Runkeeper2Endomondo, self).__init__()
        
        self.initUI()
        
    def initUI(self):      

        self.textEdit = QtGui.QTextEdit()
        self.setCentralWidget(self.textEdit)
        self.statusBar()

        openFile = QtGui.QAction(QtGui.QIcon('open.png'), 'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Select GPX Directory')
        openFile.triggered.connect(self.showDialog)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)       
        
        self.setGeometry(300, 300, 450, 300)
        self.setWindowTitle('RunKeeper to Endomondo Converter')
        message = "Use the File menu to select the directory to which you have unzipped all your RunKeeper GPX files.\n\nThis tool will concatenate all those files into a file called endomondo.gpx which you can then import into Endomondo.\n\nEndomondo has a 10MB limit on file uploads, if your workouts results in a larger file, they will automatically be split in serveral files.\n\nCopyright Conor O\'Neill, cwjoneill@gmail.com, 2013"
        self.textEdit.setText(message)
        self.textEdit.moveCursor(QtGui.QTextCursor.End)
        self.show()
        
    def showDialog(self):
        dialog = QtGui.QFileDialog(self, "Pick GPS Dir")
        dialog.setFileMode(QtGui.QFileDialog.Directory)
        dialog.setOption(QtGui.QFileDialog.ShowDirsOnly)
        fname = dialog.getExistingDirectory(self, 'Select Directory with RunKeeper GPX files', '.',)

        if fname:
            self.textEdit.setText(fname)
            self.textEdit.repaint()
            files = list()
            gpxpath = fname + '/*.gpx'
            if platform.system() == "Windows":
                gpxpath = fname + '\\*.gpx'
            all_gpx_files = glob.glob(gpxpath)
            # To make sure our data files are attached in correct order; we don't trust file system (download order, ...)
            message = "Processing files, please wait\n"
            self.textEdit.setText(message)
            self.textEdit.repaint()
            for ffile in all_gpx_files:
                if ("endomondo" not in ffile):
                    message = message + ffile + "\n"
                    self.textEdit.setText(message)
                    self.textEdit.moveCursor(QtGui.QTextCursor.End)
                    self.textEdit.ensureCursorVisible()
                    self.textEdit.repaint()
                    ffile = open(ffile, "r")
                    filecontent = ffile.read()
                    xml = BeautifulStoneSoup(filecontent)
                    tracktime = xml.find("trk")
                    try:
                        trkstart= tracktime.find("time").string
                    except AttributeError:
                        # Skip file if track is empty. i.e. manual added workout - no gps data
                        continue
                    try:
                        starttime = datetime.datetime.strptime(trkstart, gpx_time_format)
                    except ValueError:
                        # This deals with Sports Tracker files which have a silly time format
                        index = trkstart.find('.')
                        try:
                            timepart = trkstart[0:index-1]
                            starttime = datetime.datetime.strptime(timepart, sportstracker_time_format)
                        except ValueError:
                            # A user has submitted yet another Sports Tracker time format    
                            timepart = trkstart[0:index]
                            starttime = datetime.datetime.strptime(timepart, sportstracker_time_format)
                    files += [[starttime, filecontent]]
            
            ffiles = sorted(files, key=lambda *d: d[0]) 
            
            # GPX end tag is unnecessary from initial file
            joined_gpx = ffiles[0][1].split("</gpx>")[0]
            
            # "Header" data (initial xml tag, gpx tag, metadata, etc.) is unnecessary
            # in subsequent file, therefore we remove it, along with end GPX tag.
            fileno = 1
            for date, ffile in ffiles[1:]:
                header, content = ffile.split("<trk>")
                content = "<trk>" + content
                combined_length = len(content) + len(joined_gpx) + 20 # closing tags
                # Max endomondo length is 10MB, split files if larger
                if combined_length > 10000000:
                    joined_gpx += "</gpx>"
                    output_filename = "endomondo_{0:03d}.gpx".format(fileno)
                    output_gpx = file(output_filename, "w")
                    output_gpx.write(joined_gpx)
                    output_gpx.close()
                    fileno += 1
                    # Start new file with header
                    joined_gpx = header
                joined_gpx += content.split("</gpx>")[0]
            
            # Processed all files, append end GPX tag
            joined_gpx += "</gpx>"
            
            # Write out concatenated file
            output_filename = "endomondo_{0:03d}.gpx".format(fileno)
            output_gpx = file(output_filename, "w")
            output_gpx.write(joined_gpx)
            output_gpx.close()
            message = message + "\n\nAll Done!\nNow import endomondo001.gpx - " + "endomondo_{0:03d}.gpx".format(fileno) + " into Endomondo."
            self.textEdit.setText(message)
            self.textEdit.moveCursor(QtGui.QTextCursor.End)
            self.textEdit.ensureCursorVisible()
            self.textEdit.repaint()

        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = Runkeeper2Endomondo()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()