# -*- coding: utf-8 -*-background

import sys
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
import traceback
import threading
import subprocess
from time import sleep
from typing import Union
from string import ascii_letters

import cv2
from vidgear.gears import CamGear
from vidgear.gears import WriteGear
from googleapiclient.discovery import build

from moviepy.editor import (
    concatenate_videoclips,VideoFileClip,
    AudioFileClip,CompositeVideoClip)

from PySimpleGUI import (
    popup_get_folder,popup_yes_no,
    popup_get_text)



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


class Streamer:
    
    def __init__(self, channelID: str="UC-RnLMNepBTHFitAfxltcBw"):
        self.channelID = channelID
        self.font = cv2.FONT_HERSHEY_COMPLEX_SMALL
        self.streamkey = popup_get_text("Stream Key?: ").strip()
        
        api_key = popup_get_text("Api Key?: ").strip()
        try:
            self.youtube = build('youtube','v3',developerKey=api_key)
            self.api_key = api_key
        
        except Exception as e:
            print("Api access failed.", end=str(e))
            self.api_key = None

    def __get_channel_playlists(self):
        playlists = []
        request = self.youtube.playlists().list(part='snippet', channelId=self.channelID, maxResults=50)
        response = request.execute()
        for item in response['items']:
            title = item['snippet']['title']
            playlist_id = item['id']
            playlists.append((title, playlist_id))
        return playlists

    def __get_playlist_videos(self, playlistID: str):
        videos = []
        request = self.youtube.playlistItems().list(part='snippet', playlistId=playlistID, maxResults=50)
        response = request.execute()
        for item in response['items']:
            title = item['snippet']['title']
            video_id = item['snippet']['resourceId']['videoId']
            videos.append((title, video_id))
        return videos

    def __write_title(self, frame, title):
        return cv2.putText(
            frame, title, (260,850), 
            self.font, 0.2, "white", 2, 
            cv2.LINE_AA, False)
    
    def __write_composer(self, frame, composer):
        return cv2.putText(
            frame, composer, (275,965), 
            self.font, 1.5, "white", 2, 
            cv2.LINE_AA, False)
        
    def _show_frame(self, frame, writer, composer, title):
        cv2.imshow(writer,
            self.__write_title(
                self.__write_composer(frame,composer),title))

    def _get_stream(vid: str, streamKey: str):
        stream = CamGear(
        source=f"https://youtu.be/{vid}",
        stream_mode=True,logging=True).start()
        
        writer = WriteGear(
            output_filename="rtmp://a.rtmp.youtube.com/live2/{}".format(streamKey),
            logging=True,
            **{"-acodec": "aac",
            "-ar": 44100,
            "-b:a": 712000,
            "-vcodec": "libx264",
            "-preset": "medium",
            "-b:v": "4500k",
            "-bufsize": "512k",
            "-pix_fmt": "yuv420p",
            "-f": "flv",})
        return (stream,writer)

    def get_composers(self):
        return self.__get_channel_playlists()


    def get_videos(self, composer: tuple):
        return self.__get_playlist_videos(composer[1])

    def stream(self):
        print(f"\rInitializing Infinite Stream...", end="")
        sleep(2)
        composers = self.get_composers()
        while True:
            random.shuffle(composers)
            playlistName = composers[0]
            playlistID = composers[1]
            string2find = "Selected Works by"
            if string2find in playlistName:
                videos = self.get_videos(playlistID)
                random.shuffle(videos)
                
                video = videos[0]
                title = video[0]
                vid = video[1]
                
                composer = playlistName.split("Selected Works by")[-1].strip().title()
                stream, writer = self._get_stream(vid,streamkey)
                
                while True:                
                    frame = stream.read()   
                    if not frame:
                        break

                    self._show_frame(frame,writer,composer,song[0])
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        break
            
                stream.stop()
                writer.close()


class Composer:
    
    
    def __init__(self):
        tones = ['C','D','E','F','G','A','B']
        semitones = ["C#","Eb","F#","Ab","Bb"]
    
    def chord_progression(self, progression, key: str, quality: str, interval: str):
        duration = interval
        scale = S(f"{key} {quality}")
        
        if type(progression) == str: progression = progression.split("-")
        return scale.chord_progression(progression,duration,interval)

    def broken_chord_progression(self, progression, key: str, quality: str, interval: str):
        progression = self.chord_progression(progression, key, quality, interval)
        for chord in progression:
            notes = chord.notes
            chord.notes = notes[0] | notes[2] |notes[1] | notes[2]  
        return progression 


class AudioDubber:

    def __init__(self, audioPath: Path, videoPath: Path):
        self.dest      = str(Path(audioPath.parent,f"{audioPath.stem}.mp4"))
        self.audioPath = str(audioPath)
        self.videoPath = str(videoPath) 

    def dub(self):
        try:
            video  = VideoFileClip(self.videoPath)
            audio  = AudioFileClip(self.audioPath)
            dubbed = video.set_audio(audio)
            dubbed.write_videofile(self.dest)
        
        except Exception as e:
            print(str(e))


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
        threading.Thread.__init__(self)
        
        destName = f"{midiPath.stem}_Pianoroll.mp4" 
        
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
        
        try:
            output = subprocess.check_output(self.app+params,shell=False)
        
        except Exception as e:
            print(output,end=str(e))


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
        
        try:
            p = subprocess.check_output(self.app+params,shell=False)
            print(p)
        
        except Exception as e:
            print(str(e))


class AVP(threading.Thread):

    BACKGROUNDS = [Path(CWD,"assets",bg) for bg in os.listdir(Path(CWD,"assets")) \
                   if Path(CWD,"assets",bg).suffix == ".png"]

    def __init__(self, audioPath: Path, color: str,
                 backgrounds=BACKGROUNDS):
        threading.Thread.__init__(self)
        
        dest = Path(audioPath.parent,f"{audioPath.stem}_Visualizer.mp4")
        self.dest = str(dest)

        background = [bg for bg in backgrounds if bg.stem == color][0] 
        self.background = str(background)
        if audioPath.suffix != ".wav":
            audioPath = Path(audioPath.parent,f"{audioPath.stem}.wav")
        self.audioPath = str(audioPath)
    
    def run(self):
        cmd = f'avp -c 0 image path="{self.background}"'
        cmd += f' -c 1 classic color=255,255,255 -i "{self.audioPath}"'
        cmd += f' -o "{self.dest}"'
        
        try:
            p = subprocess.check_output(cmd,shell  = False)
        
        except Exception as e:
            print(str(e))
        

class VideoEditor(threading.Thread):


    def __init__(self, pianorollPath: Path, visualizerPath: Path):
        threading.Thread.__init__(self)
        
        destName        = pianorollPath.stem.split("_Pianoroll")[0]
        self.dest       = str(Path(pianorollPath.parent,f"{destName}.mp4"))
        self.visualizer = str(visualizerPath)
        self.pianoroll  = str(pianorollPath)
        
    def run(self):
        try:
            visualizerClip = VideoFileClip(self.visualizer).resize((1920,1080))
            pianorollClip  = VideoFileClip(self.pianoroll).resize((1920,1080))
            duration = pianorollClip.duration
            actualDuration = duration - 5
            pianorollClip = pianorollClip.subclip(0,actualDuration)
            pianorollClip  = crop(pianorollClip, y1=1080//2)

            combinedVideo = CompositeVideoClip([
                visualizerClip.volumex(1.0),
                pianorollClip.set_position((0,0))],
                size = (1920,1080))
            combinedVideo.write_videofile(self.dest,fps=60,codec='mpeg4')

        except Exception as e:
            print(str(e))


class ChapterGenerator:


    def __init__(self, videoDir: Path):
        self.videoPaths = [
            Path(videoDir,f) for f in os.listdir(videoDir) \
                if Path(videoDir,f).suffix == ".mp4"]
        random.shuffle(self.videoPaths)

    def __create_chapter_listing(self):
        chapterListing = ""
        totalDuration = 0
        
        for video in self.videoPaths:
            try:
                clip = VideoFileClip(str(video))
                duration = clip.duration
            
            except Exception as e:
                trackback.print_exception(e)
                msg = f"Please remove {video.name} from the source folder and try again."
                print(msg)
                return
            
            title = video.stem
            timestamp = "{:02d}:{:02d}:{:02d}".format(int(totalDuration // 3600),
                            int(totalDuration % 3600 // 60),
                            int(totalDuration % 60))

            ts_components = timestamp.split(":")
            if int(ts_components[0]) == 0:
                ts_components = ts_components[1:]
                
            if int(ts_components[0]) < 10:
                ts_components[0] = ts_components[0][1:]
            
            timestamp = ":".join(ts_components)
            chapterListing += "{} - {}\n".format(timestamp, title)
            
            totalDuration += duration
        
        dest = Path(self.videoPaths[0].parent, "chapterListing.txt")
        
        try:
            with open(dest, "w+") as listing:
                listing.write(chapterListing)
        
        except Exception as e:
            trackback.print_exception(e)
            print("Failed to write Chapter Listing...")
    
    def generate(self):
        clips = [VideoFileClip(str(v)) for v in self.videoPaths]
       
        trim = int(popup_get_text("Trim?: ").strip())
        if trim > 0:
            clips = [c.subclip(0,c.duration-trim) for c in clips]

        duration = sum([c.duration for c in clips])
        mins = duration // 60
        if popup_yes_no(f"Generate {mins} minute video?") == "Yes":
            self.__create_chapter_listing()
            concatVideo = concatenate_videoclips(clips)
        
            finalVideoName = list("ByPassAudioWriteBug")
            random.shuffle(finalVideoName)
            finalVideoName = f'{"".join(finalVideoName)}.mp4'        
            
            dest = str(Path(self.videoPaths[0].parent,finalVideoName))
            concatVideo.write_videofile(dest)