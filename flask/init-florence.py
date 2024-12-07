import torch
from transformers import AutoModelForCausalLM, AutoProcessor

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

# https://huggingface.co/microsoft/Florence-2-large
model = AutoModelForCausalLM.from_pretrained(
    "microsoft/Florence-2-large", torch_dtype=torch_dtype, trust_remote_code=True
).to(device)
processor = AutoProcessor.from_pretrained(
    "microsoft/Florence-2-large", trust_remote_code=True
)
