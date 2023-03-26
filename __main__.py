import os
import random
from tqdm import tqdm
from pathlib import Path
from threading import Thread

from .__init__ import (GET_FILES, MIDIVisualizer, 
    FluidSynth, AudioDubber, AVP, VideoEditor,
    ChapterGenerator)


from PySimpleGUI import (popup_yes_no,
    popup_get_text, popup_get_file,
    popup_get_folder)


NOTES = None
COLOR = None
MIDIPATHS = None


def midi_to_pianoroll():
    global MIDIPATHS, COLOR, NOTES    
    threads = [MIDIVisualizer(f,NOTES,COLOR) for f in MIDIPATHS]
    for th in threads:
        th.start()

    while list(set(threads))[0] != True and len(list(set(threads))) == 1:
        for i, th in tqdm(enumerate(threads)):
            if type(th) != bool:
                if not th.is_alive():
                    th.join()
                    print(f"Thread {i} Completed.")
                    threads[i] = True


def generate_audio():
    global MIDIPATHS
    threads = [FluidSynth("studio",f) for f in MIDIPATHS]
    for th in threads:
        th.start()

    while list(set(threads))[0] != True and len(list(set(threads))) == 1:
        for i, th in tqdm(enumerate(threads)):
            if type(th) != bool:
                if not th.is_alive():
                    th.join()
                    print(f"Thread {i} Completed.")
                    threads[i] = True
                    
    
def visualizer_from_audio():
    global MIDIPATHS
    wavfiles = [Path(f.parent,f"{f.stem}.wav") for f in MIDIPATHS]
    wavfiles = [f for f in wavfiles if f.exists()]
    
    global COLOR
    threads = [AVP(f,COLOR) for f in wavfiles]
    for th in threads:
       th.start()

    while list(set(threads))[0] != True and len(list(set(threads))) == 1:
        for i, th in tqdm(enumerate(threads)):
            if type(th) != bool:
                if not th.is_alive():
                    print(f"Thread {i} Completed.")
                    th.join()
                    threads[i] = True


def overlay_pianoroll():
    threads = list()
    global MIDIPATHS
    for midiPath in MIDIPATHS:
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
        return
    
    for th in threads:
        th.start()

    while list(set(threads))[0] != True and len(list(set(threads))) == 1:
        for i, th in tqdm(enumerate(threads)):
            if type(th) != bool:
                if not th.is_alive():
                    print(f"Thread {i} Completed!")
                    th.join()
                    threads[i] = True


if __name__ == "__main__":

    COLORS = {1:"blue",2:"green",3:"red",4:"purple",5:"grey"}
    print(COLORS)
    COLOR = COLORS[int(input("Color?: "))]


    MAINMENU = [
        "Create Videos",
        "Merge into Chapters",
        "Chord Progression to Midi",
        "Transpose Midi",
        "Play Midi",
        "Play Progression"]
    
    
    CREATEVIDEOSMENU = [
        "Midi to Pianoroll",
        "Generate Audio",
        "Visualizer from Audio",
        "Overlay Pianoroll"]

    
    while True:
        
        os.system('cls')
        
        for i, option in enumerate(MAINMENU):
            print(f"{i+1}: {option}")
        
        while True:
            
            try:
                selection = int(input("Selection?: "))
                break
            
            except:
                print("\r???",end="")

        if selection == 1:

            os.system('cls')

            MIDIPATHS = GET_FILES([".midi",".mid"])
            print(f"Working in {MIDIPATHS[0].parent}")


            NOTES = popup_yes_no("Add Notes? ") == "Yes"
            if NOTES:
                midi_to_pianoroll()
                _ = input("Press Enter to continue...: ")
                
                generate_audio()
                _ = input("Press Enter to continue...: ")
                
                videosPaths = [Path(f.parent,f"{f.stem}_Pianoroll.mp4") for f in MIDIPATHS]
                audioPaths = [Path(f.parent,f"{f.stem}.wav") for f in MIDIPATHS]
                
                threads = [AudioDubber(vp,ap) for vp,ap in zip(videoPaths,audioPaths)]
                for th in threads:
                    th.start()

                while list(set(threads))[0] != True and len(list(set(threads))) > 1:
                    for i, th in enumerate(threads):
                        if not th.is_alive():
                            print(f"Thread {i} Completed.")
                            threads[i] = True

            else:
                for process in CREATEVIDEOSMENU:
                    _ = input(f"Press Enter to start: {process}: ") # blocking
                    process = "_".join(process.lower().split(" "))
                    process = eval(process)
                    process()

        elif selection == 2:

            videoDir = Path(popup_get_folder("Please open the video directory.").replace("//","/"))
            ChapterGenerator(videoDir).generate()