import time, sys, os
import logging as log
import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader


def indexer():
    logging = log.getLogger('chromadb-photo-organizer')
    logging.setLevel(log.INFO)
    # logging is a singleton, make sure we don't duplicate the handlers and spawn additional log messages
    if not logging.handlers:
        logHandler = log.StreamHandler()
        logHandler.setLevel(log.INFO)
        logHandler.setFormatter(log.Formatter("{%(pathname)s:%(lineno)d} %(asctime)s - %(levelname)s - %(message)s", '%m/%d/%Y %I:%M:%S %p'))
        logging.addHandler(logHandler)
        logging = log.LoggerAdapter(logging)

    client = chromadb.HttpClient(host='chromadb', port=8000)

    embedding_function = OpenCLIPEmbeddingFunction()
    image_loader = ImageLoader()

    collection = client.get_or_create_collection(
        name='chromadb-photo-organizer', 
        embedding_function=embedding_function, 
        data_loader=image_loader)
    
    image_uris = sorted([os.path.join("/images/", image_name) for image_name in os.listdir("/images/")])
    ids = [str(i) for i in range(len(image_uris))]

    collection.add(ids=ids, uris=image_uris)

if __name__ == '__main__':
    indexer()