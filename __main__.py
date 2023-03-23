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
    wavfiles = [Path(f.parent,f"{f.stem}.wav") for f in files]
    wavfiles = [f for f in files if f.exists()]
    
    threads = [AVP(f,color) for f in wavfiles]
    for th in threads:
       th.start()

    while list(set(threads))[0] != True:
        for i, th in enumerate(threads):
            if type(th) != bool:
                if not th.is_alive():
                    th.join()
                    threads[i] = True

    threads = list()
    for midiPath in files:
        
        name = f"{midiPath.stem}_Pianoroll.mp4"
        pianoroll = Path(midiPath.parent, name)
        try:
            assert pianoroll.exists()
        except:
            print(f"Pianoroll does not exist for {name}")
            next
        
        name = f"{midiPath.stem}_Visualizer.mp4"
        visualizer = Path(midiPath.parent, name)
        try:
            assert visualizer.exists()
        except:
            print(f"Visualizer does not exist for {name}")
            next

        threads.append(VideoEditor(pianoroll,visualizer))
    
    if not threads:
        print(f"Nothing to thread. Please check the file paths.")
    else: 
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

    files = [Path(f.parent,f"{f.stem}.wav") for f in files]
    files = [f for f in files if f.exists()]

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