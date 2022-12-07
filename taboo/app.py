import re
from argparse import ArgumentParser
from functools import partial

import pywebio as pw
import pywebio.input as pwi
import pywebio.output as pwo
import pywebio.pin as pin

from util import get_generated_images

task_data = [  # todo use examples from the real taboo game? https://boardgamegeek.com/image/131988/taboo-quick-draw
    ("dog", ["dog", "woof", "hound"], "a dog"),
    ("cat", ["cat", "meow"], "a cat"),
    ("evil old witch with a hat", ["witch", "cat", "broom stick"], "a witch"),
    ("zebra", ["zebra", "stripe", "africa"], "a zebra"),
]


def split_words(phraselist):
    return [word for phrase in phraselist for word in phrase.split(" ")]


def wrap_prompt(guess):
    return f"{guess} in front of a gray background, studio image photography"


def detect_invalid(prompt):  # todo dictionary constraint to disallow nsfw prompts? maybe check using gpt?
    if not (2 <= len(prompt) < 20):
        return True
    if re.search(r"[^a-zA-Z0-9 -]", prompt):
        return True
    if len(re.findall(r" ", prompt)) >= 2:
        return True
    return False


def remove_repetitions(w):  # prevents cheats like "cat vs. caat"
    return "".join([a for (i, a) in enumerate(w) if not (" " + w)[i] == a])


def detect_fault(prompt: str, taboo_list):
    for taboo in taboo_list:
        if remove_repetitions(taboo) in remove_repetitions(prompt):
            return True
    return False


def check_form(data, taboo_list):
    if not data["guess"]:
        return ("guess", "Please give a description.")
    if detect_invalid(data["guess"]):
        return ("guess", "Only short one or two word descriptions are allowed.")
    if detect_fault(data["guess"], taboo_list):
        return ("guess", f"You may not use any of the following words: {', '.join(taboo_list)}")


def main():
    pwo.put_markdown("""
    # Taboo 🤫

    - You are given an image that shows an certain object.
    - Try to identify the object and describe it with a short term.
    - The software will then generate an image for your description. The more it matches the original image, the better!
    - However, your description may not contain the taboo words listed below.
    ---
    """)
    pwo.put_row([
        pwo.put_column([
            pwo.put_scope('target'),
            pwo.put_scope('instructions'),
        ], size="auto"),
        pwo.put_scrollable(pwo.put_scope('scrollable'), height=600)])

    for prompt_groundtruth, taboo_list, verification_groundtruth in task_data:  # loop of multiple games
        pwo.clear('scrollable')
        pwo.clear('instructions')
        counter = 0

        with pwo.use_scope('target', clear=True):
            with pwo.put_loading():
                pwo.put_image(get_generated_images(wrap_prompt(prompt_groundtruth), seed=42)[0])

        with pwo.use_scope('instructions', clear=True):
            pwo.put_text(
                f"You may not use any of the following words: \n{', '.join(taboo_list)}")

        while True:  # game loop

            with pwo.use_scope('input'):
                data = pwi.input_group("Your description", [
                    pwi.input('', name='guess', value=""),
                    pwi.actions(name='submit', buttons=['Submit'])
                ], validate=partial(check_form, taboo_list=split_words(taboo_list)))

            guess = data['guess']
            prompt = wrap_prompt(guess)

            counter += 1

            with pwo.use_scope('scrollable'):
                pwo.put_html("<hr>", position=0)
                with pwo.put_loading(position=0):
                    pwo.put_column([
                        pwo.put_image(get_generated_images(prompt, seed=42)[0]),
                        pwo.put_text(f"\nAttempt {counter}:\n{guess}"),
                    ], size="auto", position=0)

            if pwi.actions('Are you happy with the result?', ['yes', 'no, try again']) == "yes":
                break

        with pwo.popup("Decide!", closable=False) as s:
            with pwo.put_loading():
                pwo.put_column([
                    pwo.put_image(get_generated_images(prompt, seed=43)[0]),
                    # using a different seed to verify generalization
                    pwo.put_text(f"Does this image show {verification_groundtruth}?"),
                    pin.put_actions(name="decision", buttons=["yes", "no"])
                ], size="auto")

        pin.pin_wait_change("decision")

        if pin.pin["decision"] == "yes":
            with pwo.popup("Great job!", closable=False) as s:
                pwo.put_column([
                    pwo.put_text("You managed to identify and recreate the content of the given image."),
                    pin.put_actions(name="continue", buttons=["Start next round"])
                ], size="auto")
        else:
            with pwo.popup("What a pitty!", closable=False) as s:
                pwo.put_column([
                    pwo.put_text(
                        "You didn't manage to identify and recreate the content of the given image this time."),
                    pin.put_actions(name="continue", buttons=["Start next round"])
                ], size="auto")

        pin.pin_wait_change("continue")
        pwo.close_popup()

    with pwo.popup("Finished!", closable=False) as s:
        pwo.put_text("You completed the final puzzle. Thanks for participating!")


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--port", dest="port",
                        help="Port under which the app will be running", default=8081)
    args = parser.parse_args()

    pw.start_server(main, port=args.port, debug=True)
