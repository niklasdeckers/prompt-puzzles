import base64
import json
import os
import urllib.error

import numpy as np
import openai
import requests


def get_generated_images(prompt, num_images=1, seed=-1):
    if seed == -1:
        seed = np.random.randint(100000000)

    urls = []
    if os.environ.get('TXT2IMG_BACKEND_URLS'):
        urls += json.loads(os.environ.get('TXT2IMG_BACKEND_URLS'))
    if os.environ.get('TXT2IMG_BACKEND_URL'):
        urls.append(os.environ.get('TXT2IMG_BACKEND_URL'))

    r = None
    for url in urls:
        backend_url = url + "/backend"
        try:
            r = requests.post(backend_url, json={"text": prompt, "num_images": num_images,
                                                 "seed": seed})
            if r.status_code == 200:
                r_json = r.json()
                images = r_json["generatedImgs"]
                images = [base64.b64decode(img) for img in images]
                return images
        except requests.ConnectionError:
            continue
    if r:
        raise urllib.error.URLError(f"Error {r.status_code} while fetching network results")
    else:
        raise ValueError("No valid backend URL specified")


def get_gpt3_response(prompt):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0.7,  # todo maybe determinism (i.e. temperature=0.0) is desirable?
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    return response["choices"][0]["text"]
