import os, subprocess, sys
from flask import Flask
import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader
from utility import get_imgs, get_videos
from pathlib import Path

def threaded_index(lock,app):
    try:
        lock.acquire()

        if (os.environ.get('ORGANIZE_FILES') and os.environ.get('ORGANIZE_FILES').lower() == "true"):
            # remove some bad characters from filenames
            for replaceme in [',', '%']:
                for f in list(get_videos("/static/images",[])) + list(get_imgs("/static/images",[])):
                    if (replaceme in f):
                        os.rename(f, f.replace(replaceme, ""))

            # rename jpeg to jpg
            for f in list(get_imgs("/static/images",[])):
                if (f.lower().endswith(".jpeg")):
                    # https://stackoverflow.com/questions/9943504/right-to-left-string-replace-in-python
                    os.rename(f, 'jpg'.join(f.rsplit('.jpeg', 1)))

            app.logger.info("Running detox...")
            detox_results = subprocess.run("detox -r -v /static/images/", capture_output=True, shell=True)
            app.logger.info(detox_results)

            app.logger.info("Converting GIF files to MP4...")
            # glob searching uses unix shell matching NOT regex
            for vid in get_videos("/static/images", [], ["*.[gG][iI][fF$]"]):
                if (not Path(f"{vid.removesuffix('.gif')}.mp4").is_file()):
                    ffmpeg_results = subprocess.run(f"ffmpeg -i {vid} -hide_banner -loglevel error -movflags faststart -pix_fmt yuv420p -vf 'scale=trunc(iw/2)*2:trunc(ih/2)*2' {vid.removesuffix('.gif')}.mp4", capture_output=True, shell=True)
                    app.logger.info(ffmpeg_results)
                    if (ffmpeg_results.returncode == 0):
                        # delete the gif file
                        os.remove(vid)

            app.logger.info("Extracting images from video files...")
            for vid in get_videos("/static/images", []):
                if (not Path(f"{vid}.png").is_file()):
                    if (vid.lower().endswith(".gif")):
                        process_results = subprocess.run(f"convert '{vid}[0]' {vid}.png", capture_output=True, shell=True)
                    else:
                        # webm, mp4, etc.
                        process_results = subprocess.run(f"ffmpeg -i {vid} -hide_banner -loglevel error -vf 'select=eq(n\,0)' -vframes 1 {vid}.png", capture_output=True, shell=True)
                    app.logger.info(process_results)

            app.logger.info("Finished organizing files")

        client = chromadb.HttpClient(host='chromadb', port=8000)

        embedding_function = OpenCLIPEmbeddingFunction()
        image_loader = ImageLoader()

        collection = client.get_or_create_collection(
            name='chromadb-photo-organizer', 
            embedding_function=embedding_function, 
            data_loader=image_loader)

        existingids = collection.get(include=[])
        app.logger.info(f"Existing indexed images: {len(existingids['ids'])}")
                    
        image_uris = []
        for img in get_imgs("/static/images/", existingids['ids']):
            image_uris.append(img)

        metadatas = []
        for p in image_uris:
            # add gif/video to the metadata path if the file exists, otherwise the static image
            file_type = ""
            if (Path(p.removesuffix('.png')).is_file()):
                animated_path = p.removesuffix('.png')
                if (animated_path.lower().endswith(".mp4")):
                    file_type = "video/mp4"
                elif (animated_path.lower().endswith(".webm")):
                    file_type = "video/webm"
                metadatas.append({"relative_path": animated_path, "favoritecount": 0, "file_type": file_type})
            else:
                if (animated_path.lower().endswith(".png")):
                    file_type = "image/png"
                elif (animated_path.lower().endswith(".jpg") or animated_path.lower().endswith(".jpeg")):
                    file_type = "image/jpeg"
                elif (animated_path.lower().endswith(".gif")):
                    file_type = "image/gif"
                metadatas.append({"relative_path": p, "favoritecount": 0, "file_type": file_type})
        
        ids = image_uris

        app.logger.info(f"Adding {len(ids)} images")
        i = 0
        batchamount = 100
        while (i < len(ids)):
            app.logger.info(f"adding {i} - {i+batchamount}")
            if (i+batchamount > len(ids)):
                collection.add(ids=ids[i:len(ids)], uris=image_uris[i:len(ids)], metadatas=metadatas[i:len(ids)])
                break
            else:
                collection.add(ids=ids[i:i+batchamount], uris=image_uris[i:i+batchamount], metadatas=metadatas[i:i+batchamount])
            i = i + batchamount
        
        # delete images from ChromaDB that no longer exist on disk
        metadatacleanup = collection.get(include=[])
        for img in metadatacleanup['ids']:
            if (not Path(img).is_file()):
                app.logger.info(f"Removing image: {img} from ChromaDB as it no longer exists on disk")
                collection.delete(ids=[img])

        app.logger.info("Finished indexing images")
        lock.release()
    except Exception as e:
        app.logger.error(f"Error: {e}")