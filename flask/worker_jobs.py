import os
import subprocess
from pathlib import Path

import chromadb
import torch
from chromadb.utils.data_loaders import ImageLoader
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from utility import convertVideoFormat, get_imgs, get_videos


def organize_files():
    try:
        # remove some bad characters from filenames
        for replaceme in [",", "%"]:
            for f in list(get_videos("/static/images", [])) + list(
                get_imgs("/static/images", [])
            ):
                if replaceme in f:
                    os.rename(f, f.replace(replaceme, ""))

        # rename jpeg to jpg
        for f in list(get_imgs("/static/images", [], ["*.[jJ][pP][eE][gG$]"])):
            if f.lower().endswith(".jpeg"):
                name, old_extension = f.rsplit(".", 1)
                os.rename(f, name + "." + "jpg")

        print("Running detox...")
        detox_results = subprocess.run(
            "detox -r -v /static/images/", capture_output=True, shell=True
        )
        print(detox_results)

        print("Finished organizing files")
    except Exception as e:
        print(f"Error: {e}")

def convert_gif_to_mp4():
    try:
        print("Converting GIF files to MP4...")
        convertVideoFormat(
            "*.[gG][iI][fF$]",
            ".gif",
            ".mp4",
            "-movflags faststart -pix_fmt yuv420p -vf 'scale=trunc(iw/2)*2:trunc(ih/2)*2'",
            bool(os.environ.get("DELETE_GIF_AFTER_CONVERSION")),
        )
        print("Finished converting GIF to MP4")
    except Exception as e:
        print(f"Error: {e}")

def convert_gif_to_webm():
    try:
        print("Converting GIF files to WEBM...")
        convertVideoFormat(
            "*.[gG][iI][fF$]",
            ".gif",
            ".webm",
            "-movflags faststart -pix_fmt yuv420p -vf 'scale=trunc(iw/2)*2:trunc(ih/2)*2'",
            bool(os.environ.get("DELETE_GIF_AFTER_CONVERSION")),
        )
        print("Finished converting GIF to WEBM")
    except Exception as e:
        print(f"Error: {e}")

def convert_webm_to_mp4():
    try:
        print("Converting WEBM files to MP4...")
        convertVideoFormat(
            "*.[wW][eE][bB][mM$]",
            ".webm",
            ".mp4",
            "",
            bool(os.environ.get("DELETE_WEBM_AFTER_CONVERSION")),
        )
        print("Finished converting WEBM to MP4")
    except Exception as e:
        print(f"Error: {e}")

def convert_mp4_to_webm():
    try:
        print("Converting MP4 files to WEBM...")
        convertVideoFormat(
            "*.[mM][pP][4$]",
            ".mp4",
            ".webm",
            "",
            bool(os.environ.get("DELETE_MP4_AFTER_CONVERSION")),
        )
        print("Finished converting MP4 to WEBM")
    except Exception as e:
        print(f"Error: {e}")

def extract_images_videos():
    try:
        print("Extracting images from video files...")
        for _i, vid in enumerate(get_videos("/static/images", [])):
            if not Path(f"{vid}.png").is_file():
                if vid.lower().endswith(".gif"):
                    process_results = subprocess.run(
                        f"convert '{vid}[0]' {vid}.png", capture_output=True, shell=True
                    )
                else:
                    # webm, mp4, etc.
                    process_results = subprocess.run(
                        f"ffmpeg -i {vid} -hide_banner -loglevel error -vf 'select=eq(n,0)' -vframes 1 {vid}.png",
                        capture_output=True,
                        shell=True,
                    )
                print(process_results)
            if _i % 100 == 0:
                print(f"Extracting images from video files... {_i}")
        print("Finished extracting images from video files")

        client = chromadb.HttpClient(host="chromadb", port=8000)

        embedding_function = OpenCLIPEmbeddingFunction()
        image_loader = ImageLoader()

        collection = client.get_or_create_collection(
            name="chromadb-photo-organizer",
            embedding_function=embedding_function,
            data_loader=image_loader,
        )

        existingids = collection.get(include=[])
        print(f"Existing indexed images: {len(existingids['ids'])}")

        image_uris = []
        for img in get_imgs("/static/images/", existingids["ids"]):
            image_uris.append(img)

        metadatas = []
        for p in image_uris:
            # add gif/video to the metadata path if the file exists, otherwise the static image
            if Path(p.removesuffix(".png")).is_file():
                animated_path = p.removesuffix(".png")
                metadatas.append(
                    {
                        "relative_path": animated_path,
                        "favoritecount": 0,
                        "tags": "",
                        "caption": "",
                    }
                )
            else:
                metadatas.append(
                    {"relative_path": p, "favoritecount": 0, "tags": "", "caption": ""}
                )

        ids = image_uris

        print(f"Adding {len(ids)} images")
        i = 0
        batchamount = 100
        while i < len(ids):
            print(f"adding {i} - {i+batchamount}")
            if i + batchamount > len(ids):
                collection.add(
                    ids=ids[i : len(ids)],
                    uris=image_uris[i : len(ids)],
                    metadatas=metadatas[i : len(ids)],
                )
                break
            else:
                collection.add(
                    ids=ids[i : i + batchamount],
                    uris=image_uris[i : i + batchamount],
                    metadatas=metadatas[i : i + batchamount],
                )
            i = i + batchamount

        # delete images from ChromaDB that no longer exist on disk
        metadatacleanup = collection.get(include=[])
        for img in metadatacleanup["ids"]:
            if not Path(img).is_file():
                print(f"Removing image: {img} from ChromaDB as it no longer exists on disk")
                collection.delete(ids=[img])
            if not Path(img.removesuffix(".png")).is_file():
                print(f"Removing image: {img.removesuffix('.png')} from ChromaDB as it no longer exists on disk")
                collection.delete(ids=[img.removesuffix(".png")])
        print("Finished ChromaDB cleanup")
    except Exception as e:
        print(f"Error: {e}")

def generate_captions():
    try:
        client = chromadb.HttpClient(host="chromadb", port=8000)

        embedding_function = OpenCLIPEmbeddingFunction()
        image_loader = ImageLoader()

        collection = client.get_or_create_collection(
            name="chromadb-photo-organizer",
            embedding_function=embedding_function,
            data_loader=image_loader,
        )

        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        # https://huggingface.co/microsoft/Florence-2-large
        # https://huggingface.co/Salesforce/blip-image-captioning-base
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)

        def generateCaption(image_path):
            try:
                image = Image.open(image_path).convert("RGB")
                inputs = processor(images=image, return_tensors="pt").to(device)
                out = model.generate(**inputs)
                caption = processor.decode(out[0], skip_special_tokens=True)

                return str(caption)
            except Exception as e:
                print(f"Error: {e}")
                print(f"Issue with: {image_path}")
                return ""

        print("Adding captions to images...")
        # add captions for each image that is missing a caption
        imagecaptionscheck = collection.get(include=["metadatas"])
        lastpercentagesent = 0
        for _i, metadata in enumerate(imagecaptionscheck["metadatas"]):
            if "caption" not in metadata or metadata["caption"] == "":
                upsertmetadata = metadata
                upsertmetadata["caption"] = generateCaption(
                    metadata["relative_path"]
                )
                collection.update(
                    ids=[metadata["relative_path"]], metadatas=[upsertmetadata]
                )
                # print(f"Adding caption for image: {metadata['relative_path']}, caption: {upsertmetadata['caption']}")
                new_percentage = round(
                    (_i / len(imagecaptionscheck["metadatas"])) * 100
                )
                # only emit when we have a percentage tick over
                if new_percentage > lastpercentagesent + 1:
                    print(f"Adding captions... {new_percentage}%")
                    lastpercentagesent = new_percentage
        print("Finished adding captions to images")
    except Exception as e:
        print(f"Error: {e}")
