from pathlib import Path

# https://betterprogramming.pub/glob-generators-with-python-be9ad86ca682
def get_imgs(directory: str, existingids: list, recursive: bool = True):
    path = Path(directory)
    # jpg, png, jpeg, etc.
    # glob searching uses unix shell matching NOT regex
    pattern = '*.[jpJP][npNP]*[gG$]'
    frec = lambda p, g: p.rglob(g) if recursive else p.glob(g)
    for file in frec(path, pattern):
        # skip over existing images if the embeddings have already been inserted
        if (str(file) not in existingids):
            yield str(file)

def get_videos(directory: str, existingids: list, patterns: list = ['*.[mM][pP][4$]', '*.[wW][eE][bB][mM$]', '*.[gG][iI][fF$]'], recursive: bool = True):
    path = Path(directory)
    # mp4, webm, gif, etc.
    # glob searching uses unix shell matching NOT regex
    frec = lambda p, g: p.rglob(g) if recursive else p.glob(g)
    for pattern in patterns:
        for file in frec(path, pattern):
            # skip over existing images if the embeddings have already been inserted
            if (str(file) not in existingids):
                yield str(file)