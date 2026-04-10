import torch
from transformers import BlipForConditionalGeneration, BlipProcessor

device = "cuda:0" if torch.cuda.is_available() else "cpu"

# https://huggingface.co/Salesforce/blip-image-captioning-base
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-base"
).to(device)
