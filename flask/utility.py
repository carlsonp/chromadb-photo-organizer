from pathlib import Path

# https://betterprogramming.pub/glob-generators-with-python-be9ad86ca682
def get_imgs(directory: str, existingids: list, recursive: bool = True):
    path = Path(directory)
    pattern = '*.[jpJP][npNP]*[gG$]'
    frec = lambda p, g: p.rglob(g) if recursive else p.glob(g)
    for file in frec(path, pattern):
        # skip over existing images if the embeddings have already been inserted
        if (str(file) not in existingids):
            yield str(file)