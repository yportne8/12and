import os
import sys
import inspect
from pathlib import Path

from .__init__ import Transcriber, Director, Composer, _12andProgressionsUploader, _12andUploader


def _12andProgressionsMain():
    composer, director, uploader = Composer(), Director(), _12andProgressionsUploader()
    dest = Path(Path(__file__).parent,"Progression Midi")
    if not dest.exists(): dest.mkdir()

    df = composer.transposable_progressions
    playlistnames = list(set(df.PLAYLIST.to_list()))
    
    for name in playlistnames:
        playlistFolder = Path(dest, name)
        if not playlistFolder.exists(): playlistFolder.mkdir()
        
        filteredDf = df[df.PLAYLIST == name]
        #playlistID = uploader.create_playlist(name)
        for label in filteredDf.PROGRESSION:
            composer.get_chord_progression(label,playlistFolder)
            for f in os.listdir(playlistFolder):
                f = Path(playlistFolder, f)
                if f.suffix == ".midi":
                    videoPath = director.create_video(channel="progressions",midiSource=f)
                    #uploader.upload_into_playlist(
                    #    playlistID=playlistID,
                    #    videoPath=videoPath,
                    #    include_description=False)

    df = composer.nontransposable_progressions
    #playlistID = uploader.create_playlist("Non-Transposable Progressions")
    playlistFolder = Path(Path.home(),"Desktop","Progression Midi","Non-Transposable Progressions")
    if not dest.exists(): dest.mkdir()
    name = f"{progression} Progression (Non-Transposable).midi"
    for progression in df.PROGRESSION:
        composer.get_chord_progression(label,playlistFolder)
        for f in os.listdir(playlistFolder):
            f = Path(playlistFolder, f)
            if f.suffix == ".midi":
                videoPath = director.create_video(channel="progressions",midiSource=f)
                #uploader.upload_into_playlist(
                #    playlistID=playlistID,
                #    videoPath=videoPath,
                #    include_description=False)
    

def _12andMain():
    transcriber  = Transcriber()
    try:
        transcriber.get_vizualizations()
    except Exception as e:
        inspect.trace(e)


if __name__ == "__main__":


    channel = sys.argv[1]
    try:
        _12andMain() if channel == "12and" else _12andProgressionsMain()
    except Exception as e:
        inspect.trace(e)