import os, sys
import tkinter as tkinter
import threading

import gi
#gi.require_version('Gst', '1.0')
#gi.require_version('GstVideo', '1.0')
#gi.require_version('GdkX11', '3.0')
from gi.repository import Gst, GObject, GdkX11, GstVideo

def set_frame_handle(bus, message, frame_id):
    if not message.get_structure() is None:
        print(message.get_structure().get_name())
        if message.get_structure().get_name() == 'prepare-window-handle':
            display_frame = message.src
            display_frame.set_property('force-aspect-ratio', True)
            display_frame.set_window_handle(frame_id)

window = tkinter.Tk()
window.title('')
window.geometry('500x400')

GObject.threads_init()
Gst.init(None)

display_frame = tkinter.Canvas(window, bg='#030')
display_frame.pack(side=tkinter.TOP,expand=tkinter.YES,fill=tkinter.BOTH)
frame_id = display_frame.winfo_id()

player = Gst.ElementFactory.make('playbin', None)

filepath = os.path.realpath('advert.mp4')
filepath2 = "file:///" + filepath.replace('\\', '/').replace(':', '|')
player.set_property('uri', filepath2)

bus = player.get_bus()
bus.enable_sync_message_emission()
bus.connect('sync-message::element', set_frame_handle, frame_id)

player.set_state(Gst.State.PLAYING)

window.mainloop()
