from flask import Flask
import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader
from utility import get_imgs

def threaded_index():
    try:
        #client = chromadb.HttpClient(host='chromadb', port=8000)
        client = chromadb.HttpClient(host='192.168.1.112', port=8000)

        embedding_function = OpenCLIPEmbeddingFunction()
        image_loader = ImageLoader()

        # existing items don't seem to have metadata updated so in some cases it's easier just to blow it away
        #client.delete_collection(name="chromadb-photo-organizer")

        collection = client.get_or_create_collection(
            name='chromadb-photo-organizer', 
            embedding_function=embedding_function, 
            data_loader=image_loader)

        existingids = collection.get(include=[])
        print(f"Existing indexed images: {len(existingids['ids'])}")
                    
        image_uris = []
        for img in get_imgs("/home/carlsonp/src/chromadb-photo-organizer/images/", existingids['ids']):
            image_uris.append(img)
        #app.logger.info(image_uris)

        relative_paths = []
        for p in image_uris:
            relative_paths.append({"relative_path": p.replace('/home/carlsonp/src/chromadb-photo-organizer', '.')})
        #app.logger.info(relative_paths)
        
        #ids = [str(i) for i in range(len(image_uris))]
        ids = image_uris

        print(f"Adding {len(ids)} images")
        i = 0
        batchamount = 50
        while (i < len(ids)):
            print(f"adding {i} - {batchamount}")
            if (i+batchamount > len(ids)):
                collection.add(ids=ids[i:len(ids)], uris=image_uris[i:len(ids)], metadatas=relative_paths[i:len(ids)])
                break
            else:
                collection.add(ids=ids[i:i+batchamount], uris=image_uris[i:i+batchamount], metadatas=relative_paths[i:i+batchamount])
            i = i + batchamount
        print("Finished indexing images")
    except Exception as e:
        print(f"Error: {e}")