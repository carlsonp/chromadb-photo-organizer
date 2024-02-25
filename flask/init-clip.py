from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
# downloads open_clip_pytorch_model.bin file, ~600 MB
embedding_function = OpenCLIPEmbeddingFunction()
