import base64
import os
import urllib.error

import openai
import requests


def get_dalle_images(prompt, num_images=1):
    backend_url = os.environ.get('DALLE_BACKEND_URL') + "/dalle"
    r = requests.post(backend_url, json={"text": prompt, "num_images": num_images})
    if r.status_code == 200:
        json = r.json()
        images = json["generatedImgs"]
        images = [base64.b64decode(img) for img in images]
        return images
    else:
        raise urllib.error.URLError(f"Error {r.status_code} while fetching DALLE results")


def get_gpt3_response(prompt):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    response = openai.Completion.create(
        model="text-davinci-002",
        prompt=prompt,
        temperature=0.7,  # todo maybe determinism (i.e. temperature=0.0) is desirable?
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    return response["choices"][0]["text"]
