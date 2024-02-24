import requests
import json
import io
import base64
from PIL import Image, PngImagePlugin
import logging
import uuid
import datetime
import base64
from .globals import LOGLEVEL

logging.basicConfig(level=LOGLEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

class StableDiffusion:
    def __init__(self, url):
        self.name="Stable Diffusion"
        self.url = url


    def generate_image(self, prompt, height="512", width="512", username=""):
        '''
        Generates an image from a prompt.
        Returns the raw data of the image and the pnginfo.
        '''

        endpoint = "/sdapi/v1/txt2img"

        fixed_prompt = " 8k, high-resolution, photorealistic"
        fixed_negative_prompt = "low-resolution, pixelated, blurry, bad quality, distorted, many fingers, many limbs, misshapen body, weird face, distorted face, ugly"

        payload = {
            "prompt": prompt+fixed_prompt,
            "negative_prompt": fixed_negative_prompt,
            "steps": 150,
            "width": 512,
            "height": 512,
            "refiner_checkpoint": "lrmLiangyiusRealistic_v15.safetensors",
            "refiner_switch_at": 0.85,
        }

        logging.debug(f"Payload: {payload}")

        response = requests.post(url=f'{self.url}{endpoint}', json=payload)
        r = response.json()
        for i in r['images']:
            image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))
            # image = BytesIO()
            logging.debug(f"Image: created")
            png_payload = {
                "image": "data:image/png;base64," + i
            }
            r2 = requests.post(url=f'{self.url}/sdapi/v1/png-info', json=png_payload)
            logging.debug("got png info")
            pnginfo = PngImagePlugin.PngInfo()
            pnginfo.add_text("parameters", r2.json().get("info"))

            filename = uuid.uuid4().hex
            image.save(f"../images/{filename}.png", pnginfo=pnginfo)

            # Save caption and image name as csv 
            with open("../images/log.csv", "a") as f:
                date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{date},{username},new,{prompt},{filename}.png\n")

            return(f"{filename}.png")

    def generate_image_variation(self, image, height="512", width="512", username="", prompt=""):
        '''
        Generates an image variation from an image using a prompt.
        Returns the raw data of the image and the pnginfo.
        '''

        endpoint = "/sdapi/v1/img2img"

        fixed_negative_prompt = "low-resolution, pixelated, blurry, bad quality, distorted, many fingers, many limbs, misshapen body, weird face, distorted face, ugly"

        base64_string = base64.b64encode(image).decode('utf-8')

        payload = {
            "prompt": prompt,
            "negative_prompt": fixed_negative_prompt,
            "init_images": [base64_string],
            "steps": 150,
            "width": 512,
            "height": 512,
            "refiner_checkpoint": "lrmLiangyiusRealistic_v15.safetensors",
            "refiner_switch_at": 0.85,
        }

        response = requests.post(url=f'{self.url}{endpoint}', json=payload)
        r = response.json()
        for i in r['images']:
            image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))
            # image = BytesIO()
            logging.debug(f"Image: created")
            png_payload = {
                "image": "data:image/png;base64," + i
            }
            r2 = requests.post(url=f'{self.url}/sdapi/v1/png-info', json=png_payload)
            logging.debug("got png info")
            pnginfo = PngImagePlugin.PngInfo()
            pnginfo.add_text("parameters", r2.json().get("info"))

            filename = uuid.uuid4().hex
            image.save(f"../images/{filename}.png", pnginfo=pnginfo)

            # Save caption and image name as csv 
            with open("../images/log.csv", "a") as f:
                date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{date},{username},variation,{prompt},{filename}.png\n")

            return(f"{filename}.png")