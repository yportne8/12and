# -*- coding: utf-8 -*-
# Code used to create YouTube Channels 12and and 12andProgressions.

# [About 12&] 12and is a non-monetized YouTube Channel. This includes the
# 24/7 Live stream of the contents of this channel to drive viewership.

# [About 12& Progressions] 12andProgressions is a monetized channel. All videos 
# are under one minute (where possible) viewable on repeat without interruptions. The channel will be introducing advanced chords
# and chord progressions, as well as midi-renditions of string instruments as we
# move forward.


import os
import shutil
import random
import subprocess
from time import sleep
from pathlib import Path

import pandas as pd
from musicpy import (
    C,chord_progression,write,scale,rest)
from moviepy.editor import ( 
    concatenate_videoclips,VideoFileClip,
    AudioFileClip,)

import googleapiclient.errors
import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload


class MaestroDataSet:
    
    def __init__(self):
        self.sourceDir = Path(Path(__file__).parent, "maestro")
        if not self.sourceDir.exists(): os._exit(0)
        
        self.midiDir = Path(Path.home(), "Desktop", "Midi")
        if not self.midiDir.exists(): self.midiDir.mkdir()
        
        self.wavDir = Path(self.midiDir.parent, "Wav")
        if not self.wavDir.exists(): self.wavDir.mkdir()
        
        self.tags = pd.read_csv("composer_title_track.csv")
        videoTitles = f"{self.tags.title} ({self.tags.COMPOSER})"
        self.tags["VIDEOTITLE"] = videoTitles
        
        # For future reference👍
        self.tags[["PATH", "VIDEOTITLE"]].to_csv("deduped_tracktitle_videotitle.csv")
        
    def move_rename(self):

        for path, vtitle in zip(self.tags.PATH, self.tags.VIDEOTITLE):
            filestem = path.stem
            
            try:
                midifile = str(Path(self.sourceDir, f"{filestem}.midi"))
                destMidifile = str(Path(self.midiDir, f"{vtitle}.midi"))
                shutil.move(midifile, destMidifile)
            
                wavfile = str(Path(self.sourceDir, f"{filestem}.wav"))
                destWavfile = str(Path(self.wavDir, f"{vtitle}.wav"))            
                shutil.move(wavfile, destWavfile)
            except:
                print(f"{filestem} does not exist.")
        return (self.midiDir, self.wavDir)


class Composer:
        
    def __init__(self):
        self.transposable_progressions = pd.read_csv(
            Path(Path(__file__).parent,"transposable_progressions.csv"))
        self.nontransposable_progressions = pd.read_csv(
            Path(Path(__file__).parent,"nontransposable_progressions.csv"))
        
    def get_chord_progression(self, progression: str, dest: Path=None):
        I,II,III,IV,V,VI,VII="C","D","E","F","G","A","B"
        i,ii,iii,iv,v,vi,vii="Cm","Dm","Em","Fm","Gm","Am","Bm"
        
        progression = progression.split("-")
        for j, c in enumerate(progression):
            progression[j] = eval(c)
        
        if dest:
            write(progression, bpm=120, name=dest)
        else:
            progression = chord_progression(progression,durations=1/4,intervals=0.25)
            return progression | rest(1) | progression | rest(1) | progression 
            
    def transpose_progressions_tofile(self, progression, label: str,
                                      playlistFolder: Path, minor=False, bpm=120):
        keylabels = ["C","D","E","F","G","A","B"]
        quality = "minor" if minor else "major"
        for key in keylabels:
            copyOfprogression = progression
            copyOfprogression.modulation(scale("C","major"),scale(key,quality))
            dest = Path(playlistFolder,f"{label} Progression in {key} major.midi")
            write(progression, bpm=bpm, name=dest)
            

class Director:
    
    def __init__(self):
        self.videoLength = dict()
        
    def _divide_chunks(self, folder: Path, numTracks):
        files = [Path(folder, f) for f in os.listdir(folder)]
        random.shuffle(files)
        for i in range(0, len(files), numTracks):
            yield files[i:i+numTracks]
        
    def _duration(self, mp4: Path):
        clip = VideoFileClip(mp4)
        duration = clip.duration
        print(f"Video duration is {duration}. Type {type(duration)}")
        return duration
    
    def create_video(self, channel: str, midiSource: Path):
        size = (1600,900) if channel == "12and" else (1080,1080)
        if not midiSource.exists(): 
            print(f"{midiSource} not found.")
            return
        app = str(Path(Path(__file__).parent, "MIDIVisualizer.exe"))
        dest = str(Path(midiSource.parent,f"{midiSource.stem}.mp4"))
        midiSource = str(midiSource)
        midiSource = rf"{midiSource}"
        parameters = f'--midi "{midiSource}"'
        parameters += f" --size {size[0]} {size[1]}"
        if channel == "12and":
            config = str(Path(Path(__file__).parent,'maestroConfig.ini'))
            parameters += f' --config "{config}"'
        else:
            config = str(Path(Path(__file__).parent,'progressionsConfig.ini'))
            parameters += f' --config "{config}"'
        parameters += f' --export "{dest}" --format MPEG4'
        subprocess.check_output(
            f"{app} {parameters}",
            stderr=subprocess.STDOUT,
            shell=True)
        sleep(2)
        if dest.exists():
            print(f"{dest.name} created.")
                
    
    def redub(self, videoFile: Path, audioFile: Path):
        audio = AudioFileClip(audioFile)
        video = VideoFileClip(videoFile)
        dub = video.set_audio(audio)
        dub.write_videofile(videoFile)
        
    def concatenate(self, folder: Path, length: int):
        if not folder.is_dir():
            print("A directory of mp4 files is required.")
            
        numTracks = {
            1: 6,
            4: 24,
            10: 60}[length]
        
        volumes = list(self._divide_chunks(folder, numTracks))
        dest = Path(folder, "Completed")
        if not dest.exists(): dest.mkdir()
        
        for i, volume in enumerate(volumes):
            tracks = list()
            for track in volume:
                self.videoLength[track.stem] = self._duration(track)
            video = concatenate_videoclips(tracks)
            video.write_videofile(Path(dest, f"Vol_{i}.webm"))
            
        self.videoLength.to_csv(f"Vol_{i}_videotitle_duration.csv")
        
    def recut(self, mp4: Path):
        try:
            tracklisting = pd.read_csv(Path(Path(__file__).parent, f"{mp4.stem}_videotitle_duration.csv"))
        except:
            print("Failed to find track listing")
            
        start, video = 0, VideoFileClip(mp4)
        print(f"Generating {len(tracklisting)} videos from {mp4.name}...")
        for title, duration in zip(tracklisting.VIDEOTITLE, tracklisting.DURATION):
            clip = video.clip(start, start + duration)
            start = start + duration
            
            dest = Path(self.dest, f"{title}.mp4")
            clip.write_videofile(dest)
            if dest.exists():
                print(f"{dest.name} has been created.")
            else:
                if input(f"{dest.name} could not be found. Continue?"): os._exit()
            

class _12andUploader:
    
    def __init__(self):
        self.client_secrets_file = str(Path(Path(__file__).parent,"12and_client_secret.json"))
        self.license = "creativeCommons"
        
    def _short_link(self, videoTitle: str):
        for i, c in enumerate(videoTitle): videoTitle[i] = c if c.isalnum() else "_"
        return f"https://12and.org/youtube/{videoTitle}"
    
    def _description(self, videoTitle: str):
        description = f"YouTube's AD-free version => {self._short_link(videoTitle)}\n"
        description += "For instructional shorts check out @12andprogressions 👍\n\n\n"
        description += "* Audio and transcription courtesy of Google LLC."
        
    def _upload(self, license: str, videoPath: Path, include_description: bool=False):
        description = self._description(videoPath.stem() if include_description else "")
        request = self.youtube().videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "categoryId": "10",
                    "description": description,
                "title": videoPath.stem},
            "status": {
                "privacyStatus": "public",
                "notifySubscribers": "False",
                "license": license}},
            media_body=MediaFileUpload(str(videoPath)))
        response = request.execute()
        print(response)
        return response["id"]
        
    def get_youtube(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
        api_service_name, api_version = "youtube", "v3"
        
        return googleapiclient.discovery.build(
            api_service_name, api_version,
            credentials=google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                self.client_secrets_file, scopes).run_console())

    def create_playlist(self, title: str):
        description = "Solo Piano Performances set to Piano Visualization.\n"
        description += "For instructional shorts check out @12andprogressions"
        request = self.get_youtube().playlists().insert(
            part="snippet,status",
            body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": [""],
                "defaultLanguage": "en"},
            "status": {"privacyStatus": "public"}})
        response = request.execute()
        print(response)
        return response["id"]
        
    def insert_into_playlist(self, playlistID: str, videoID: str):
        request = self.youtube().playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlistID,
                    "position": 0,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": videoID}}})
        response = request.execute()
        print(response)
        
    def upload_into_playlist(self, playlistID: str, videoPath: Path, include_description: False):
        videoID = self._upload(self.license, videoPath, include_description)
        self.insert_into_playlist(playlistID, videoID)


class _12andProgressionsUploader(_12andUploader):
    
    def __init__(self):
        super().__init__()
        self.client_secrets_file = str(Path(Path(__file__).parent,"client_secret.json")) 
        self.license = "youtube"
        
    def get_youtube(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
        api_service_name, api_version = "youtube", "v3"
       
        
        return googleapiclient.discovery.build(
            api_service_name, api_version,
            credentials=google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                self.client_secrets_file, scopes).run_console())
        
    def create_playlist(self, title: str):
        request = self.get_youtube().playlists().insert(
            part="snippet,status",
            body={
            "snippet": {
                "title": title,
                "description": "New progressions added regularly, subscribe for notifications!",
                "tags": [
                    "12&","twelve and","twelveand","12&Progressions",
                    "12& Progressions","12 and progressions","12 andprogressions",
                    "twelveandprogressions","twelve and progressions",
                    "twelveand progressions","twelve andprogressions"],
                "defaultLanguage": "en"},
            "status": {"privacyStatus": "public"}})
        print(request.execute())