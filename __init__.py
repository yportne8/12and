# -*- coding: utf-8 -*-background

import sys
import random

from pathlib import Path
if getattr(sys, 'frozen', False):
    CWD = sys._MEIPASS
else:
    CWD = Path(__file__).parent
sys.path.append(str(Path(CWD,"bin")))

import os
import shutil
import random
import atexit
import threading
import subprocess
from time import sleep
from typing import Union
from string import ascii_letters

from ffmpeg import FFmpeg
from moviepy.editor import (vfx,
    concatenate_videoclips,VideoFileClip,
    AudioFileClip,TextClip,CompositeVideoClip)
from moviepy.video.fx.all import crop, mask_color
from PySimpleGUI import popup_get_folder, popup_yes_no, popup_get_text



def _FIX_WINDOWS_PATH(source:Union[Path,str]):
    if type(source) == str: Path(source.replace("//","/"))
    new_stem = "".join([c for c in source.stem if c.isalnum() or c in [" ","-","_"]])
    dest = Path(source.parent,f"{new_stem}{source.suffix}")
    
    if source != dest: shutil.move(str(source),str(dest))
    return dest


def GET_FILES(suffix):
    msg          = "Please select a folder."
    default_path = str(Path(Path.home(),"Desktop"))
    directory    = popup_get_folder(msg,default_path=default_path)
    paths        = [Path(directory,f) for f in os.listdir(directory)]
    
    if type(suffix) == str: suffix = [suffix]
    return [_FIX_WINDOWS_PATH(p) for p in paths if p.suffix in suffix]


class Composer:

    def progression_midi(self, progression: str, bpm: int=120, all_keys: bool=False):
        _12keys = ["C","C#","D","Eb","E","F","F#","G","Ab","A","Bb","B"]
        
        progressions = list()
        repeat = 2 if all_keys else 1
        for tone in _12keys:
            for quality in ["major", "minor"]:
                keysig = f"{tone} {quality}"
                c1 = S(keysig).chord_progression(progression.split("-"),1/6,1/6)
                c2 = S(keysig).chord_progression(progression.split("-"),1/4,1/4)
                                   
                chord_progression = c1*2 | rest(0.5) | c1[::-1]*2 | rest(0.5) | c2*2 | rest(0.5) | c2[::-1]*2
                keysigMidi = Path(playlistFolder, f"{progression} Progression in {tone} {quality}.midi")
                write(chord_progression, bpm=bpm, name=keysigMidi)
                progressions.append(c1 | rest(0.5))
        fullMidi = Path(playlistFolder, f"{progression} Progression in All Key Signatures).midi")
        write(progressions, fullMidi)


class AudioDubber:

    def __init__(self, audioPath: Path, videoPath: Path):
        self.dest      = str(Path(videoPath.parent,f"{videoPath.stem}_dubbed.mp4"))
        self.audioPath = str(audioPath)
        self.videoPath = str(videoPath) 

    def dub(self):
        video  = VideoFileClip(self.videoPath)
        audio  = AudioFileClip(self.audioPath)
        dubbed = video.set_audio(audio)
        dubbed.write_videofile(self.dest)


class MIDIVisualizer(threading.Thread):

    APP = Path(CWD,"bin","MIDIVisualizer.exe")
    CONFIG = Path(CWD,"assets","config.ini")
    BACKGROUNDS = [Path(CWD,"assets",bg) for bg in os.listdir(Path(CWD,"assets")) \
                   if Path(CWD,"assets",bg).suffix == ".jpg"]

    def __init__(self, midiPath: Path, notes: bool, color: str,
                 # color: blue, green, grey, purple, red
                 peddle      : bool = True,
                 app         : Path = APP,
                 config      : Path = CONFIG,
                 backgrounds : dict = BACKGROUNDS):
        self.stdout = None
        self.stderr = None
        threading.Thread.__init__(self)
        
        destName = f"{midiPath.stem}.mp4" if notes \
                    else f"{midiPath.stem}_Pianoroll.mp4" 
        
        self.app        = str(app)
        self.dest       = str(Path(midiPath.parent,destName))
        self.midiPath   = str(_FIX_WINDOWS_PATH(midiPath)) 
        
        background = [bg for bg in backgrounds if bg.stem == color][0] 
        self.background = str(background)
        
        showScore  = 1 if notes else 0
        showNotes  = 1 if notes else 0
        if peddle:
            showPeddle = 1
            self.height = "1080"
            self.width = "1920"
        else:
            showPeddle = 0
            self.height = "1080"
            self.width = "1080"
            self.background = [bg for bg in backgrounds if bg.stem == "square"][0]

        with open(config, "r") as f:
            contents = f.read()
            contents = contents % (showScore,showNotes,showPeddle,self.background)
            config = Path(config.parent, f"_{config.stem}.ini")
            with open(config, "w+") as f:
                f.write(contents)

        self.config = str(config)

    def run(self):
        params  = f' --export "{self.dest}" --format MPEG4 --config "{self.config}"'
        params += f' --midi "{self.midiPath}" --size {self.width} {self.height}'
        p = subprocess.Popen(
            self.app+params,shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        self.stdout, self.stderr = p.communicate()


class FluidSynth(threading.Thread):

    GAIN = "0.2"
    SAMPLE_RATE = "44100"
    FSYNTH = Path(CWD,"bin","fluidsynth.exe")
    SOUNDFONTS = [Path(CWD,"soundfonts",sf) for sf in os.listdir(Path(CWD,"soundfonts"))]

    def __init__(self, soundfont: str, midiPath: Path,
                 gain        : str  = GAIN,
                 app         : Path = FSYNTH,
                 soundfonts  : dict = SOUNDFONTS,
                 sample_rate : str  = SAMPLE_RATE):
        self.stdout = None
        self.stderr = None
        threading.Thread.__init__(self)
        
        self.app         = str(app)
        self.gain        = gain
        self.sample_rate = sample_rate
        
        soundfont = [sf for sf in soundfonts if sf.stem == soundfont][0] 
        self.soundfont   = str(soundfont)
        
        self.dest        = str(Path(midiPath.parent,f"{midiPath.stem}.wav"))
        self.midiPath    = str(midiPath)

    def run(self):
        params  = f' -ni -g {self.gain} "{self.soundfont}"'
        params += f' "{self.midiPath}" -F "{self.dest}"'
        params += f' -r {self.sample_rate}'
        p = subprocess.Popen(self.app+params,
                             shell=False,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        self.stdout, self.stderr = p.communicate()


class AVP(threading.Thread):

    BACKGROUNDS = [Path(CWD,"assets",bg) for bg in os.listdir(Path(CWD,"assets")) \
                   if Path(CWD,"assets",bg).suffix == ".png"]

    def __init__(self, audioPath: Path, color: str,
                 backgrounds=BACKGROUNDS):
        self.stdout = None
        self.stderr = None
        threading.Thread.__init__(self)

        self.app        = "avp"
        self.dest       = str(Path(audioPath.parent,f"{audioPath.stem}_Visualizer.mp4"))
        self.audioPath  = str(audioPath)
        
        background = [bg for bg in backgrounds if bg.stem == color][0] 
        self.background = str(background)
        
    
    def run(self):
        params  = f' -c 0 image path="{self.background}"'
        params += ' -c 1 classic color=255,255,255'
        params += f' -i "{self.audioPath}" -o "{self.dest}"'
        p = subprocess.Popen(self.app+params,
                             shell=False,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        self.stdout, self.stderr = p.communicate()
        

class VideoEditor(threading.Thread):


    def __init__(self, pianorollPath: Path, visualizerPath: Path):
        self.stdout = None
        self.stderr = None
        threading.Thread.__init__(self)
        
        destName        = pianorollPath.stem.split("_Pianoroll")[0]
        self.dest       = Path(pianorollPath.parent,f"{destName}.mp4")
        self.visualizer = str(visualizerPath)
        self.pianoroll  = str(pianorollPath)
        
    def run(self):
        visualizerClip = VideoFileClip(self.visualizer).resize((1920,1080))
        pianorollClip  = VideoFileClip(self.pianoroll).resize((1920,1080))
        pianorollClip  = crop(pianorollClip, y1=1080//2)
        
        combinedVideo = CompositeVideoClip([
            visualizerClip.volumex(1.0),
            pianorollClip.set_position((0,0))],
            size = (1920,1080))

        combinedVideo.write_videofile(self.dest,fps=60,codec='mpeg4',threads=6)


class ChapterGenerator(threading.Thread):


    def __init__(self, videoDir: Path):
        self.stdout = None
        self.stderr = None
        threading.Thread.__init__(self)

        self.videoPaths = [
            Path(videoDir,f) for f in os.listdir(videoDir) \
                if Path(videoDir,f).suffix == ".mp4"]
        random.shuffle(self.videoPaths)

    def __create_chapter_listing(self):
        chapterListing = ""
        totalDuration = 0
        
        for video in self.videoPaths:
            title = video.stem
            clip = VideoFileClip(str(video))
            duration = clip.duration
            
            timestamp = "{:02d}:{:02d}:{:02d}".format(int(total_duration // 3600),
                            int(total_duration % 3600 // 60),
                            int(total_duration % 60))
            ts_components = timestamp.split(":")
            if int(ts_components[0]) == 0:
                ts_components = ts_components[1:]
                if int(ts_components[0]) < 10:
                    ts_components[0] = str(int(ts_components))
            timestamp = ":".join(ts_components)
            chapterListing += "{} - {}\n".format(timestamp, title)
            totalDuration += duration
        
        dest = Path(self.videoPaths[0].parent, "chapterListing.txt")
        with open(dest, "w+") as cl:
            cl.write(chapterListing)
    
    def run(self):
        clips = [VideoFileClip(str(v)) for v in self.videoPaths]
        concatVideo = concatenate_videoclips(clips)
        
        finalVideoName = list("ByPassAudioWriteBug")
        random.shuffle(finalVideoName)
        finalVideoName = f'{"".join(finalVideoName)}.mp4'        
        
        dest = str(Path(self.videoPaths[0].parent,finalVideoName))
        concatVideo.write_videofile(dest)