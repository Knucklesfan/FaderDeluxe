from tkinter import *
from tkinter import filedialog
from tkinter import ttk

import numpy as np
import subprocess
from PIL import Image, ImageTk
import ffmpeg
import io
import math

def difference_fade(pixela, pixelb, t, dur):
    if dur > 0.5:
        r = abs(pixela[0]-pixelb[0])*(t) + pixelb[0]*(1-t)
        g = abs(pixela[1]-pixelb[1])*(t) + pixelb[1]*(1-t)
        b = abs(pixela[2]-pixelb[2])*(t) + pixelb[2]*(1-t)
    else:
        r = abs(pixela[0]-pixelb[0])*(t) + pixela[0]*(1-t)
        g = abs(pixela[1]-pixelb[1])*(t) + pixela[1]*(1-t)
        b = abs(pixela[2]-pixelb[2])*(t) + pixela[2]*(1-t)

    return (int(r),int(g),int(b))

def inverse_difference_fade(pixela, pixelb, t, dur):
    if dur > 0.5:
        r = abs(pixelb[0]-pixela[0])*(t) + pixelb[0]*(1-t)
        g = abs(pixelb[1]-pixela[1])*(t) + pixelb[1]*(1-t)
        b = abs(pixelb[2]-pixela[2])*(t) + pixelb[2]*(1-t)
    else:
        r = abs(pixelb[0]-pixela[0])*(t) + pixela[0]*(1-t)
        g = abs(pixelb[1]-pixela[1])*(t) + pixela[1]*(1-t)
        b = abs(pixelb[2]-pixela[2])*(t) + pixela[2]*(1-t)

    return (int(r),int(g),int(b))

def addition_fade(pixela, pixelb, t, dur):
    if dur > 0.5:
        r = abs(pixela[0]+pixelb[0])*(t) + pixelb[0]*(1-t)
        g = abs(pixela[1]+pixelb[1])*(t) + pixelb[1]*(1-t)
        b = abs(pixela[2]+pixelb[2])*(t) + pixelb[2]*(1-t)
    else:
        r = abs(pixela[0]+pixelb[0])*(t) + pixela[0]*(1-t)
        g = abs(pixela[1]+pixelb[1])*(t) + pixela[1]*(1-t)
        b = abs(pixela[2]+pixelb[2])*(t) + pixela[2]*(1-t)

    return (int(r),int(g),int(b))
def mix(x,y,a):
    return x*(1-a)+y*a
def basic_mix(pixela, pixelb, t, dur):
    r = mix(pixela[0],pixelb[0],dur)
    g = mix(pixela[1],pixelb[1],dur)
    b = mix(pixela[2],pixelb[2],dur)

    return (int(r),int(g),int(b))

fades = { # this is the actual "pointers" to the fades (python doesnt actually have pointers tho, so they're more like references)
    'Difference': difference_fade,
    'Inverse Difference': inverse_difference_fade,
    'Addition': addition_fade,
    'Mix': basic_mix
}
fade_text = ["Difference", "Inverse Difference", "Addition", "Mix"] # this is the text used for the UI

window = Tk()

leftimage = Image.new("RGB", (480,270))
leftph = ImageTk.PhotoImage(leftimage)
rightimage = Image.new("RGB", (480,270))
rightph = ImageTk.PhotoImage(rightimage)
overlayPath = "";
underlayPath = "";
overlayFramecount = 0;
underlayFramecount = 0;
framerate = 0;


window.title("Fader Deluxe")


# Combobox
cb = ttk.Combobox(window, values=fade_text)
cb.set("Fade Method")
cb.grid(column=1, row=2)

leftimage_label = Label(window, image=leftph)
leftimage_label.grid(column=0, row=2)

rightimage_label = Label(window, image=rightph)
rightimage_label.grid(column=2, row=2)


def loadOverlay(path,framenum, noscale=False):
    out, err = (
        ffmpeg
        .input(path)
        .filter("select","eq(n,"+str(framenum)+")")
        .output('pipe:', format='image2', vframes=1)
        .run(capture_stdout=True, capture_stderr=True)
    )

    global rightimage
    rightimage = Image.open(io.BytesIO(out))
    if(not noscale): # this is stupid syntax, python!!!
        rightimage = rightimage.resize((rightimage.width//4, rightimage.height//4), Image.Resampling.LANCZOS)
        overlayPath = path
        rightph = ImageTk.PhotoImage(rightimage)
        rightimage_label.configure(image=rightph)
        rightimage_label.image = rightph

def loadUnderlay(path,framenum, noscale=False):
    out, err = (
        ffmpeg
        .input(path)
        .filter("select","eq(n,"+str(framenum)+")")
        .output('pipe:', format='image2', vframes=1)
        .run(capture_stdout=True, capture_stderr=True)
    )

    global leftimage
    leftimage = Image.open(io.BytesIO(out))
    if(not noscale): # this is stupid syntax, python!!!
        leftimage = leftimage.resize((leftimage.width//4, leftimage.height//4), Image.Resampling.LANCZOS)
        underlayPath = path
        leftph = ImageTk.PhotoImage(leftimage)
        leftimage_label.configure(image=leftph)
        leftimage_label.image = leftph

def underlayFrame():
    loadUnderlay(underlayPath, underlayspinbox.get())
def overlayFrame():
    loadOverlay(overlayPath, overlayspinbox.get())


underlayspinbox = Spinbox(window, from_=0, to=100, width=10, relief="sunken", repeatdelay=500, repeatinterval=20,command=underlayFrame)
underlayspinbox.grid(column=0, row=3)
overlayspinbox = Spinbox(window, from_=0, to=100, width=10, relief="sunken", repeatdelay=500, repeatinterval=20,command=overlayFrame)
overlayspinbox.grid(column=2, row=3)
durationspinbox = Spinbox(window, from_=0, to=100, width=10, relief="sunken", repeatdelay=500, repeatinterval=20,command=overlayFrame)
durationspinbox.grid(column=1, row=3)

lbl = Label(window, text="Underlay Start")
lbl.grid(column=0, row=4)
lbl = Label(window, text="Duration")
lbl.grid(column=1, row=4)
lbl = Label(window, text="Overlay End")
lbl.grid(column=2, row=4)

def loadFrameCnt(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            "-show_entries",
            "stream=r_frame_rate",
            path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    result_string = result.stdout.decode('utf-8').split()[0].split('/')
    global framerate
    framerate = float(result_string[0])/float(result_string[1])
    print(framerate)
    return int(result_string[1])

def underlayOpen():
    filename = filedialog.askopenfilename()
    underlayFramecount = loadFrameCnt(filename)
    loadUnderlay(filename, 0)
    underlayspinbox.configure(to=underlayFramecount-1)
    underlayspinbox.to = underlayFramecount-1
    global underlayPath
    underlayPath = filename

def overlayOpen():
    filename = filedialog.askopenfilename()
    overlayFramecount = loadFrameCnt(filename)
    loadOverlay(filename, 0)
    overlayspinbox.configure(to=overlayFramecount-1)
    overlayspinbox.to = overlayFramecount-1
    global overlayPath
    overlayPath = filename

openoverlay = Button(window, text="Open Overlay Video", command=overlayOpen)
openoverlay.grid(column=2, row=1)
openunderlay = Button(window, text="Open Underlay Video", command=underlayOpen)

openunderlay.grid(column=0, row=1)

progress_var = DoubleVar()
pb = ttk.Progressbar(
    window,
    orient='horizontal',
    mode='determinate',
    length=280,
    variable = progress_var,
    maximum=100
)

pb.grid(column=1, row=5)

def renderVideo():
    pb.configure(value=0)
    progress_var.set(0)
    window.update_idletasks()

    startFrame = int(underlayspinbox.get())
    endFrame = int(overlayspinbox.get())
    duration = int(durationspinbox.get())
    method = fades[cb.get()]
    for i in range(0,duration+1):
        loadUnderlay(underlayPath,startFrame+i,True)
        loadOverlay(overlayPath,endFrame-(duration//2)+i,True)
        underlayLoaded = leftimage.load()
        overlayLoaded = rightimage.load()
        combinedimage = Image.new("RGB", (leftimage.width,leftimage.height))
        combineload = combinedimage.load();
        t = math.sin((i/duration)*math.pi)

        for x in range(0,leftimage.width):
            for y in range(0,leftimage.height):
                combineload[x,y] = method(underlayLoaded[x,y],overlayLoaded[x,y],t,i/duration)

        combinedimage.save("./temp/frames"+str(i)+".png")
        print((i/(duration+1))*100)
        pb.configure(value=(i/(duration+1))*100)
        progress_var.set((i/(duration+1))*100)
        window.update_idletasks()
    result = subprocess.run(
    [
        'ffmpeg','-y','-framerate',str(framerate),'-i','./temp/frames%d.png','-r','30', "output.mp4",
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    )

    pb.configure(value=100)
    progress_var.set(100)
    window.update_idletasks()


openunderlay = Button(window, text="RENDER!", command=renderVideo)

openunderlay.grid(column=1, row=6)

window.mainloop()
