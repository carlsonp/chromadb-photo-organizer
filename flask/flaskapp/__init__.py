import os, glob, random
from flask import Flask, render_template, request
import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader
from threading import Thread
import threading
from indeximages import threaded_index
from PIL import Image
import numpy as np
from utility import get_imgs

# used for locking the index so we only run one at a time
lock = threading.Lock()

def create_app():
    app = Flask(__name__, instance_relative_config=True, static_folder='/home/carlsonp/src/chromadb-photo-organizer/static/')

    @app.route('/')
    def homepage():
        try:
            client = chromadb.HttpClient(host='192.168.1.112', port=8000)
            embedding_function = OpenCLIPEmbeddingFunction()
            collection = client.get_or_create_collection(name='chromadb-photo-organizer', embedding_function=embedding_function)

            return render_template('index.html', numberimages=collection.count())
        except Exception as e:
            app.logger.error(e)
    
    @app.route('/index')
    def index():
        try:
            if not lock.locked():
                thread = Thread(target=threaded_index, args=(lock,))
                thread.daemon = True
                thread.start()
                return render_template('index.html', textmessage="Started indexing images")
            else:
                return render_template('index.html', textmessage="Index already running")
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
            retrieved = collection.query(query_texts=[request.form.get('search')], include=['data', 'metadatas'], n_results=8)

            return render_template('results.html', ids=retrieved['ids'][0], imageuris=retrieved['uris'][0], metadatas=retrieved['metadatas'][0])

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
            retrieved = collection.query(query_images=[query_image], include=['data', 'metadatas'], n_results=8)

            return render_template('results.html', ids=retrieved['ids'][0], imageuris=retrieved['uris'][0], metadatas=retrieved['metadatas'][0])
        except Exception as e:
            app.logger.error(e)
    
    @app.route('/randomimages')
    def randomimages():
        try:
            client = chromadb.HttpClient(host='192.168.1.112', port=8000)
            embedding_function = OpenCLIPEmbeddingFunction()
            data_loader = ImageLoader()
            collection = client.get_or_create_collection(name='chromadb-photo-organizer', embedding_function=embedding_function, data_loader=data_loader)
            
            image_uris = []
            for img in get_imgs("/home/carlsonp/src/chromadb-photo-organizer/static/images/", []):
                image_uris.append(img)
            randomlyselected = random.sample(image_uris, 4)

            # https://docs.trychroma.com/usage-guide#querying-a-collection
            retrieved = collection.get(ids=randomlyselected, include=['metadatas'])

            return render_template('results.html', ids=retrieved['ids'], imageuris=retrieved['uris'], metadatas=retrieved['metadatas'])

        except Exception as e:
            app.logger.error(e)

    @app.route('/deleteindex')
    def deleteindex():
        # existing items don't seem to have metadata updated so in some cases it's easier just to blow it away
        try:
            client = chromadb.HttpClient(host='192.168.1.112', port=8000)
        except Exception as e:
            app.logger.error(e)
            return "Unable to connect to ChromaDB"
        try:
            client.delete_collection(name="chromadb-photo-organizer")
        except Exception as e:
            app.logger.warning(e)
            return "Index does not exist to delete"

        return render_template('index.html', textmessage="Index deleted")
    
    @app.route('/favorite')
    def favorite():
        try:
            # favorite images and see other images that are similar to it
            client = chromadb.HttpClient(host='192.168.1.112', port=8000)
            embedding_function = OpenCLIPEmbeddingFunction()
            collection = client.get_or_create_collection(name='chromadb-photo-organizer', embedding_function=embedding_function)

            # upvote or downvote if needed
            for t in ['downvote', 'upvote']:
                if request.args.get(t):
                    retrieved = collection.get(ids=[request.args.get(t)], include=['metadatas'])
                    if t == 'downvote':
                        retrieved['metadatas'][0]['favoritecount'] = retrieved['metadatas'][0]['favoritecount'] - 1
                    elif t == 'upvote':
                        retrieved['metadatas'][0]['favoritecount'] = retrieved['metadatas'][0]['favoritecount'] + 1
                    collection.update(ids=[request.args.get(t)], metadatas=retrieved['metadatas'])

            # figure out which image to load up
            if request.args.get('favorite'):
                img = request.args.get('favorite')
            elif request.args.get('upvote'):
                # get a similar image
                query_image = np.array(Image.open(request.args.get('upvote')))
                # return a few images since the first image is always the one searched for
                # we also don't want to get into a loop where the images are all completely
                # similar to one another so we add a little variability with randomness
                # in terms of the match score
                retrieved = collection.query(query_images=[query_image], include=['metadatas'], n_results=6)
                img = retrieved['ids'][0][random.randint(1, 5)]
            else:
                # randomly select an image if nothing is passed in or we downvoted an image
                image_uris = []
                for img in get_imgs("/home/carlsonp/src/chromadb-photo-organizer/static/images/", []):
                    image_uris.append(img)
                img = random.sample(image_uris, 1)[0]
            
            retrieved = collection.get(ids=[img], include=['metadatas'])

            return render_template('favorite.html', id=retrieved['ids'][0], imageuris=retrieved['uris'], metadatas=retrieved['metadatas'])
        except Exception as e:
            app.logger.error(e)

    return app