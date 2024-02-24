from flask import Flask
import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader
from utility import get_imgs
import threading
from pathlib import Path

def threaded_index(lock):
    try:
        lock.acquire()

        #client = chromadb.HttpClient(host='chromadb', port=8000)
        client = chromadb.HttpClient(host='192.168.1.112', port=8000)

        embedding_function = OpenCLIPEmbeddingFunction()
        image_loader = ImageLoader()

        collection = client.get_or_create_collection(
            name='chromadb-photo-organizer', 
            embedding_function=embedding_function, 
            data_loader=image_loader)

        existingids = collection.get(include=[])
        print(f"Existing indexed images: {len(existingids['ids'])}")
                    
        image_uris = []
        for img in get_imgs("/home/carlsonp/src/chromadb-photo-organizer/static/images/", existingids['ids']):
            image_uris.append(img)

        metadatas = []
        for p in image_uris:
            # add gif to the metadata path if the file exists, otherwise the static image
            if (Path(p.removesuffix('.png')).is_file()):
                gif_path = p.replace('/home/carlsonp/src/chromadb-photo-organizer', '.').removesuffix('.png')
                metadatas.append({"relative_path": gif_path, "favoritecount": 0})
            else:
                metadatas.append({"relative_path": p.replace('/home/carlsonp/src/chromadb-photo-organizer', '.'), "favoritecount": 0})
        
        ids = image_uris

        print(f"Adding {len(ids)} images")
        i = 0
        batchamount = 100
        while (i < len(ids)):
            print(f"adding {i} - {i+batchamount}")
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
                print(f"Removing image: {img} from ChromaDB as it no longer exists on disk")
                collection.delete(ids=[img])

        print("Finished indexing images")
        lock.release()
    except Exception as e:
        log.error(f"Error: {e}")