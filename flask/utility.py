import os
import subprocess
from pathlib import Path


# https://betterprogramming.pub/glob-generators-with-python-be9ad86ca682
def get_imgs(
    directory: str,
    existingids: list,
    patterns: list = ["*.[jJ][pP][gG$]", "*.[pP][nN][gG$]", "*.[wW][eE][bB][pP$]"],
    recursive: bool = True,
):
    path = Path(directory)
    # jpg, png, webp, etc.
    # glob searching uses unix shell matching NOT regex
    frec = lambda p, g: p.rglob(g) if recursive else p.glob(g)
    for pattern in patterns:
        for file in frec(path, pattern):
            # skip over existing images if the embeddings have already been inserted
            if str(file) not in existingids:
                yield str(file)


def get_videos(
    directory: str,
    existingids: list,
    patterns: list = ["*.[mM][pP][4$]", "*.[wW][eE][bB][mM$]", "*.[gG][iI][fF$]"],
    recursive: bool = True,
):
    path = Path(directory)
    # mp4, webm, gif, etc.
    # glob searching uses unix shell matching NOT regex
    frec = lambda p, g: p.rglob(g) if recursive else p.glob(g)
    for pattern in patterns:
        for file in frec(path, pattern):
            # skip over existing images if the embeddings have already been inserted
            if str(file) not in existingids:
                yield str(file)


def convertVideoFormat(
    searchpattern: str,
    sourcetype: str,
    endtype: str,
    parameters: str,
    deletesource: bool = False,
):
    # glob searching uses unix shell matching NOT regex
    for vid in get_videos("/static/images", [], [searchpattern]):
        if not Path(f"{vid.removesuffix(sourcetype)}{endtype}").is_file():
            ffmpeg_results = subprocess.run(
                f"ffmpeg -i {vid} -hide_banner -loglevel error {parameters} {vid.removesuffix(sourcetype)}{endtype}",
                capture_output=True,
                shell=True,
            )
            print(ffmpeg_results)
            if deletesource and ffmpeg_results.returncode == 0:
                # delete the source file
                os.remove(vid)
