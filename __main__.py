from pathlib import Path
from threading import Thread

from .__init__ import (GET_FILES, MIDIVisualizer, 
    FluidSynth, AudioDubber, AVP, VideoEditor,
    ChapterGenerator)

from PySimpleGUI import (popup_yes_no,
    popup_get_text, popup_get_file)


def midi2piano_visualizer():
    colors = {1:"blue",2:"green",3:"red",4:"purple",5:"grey"}
    print(colors)
    color = colors[int(input("Color?: "))]

    files = GET_FILES([".midi",".mid"])
    notes = False

    threads = [MIDIVisualizer(f,notes,color) for f in files]
    for th in threads:
        th.start()

    while list(set(threads))[0] != True:
        for i, th in enumerate(threads):
            if type(th) != bool:
                if not th.is_alive():
                    th.join()
                    threads[i] = True

    threads = [FluidSynth("studio",f) for f in files]
    for th in threads:
        th.start()

    while list(set(threads))[0] != True:
        for i, th in enumerate(threads):
            if type(th) != bool:
                if not th.is_alive():
                    th.join()
                    threads[i] = True

    files = [f for f in files in f.suffix == ".wav"]
    threads = [AVP(f,color) for f in files]
    for th in threads:
        th.start()

    while list(set(threads))[0] != True:
        for i, th in enumerate(threads):
            if type(th) != bool:
                if not th.is_alive():
                    th.join()
                    threads[i] = True

    files = [f for f in files in f.suffix == ".mp4"]
    threads = list()
    names = [f.stem.split("_Pianoroll")[0] for f in files if "_Pianoroll" in f.stem]
    names = [f.stem.split("Pianoroll")[0] for f in files if "Pianoroll" in f.stem]
    for name in names:
        if not "Visualizer" in name:
            pianoroll = Path(files[0].parent, f"{name}Pianoroll.mp4")
            visualizer = Path(files[0].parent, f"{name}Visualizer.mp4")
            threads.append(VideoEditor(pianoroll,visualizer))
    for th in threads:
        th.start()

    while list(set(threads))[0] != True:
        for i, th in enumerate(threads):
            if type(th) != bool:
                if not th.is_alive():
                    th.join()
                    threads[i] = True
    

def midi2visualizer():
    colors = {1:"blue",2:"green",3:"red",4:"purple",5:"grey"}
    print(colors)
    color = colors[int(input("Color?: "))]

    files = GET_FILES(".mp4")
    threads = [FluidSynth("studio",f) for f in files]
    for th in threads:
        th.start()

    while list(set(threads))[0] != True:
        for i, th in enumerate(threads):
            if type(th) != bool:
                if not th.is_alive():
                    th.join()
                    threads[i] = True

    files = [f for f in files in f.suffix == ".wav"]
    threads = [AVP(f,color) for f in files]
    for th in threads:
        th.start()

    while list(set(threads))[0] != True:
        for i, th in enumerate(threads):
            if type(th) != bool:
                if not th.is_alive():
                    th.join()
                    threads[i] = True


def midi2dubbed_piano():
    colors = {1:"blue",2:"green",3:"red",4:"purple",5:"grey"}
    print(colors)
    color = colors[int(input("Color?: "))]

    files = GET_FILES([".midi",".mid"])
    notes = True

    if popup_yes_no("Include the peddle?") in ["Yes","yes"]:
        peddle = True
    else:
        peddle = False

    threads = [MIDIVisualizer(f,notes,color,peddle) for f in files]
    for th in threads:
        th.start()

    while list(set(threads))[0] != True:
        for i, th in enumerate(threads):
            if type(th) != bool:
                if not th.is_alive():
                    th.join()
                    threads[i] = True

    threads = [FluidSynth("grand",f) for f in files]
    for th in threads:
        th.start()

    while list(set(threads))[0] != True:
        for i, th in enumerate(threads):
            if type(th) != bool:
                if not th.is_alive():
                    th.join()
                    threads[i] = True

    videoPaths = [Path(f.parent,f"{f.stem}.mp4") for f in files]
    audioPaths = [Path(f.parent,f"{f.stem}.wav") for f in files]

    threads = list()
    for aP,vP in zip(audioPaths,videoPaths):
        ad = AudioDubber(aP,vP)
        threads.append(Thread(target=ad.dub))
    for th in threads:
        th.start()

    while list(set(threads))[0] != True:
        for i, th in enumerate(threads):
            if type(th) != bool:
                if not th.is_alive():
                    th.join()
                    threads[i] = True


def chord_progression2midi(progression):
    pass


def tranpose_midi():
    pass


if __name__ == "__main__":


    options = {
        1: "Midi to Piano + Visualizer",
        2: "Midi to Visualizer",
        3: "Midi to dubbed Piano",
        4: "Chord Progression to Midi",
        5: "Transpose Midi"}
    print(options)
    routes = {
        1: midi2piano_visualizer,
        2: midi2visualizer,
        3: midi2dubbed_piano,
        4: chord_progression2midi,
        5: tranpose_midi}[int(input("Selection?: "))]()