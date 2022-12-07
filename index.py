from argparse import ArgumentParser

import pywebio as pw
import pywebio.output as pwo

from portrayal.app import main as portrayal
from taboo.app import main as taboo


def index():
    pwo.put_markdown("""
    # Prompt Puzzles for Generative Text-To-Image Models<br>🧩💬🖌️🖼️

    These puzzle games facilitate research about the interaction of users with generative text-to-image models like Stable Diffusion when developing prompts.

    More information can be found in the [repository](https://github.com/niklasdeckers/prompt-puzzles).
    
    The following games are available:
    """)

    pwo.put_column([
        pwo.put_link('Taboo 🤫', app='taboo'),
        pwo.put_link('Portrayal 🎨', app='portrayal')
    ], size="auto").style("font-size")


def start_server(port):
    pw.start_server({"index": index,
                     "taboo": taboo,
                     "portrayal": portrayal},
                    port=port)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--port", dest="port",
                        help="Port under which the app will be running", default=8081)
    args = parser.parse_args()

    start_server(args.port)
