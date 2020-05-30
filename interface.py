import concurrent.futures
import os
import threading
import time
from io import BytesIO
from urllib.parse import urlparse

import requests
import wx
import humanize

class DownloadThread(threading.Thread):
    def __init__(self, start, end, url, target, *args, chunk_size=1024 * 8, **kwargs):
        super().__init__(*args, **kwargs)
        self.prog = 0
        self._start = start
        self._end = end
        self._url = url
        self._target = target
        self._chunk_size = chunk_size
        self._kill = False
    
    def kill(self):
        self._kill = True

    def run(self):
        headers = {
            "Range": "bytes={}-{}".format(self._start, self._end)
        }
        
        result = requests.get(self._url, headers=headers, stream=True)
        perc_per_chunk = self._chunk_size / (self._end - self._start) * 100
        c = 0
        with open(self._target, "r+b") as fp:
            fp.seek(self._start)
            res = BytesIO()
            for chunk in result.iter_content(chunk_size=self._chunk_size):
                if self._kill:
                    break
                res.write(chunk)
                c += 1
                if c % 100 == 0:
                    self.prog += perc_per_chunk * 100
                    fp.write(res.getvalue())
                    res = BytesIO()
            
            fp.write(res.getvalue())
            self.prog = 100

def create_empty(target, size):
    with open(target, "wb") as fp:
        fp.seek(size - 1)
        fp.write(b'\0')

def get_info(url):
    size = int(requests.head(url).headers['content-length'])
    target = os.path.basename(urlparse(url).path)

    return size, target

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, title=title)

        self.panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # URL
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        st1 = wx.StaticText(self.panel, label="URL to download")
        hbox1.Add(st1, flag=wx.RIGHT, border=8)
        self.url = wx.TextCtrl(self.panel)
        hbox1.Add(self.url, proportion=1)
        
        vbox.Add(hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        vbox.Add((-1, 10))

        # PATH
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        st2 = wx.StaticText(self.panel, label="Destination folder")
        hbox2.Add(st2, flag=wx.RIGHT, border=8)
        self.destination = wx.DirPickerCtrl(self.panel)
        hbox2.Add(self.destination, proportion=1)
        vbox.Add(hbox2, flag=wx.LEFT | wx.TOP, border=10)
        vbox.Add((-1, 10))

        # NUMBER OF THREADS
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        st3 = wx.StaticText(self.panel, label="Number of threads")
        hbox3.Add(st3, flag=wx.RIGHT, border=8)
        self.threads = wx.SpinCtrl(self.panel)
        self.threads.SetMin(1)
        hbox3.Add(self.threads, proportion=1)
        vbox.Add(hbox3, flag=wx.LEFT | wx.TOP, border=10)
        vbox.Add((-1, 10))

        # BUTTON
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        btn1 = wx.Button(self.panel, label='Download', size=(70, 30))
        btn1.Bind(wx.EVT_BUTTON, self.OnClicked)
        hbox4.Add(btn1)
        vbox.Add(hbox4, flag=wx.ALIGN_RIGHT|wx.RIGHT, border=10)

        self.panel.SetSizer(vbox)
        self.Show()

    def OnClicked(self, event):
        progress = wx.ProgressDialog("Download", "Collecting required information", maximum=100, style=wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT)
        try:
            size, filename = get_info(self.url.GetValue())
        except:
            wx.MessageBox(message="Information about the download could not be found (does it exist?)", style=wx.OK | wx.ICON_ERROR)
            progress.Destroy()
        else:
            range_size = size // self.threads.GetValue()
            
            target = os.path.join(self.destination.GetPath(), filename)
            progress.Pulse("Creating empty file...")
            if progress.WasCancelled():
                progress.Destroy()
                return

            i = 0
            try:
                name, ext = filename.rsplit(".", 1)
            except:
                wx.MessageBox(message="No filename could be found for this download", style=wx.OK | wx.ICON_ERROR)
                progress.Destroy()
                return
            
            changed = False
            while os.path.exists(target):
                # Don't overwrite
                i += 1
                target = os.path.join(self.destination.GetPath(), "{} ({}).{}".format(name, i, ext))
                changed = True
            
            if changed:
                message = wx.MessageBox(message="The file {0}.{1} already exists. Your download will be saved to {0} ({2}).{1}".format(
                    name, ext, i
                ))

            create_empty(target, size)
            
            progress.Pulse("Downloading...")
            if progress.WasCancelled():
                progress.Destroy()
                return

            threads = []
            for t in range(self.threads.GetValue()):
                thread = DownloadThread(t * range_size, (t + 1) * range_size, self.url.GetValue(), target)
                thread.setDaemon(True)
                thread.start()
                threads.append(thread)

            progs = [thread.prog for thread in threads]
            while any(map(lambda p: p != 100, progs)):
                progs = [thread.prog for thread in threads]
                prog = sum(progs)/self.threads.GetValue()
                progress.Update(prog, "Downloading ({} of {})...".format(
                    humanize.naturalsize(prog / 100 * size),
                    humanize.naturalsize(size)
                ))

                if progress.WasCancelled():
                    progress.Update(0, "Cancelling download...")
                    for thread in threads:
                        thread.kill()
                        thread.join()
                    
                    progress.Destroy()
                    return

            progress.Update(100, "Downloaded!")
            progress.Destroy()

app = wx.App(False)
frame = MyFrame(None, "Quick download")
app.MainLoop()
