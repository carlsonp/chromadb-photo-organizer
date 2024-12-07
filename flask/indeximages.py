import os
import subprocess
from pathlib import Path

import chromadb
import torch
from chromadb.utils.data_loaders import ImageLoader
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor
from utility import convertVideoFormat, get_imgs, get_videos


def threaded_index(lock, app, socketio):
    try:
        lock.acquire()

        if (
            os.environ.get("ORGANIZE_FILES")
            and os.environ.get("ORGANIZE_FILES").lower() == "true"
        ):
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

            app.logger.info("Running detox...")
            detox_results = subprocess.run(
                "detox -r -v /static/images/", capture_output=True, shell=True
            )
            app.logger.info(detox_results)

            socketio.emit("update_progress", {"progress": f"Finished organizing files"})
            app.logger.info("Finished organizing files")

        if (
            os.environ.get("CONVERT_GIF_TO_MP4")
            and os.environ.get("CONVERT_GIF_TO_MP4").lower() == "true"
        ):
            app.logger.info("Converting GIF files to MP4...")
            convertVideoFormat(
                app,
                "*.[gG][iI][fF$]",
                ".gif",
                ".mp4",
                "-movflags faststart -pix_fmt yuv420p -vf 'scale=trunc(iw/2)*2:trunc(ih/2)*2'",
                bool(os.environ.get("DELETE_GIF_AFTER_CONVERSION")),
            )
            socketio.emit(
                "update_progress", {"progress": f"Finished converting GIF to MP4"}
            )

        if (
            os.environ.get("CONVERT_GIF_TO_WEBM")
            and os.environ.get("CONVERT_GIF_TO_WEBM").lower() == "true"
        ):
            app.logger.info("Converting GIF files to WEBM...")
            convertVideoFormat(
                app,
                "*.[gG][iI][fF$]",
                ".gif",
                ".webm",
                "-movflags faststart -pix_fmt yuv420p -vf 'scale=trunc(iw/2)*2:trunc(ih/2)*2'",
                bool(os.environ.get("DELETE_GIF_AFTER_CONVERSION")),
            )
            socketio.emit(
                "update_progress", {"progress": f"Finished converting GIF to WEBM"}
            )

        if (
            os.environ.get("CONVERT_WEBM_TO_MP4")
            and os.environ.get("CONVERT_WEBM_TO_MP4").lower() == "true"
        ):
            app.logger.info("Converting WEBM files to MP4...")
            convertVideoFormat(
                app,
                "*.[wW][eE][bB][mM$]",
                ".webm",
                ".mp4",
                "",
                bool(os.environ.get("DELETE_WEBM_AFTER_CONVERSION")),
            )
            socketio.emit(
                "update_progress", {"progress": f"Finished converting WEBM to MP4"}
            )

        if (
            os.environ.get("CONVERT_MP4_TO_WEBM")
            and os.environ.get("CONVERT_MP4_TO_WEBM").lower() == "true"
        ):
            app.logger.info("Converting MP4 files to WEBM...")
            convertVideoFormat(
                app,
                "*.[mM][pP][4$]",
                ".mp4",
                ".webm",
                "",
                bool(os.environ.get("DELETE_MP4_AFTER_CONVERSION")),
            )
            socketio.emit(
                "update_progress", {"progress": f"Finished converting MP4 to WEBM"}
            )

        app.logger.info("Extracting images from video files...")
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
                app.logger.info(process_results)
            if _i % 100 == 0:
                socketio.emit(
                    "update_progress",
                    {"progress": f"Extracting images from video files... {_i}"},
                )
        socketio.emit(
            "update_progress",
            {"progress": f"Finished extracting images from video files"},
        )

        client = chromadb.HttpClient(host="chromadb", port=8000)

        embedding_function = OpenCLIPEmbeddingFunction()
        image_loader = ImageLoader()

        collection = client.get_or_create_collection(
            name="chromadb-photo-organizer",
            embedding_function=embedding_function,
            data_loader=image_loader,
        )

        existingids = collection.get(include=[])
        app.logger.info(f"Existing indexed images: {len(existingids['ids'])}")

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

        app.logger.info(f"Adding {len(ids)} images")
        i = 0
        batchamount = 100
        while i < len(ids):
            app.logger.info(f"adding {i} - {i+batchamount}")
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
                app.logger.info(
                    f"Removing image: {img} from ChromaDB as it no longer exists on disk"
                )
                collection.delete(ids=[img])
            if not Path(img.removesuffix(".png")).is_file():
                app.logger.info(
                    f"Removing image: {img.removesuffix('.png')} from ChromaDB as it no longer exists on disk"
                )
                collection.delete(ids=[img.removesuffix(".png")])
        socketio.emit("update_progress", {"progress": f"Finished ChromaDB cleanup"})

        if (
            os.environ.get("GENERATE_CAPTIONS")
            and os.environ.get("GENERATE_CAPTIONS").lower() == "true"
        ):
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

            # https://huggingface.co/microsoft/Florence-2-large
            model = AutoModelForCausalLM.from_pretrained(
                "microsoft/Florence-2-large",
                torch_dtype=torch_dtype,
                trust_remote_code=True,
            ).to(device)
            processor = AutoProcessor.from_pretrained(
                "microsoft/Florence-2-large", trust_remote_code=True
            )

            def generateCaption(image_path, text_input=None):
                if text_input is None:
                    prompt = os.environ.get("CAPTION_PROMPT")
                else:
                    prompt = os.environ.get("CAPTION_PROMPT") + text_input

                try:
                    image = Image.open(image_path)

                    inputs = processor(
                        text=prompt, images=image, return_tensors="pt"
                    ).to(device, torch_dtype)
                    generated_ids = model.generate(
                        input_ids=inputs["input_ids"],
                        pixel_values=inputs["pixel_values"],
                        max_new_tokens=1024,
                        num_beams=3,
                    )
                    generated_text = processor.batch_decode(
                        generated_ids, skip_special_tokens=False
                    )[0]

                    parsed_answer = processor.post_process_generation(
                        generated_text,
                        task=os.environ.get("CAPTION_PROMPT"),
                        image_size=(image.width, image.height),
                    )
                    return str(parsed_answer[os.environ.get("CAPTION_PROMPT")])
                except Exception as e:
                    app.logger.error(f"Error: {e}")
                    app.logger.error(f"Issue with: {image_path}")
                    return ""

            app.logger.info("Adding captions to images...")
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
                    # app.logger.info(f"Adding caption for image: {metadata['relative_path']}, caption: {upsertmetadata['caption']}")
                    new_percentage = round(
                        (_i / len(imagecaptionscheck["metadatas"])) * 100
                    )
                    # only emit when we have a percentage tick over
                    if new_percentage > lastpercentagesent + 1:
                        socketio.emit(
                            "update_progress",
                            {"progress": f"Adding captions... {new_percentage}%"},
                        )
                        lastpercentagesent = new_percentage
            app.logger.info("Finished adding captions to images")
            socketio.emit(
                "update_progress", {"progress": f"Finished adding captions to images"}
            )

        app.logger.info("Finished indexing images")
        socketio.emit("update_progress", {"progress": f"Finished indexing images"})
        lock.release()
    except Exception as e:
        app.logger.error(f"Error: {e}")
