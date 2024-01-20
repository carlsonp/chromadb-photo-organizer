import os, glob, random
from flask import Flask, render_template, request
import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader
from threading import Thread
from indeximages import threaded_index
from PIL import Image
import numpy as np
from utility import get_imgs

def create_app():
    app = Flask(__name__, instance_relative_config=True, static_folder='/home/carlsonp/src/chromadb-photo-organizer/images/')

    @app.route('/')
    def homepage():
        try:
            return render_template('index.html')
        except Exception as e:
            app.logger.error(e)
    
    @app.route('/index')
    def index():
        try:
            # TODO: add ability to force a full index refresh via the URL
            # TODO: set lock so index can't be called again

            thread = Thread(target=threaded_index)
            thread.daemon = True
            thread.start()

            return "Started indexing images"
        except Exception as e:
            app.logger.error(e)
            return "Failure indexing"

    @app.route('/search', methods=['POST'])
    def search():
        try:
            client = chromadb.HttpClient(host='192.168.1.112', port=8000)
            embedding_function = OpenCLIPEmbeddingFunction()
            collection = client.get_or_create_collection(name='chromadb-photo-organizer', embedding_function=embedding_function)
            
            # https://docs.trychroma.com/usage-guide#querying-a-collection
            retrieved = collection.query(query_texts=[request.form.get('search')], include=['data', 'distances', 'metadatas'], n_results=6)
            print(retrieved)

            return render_template('results.html', ids=retrieved['ids'][0], imageuris=retrieved['uris'][0], metadatas=retrieved['metadatas'][0], distances=[ '%.3f' % elem for elem in retrieved['distances'][0] ])

        except Exception as e:
            app.logger.error(e)
    
    @app.route('/similar', methods=['POST'])
    def similar():
        try:
            # finds images that are similar to a provided image
            client = chromadb.HttpClient(host='192.168.1.112', port=8000)
            embedding_function = OpenCLIPEmbeddingFunction()
            collection = client.get_or_create_collection(name='chromadb-photo-organizer', embedding_function=embedding_function)

            query_image = np.array(Image.open(request.form.get('similar')))
            
            # https://docs.trychroma.com/usage-guide#querying-a-collection
            retrieved = collection.query(query_images=[query_image], include=['data', 'distances', 'metadatas'], n_results=6)
            print(retrieved)

            return render_template('results.html', ids=retrieved['ids'][0], imageuris=retrieved['uris'][0], metadatas=retrieved['metadatas'][0], distances=[ '%.3f' % elem for elem in retrieved['distances'][0] ])
        except Exception as e:
            app.logger.error(e)
    
    @app.route('/random')
    def randomimages():
        try:
            client = chromadb.HttpClient(host='192.168.1.112', port=8000)
            embedding_function = OpenCLIPEmbeddingFunction()
            data_loader = ImageLoader()
            collection = client.get_or_create_collection(name='chromadb-photo-organizer', embedding_function=embedding_function, data_loader=data_loader)
            
            image_uris = []
            for img in get_imgs("/home/carlsonp/src/chromadb-photo-organizer/images/", []):
                image_uris.append(img)
            randomlyselected = random.sample(image_uris, 6)

            # https://docs.trychroma.com/usage-guide#querying-a-collection
            retrieved = collection.get(ids=randomlyselected, include=['metadatas'])
            print(retrieved)

            return render_template('results.html', ids=retrieved['ids'], imageuris=retrieved['uris'], metadatas=retrieved['metadatas'], distances=None)

        except Exception as e:
            app.logger.error(e)

    return app