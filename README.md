# Prompt Puzzles for Generative Text-To-Image Models 🧩💬🖌️🖼️

These puzzle games facilitate research about the interaction of users with generative text-to-image models like Stable
Diffusion when developing prompts.

## Setup

[PyWebIO](https://pywebio.readthedocs.io/) is used to deploy the website frontend and backend. The required Stable
Diffusion backend, which is accessed using `requests`,
is [part of the `stable-diffusion-playground`](https://github.com/niklasdeckers/stable-diffusion-playground/tree/main/backend).

The `index.py` script launches all available games.

The following environment variables must be set:

- `TXT2IMG_BACKEND_URL` is the url of the deployed `stable-diffusion-playground` backend, including port specification.
  Alternatively:
- `TXT2IMG_BACKEND_URLS` is a json list of such urls which will be used as fallbacks.
- `OPENAI_API_KEY` is a GPT-3 API key, which is used for some applications.

## Components

### [Taboo 🤫](taboo)

The user is asked to describe images while having to avoid some given terms. This is a scenario similar to query
obfuscation, where a user tries to query a search engine while not using certain terms.

### [Portrayal 🎨](portrayal)

The user is asked to recreate a given image using a Stable Diffusion prompt. This is a scenario similar to query
refinement. In the end, the generated image is evaluated using given criteria.

## Further Readings

Please see [our paper](https://doi.org/10.1145/3576840.3578327):

```
@InProceedings{deckers:2023a,
  author =                   {Niklas Deckers and Maik Fr\"obe and Johannes Kiesel and Gianluca Pandolfo and Christopher Schr\"oder and Benno Stein and Martin Potthast},
  booktitle =                {ACM SIGIR Conference on Human Information Interaction and Retrieval (CHIIR 2023)},
  doi =                      {10.1145/3576840.3578327},
  editor =                   {Jacek Gwizdka and Soo Young Rieh},
  month =                    mar,
  pages =                    {172--186},
  publisher =                {ACM},
  site =                     {Austin, TX, USA},
  title =                    {{The Infinite Index: Information Retrieval on Generative Text-To-Image Models}},
  url =                      {https://doi.org/10.1145/3576840.3578327},
  year =                     2023
}
```
