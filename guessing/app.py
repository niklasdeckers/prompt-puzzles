import re
from argparse import ArgumentParser

import pywebio as pw
import pywebio.input as pwi
import pywebio.output as pwo
import pywebio.pin as pin

from util import get_generated_images, get_gpt3_response

task_data = [  # todo use real examples from skribble?
    "birch",
    "gummy bear",
    "iphone",
    "hot dog",
    "pirate boat", ]


def split_words(phraselist):
    return [word for phrase in phraselist for word in phrase.split(" ")]


def wrap_prompt(guess):
    return f"{guess} in front of a gray background, studio image photography"


def detect_invalid(prompt):  # todo dictionary constraint to disallow nsfw prompts? maybe check using gpt?
    if not (2 <= len(prompt) < 20):
        return True
    if re.search(r"[^a-zA-Z0-9 -]", prompt):
        return True
    if len(re.findall(r" ", prompt)) >= 3:
        return True
    return False


def check_form(data):
    if not data["guess"]:
        return ("guess", "Please make a guess.")
    if detect_invalid(data["guess"]):
        return ("guess", "Only short one, two or three word guesses are allowed.")


def get_hierarchy(groundtruth):
    prompt = f'''This is a 3 step construction of the term "poodle":
1. animal
2. dog
3. poodle
"""
This is a 3 step construction of the term "{groundtruth}":'''
    response = get_gpt3_response(prompt)
    return [term.lower().strip() for term in re.findall(r"\d\. ([a-zA-Z\- ]+)", response)]
    # todo assert that it ends on groundtruth (best: remove in GPT logic and add later)


def get_position_in_hierarchy(guess, hierarchy):
    insertion = "\n".join([f"{i + 1}. {term}" for i, term in enumerate(reversed(hierarchy))])
    prompt = f'''The terms are:
1. poodle
2. dog
3. animal
Let's compare this to "pug".
1. Not every pug is a poodle.
2. Every pug is a dog.
3. Every pug is an animal.
"""
The terms are:
1. red dog
2. dog
3. animal
Let's compare this to "cat".
1. Not every cat is a red dog.
2. Not every cat is a dog.
3. Every cat is an animal.
"""
The terms are:
1. pug
2. dog
3. animal
Let's compare this to "car".
1. Not every car is a pug.
2. Not every car is a dog.
3. Not every car is an animal.
"""
The terms are:
{insertion}
Let's compare this to "{guess}".'''
    response = get_gpt3_response(prompt)
    term = re.search(r"(\d+)\. Every [^\.]+\.", response)
    if term is None:
        ind = -1  # this corresponds to "anything"
    else:
        try:
            ind = len(hierarchy) - int(term.group(1))
        except ValueError:
            ind = -1
    return ind


def put_dialog_message_bot(content):
    pwo.put_row([content, None], size='60% 40%')


def put_dialog_message_user(content):
    pwo.put_row([None, content], size='20% 80%')


def main():
    pwo.put_markdown("""
    # Guessing Golf 🧐
    
    I'm thinking of something specific. Can you guess what?
    """)
    pwo.put_scrollable(pwo.put_scope('scrollable'), height=800, keep_bottom=True)

    for groundtruth in task_data:  # loop of multiple games

        pwo.clear('scrollable')
        counter = 0

        hierarchy = get_hierarchy(groundtruth)
        current_prompt = hierarchy[0]  # initial prompt

        while True:  # game loop

            with pwo.use_scope('scrollable'):
                with pwo.put_loading():
                    imgs = get_generated_images(wrap_prompt(current_prompt), num_images=4)
                    put_dialog_message_bot(pwo.put_grid([[pwo.put_image(imgs[0]), None,
                                                          pwo.put_image(imgs[1])], [None, None, None],
                                                         [pwo.put_image(imgs[2]), None,
                                                          pwo.put_image(imgs[3])]], cell_widths="50% 10px 50%",
                                                        cell_heights="auto 10px auto"))

                # todo put encouraging random message?

            with pwo.use_scope('input'):
                data = pwi.input_group("Your next guess", [
                    pwi.input('', name='guess', value=""),
                    pwi.actions(name='submit', buttons=['Submit'])
                ], validate=check_form)  # todo also give default value?

            guess = data['guess']

            counter += 1

            with pwo.use_scope('scrollable'):
                put_dialog_message_user(pwo.put_html(
                    f'<div style="text-align: right"> Guess {counter}: <br> {guess} </div>'))  # todo escape

            pos = get_position_in_hierarchy(guess, hierarchy)

            if pos == len(hierarchy) - 1:
                with pwo.use_scope('scrollable'):
                    with pwo.put_loading():
                        img = get_generated_images(groundtruth)[0]
                        put_dialog_message_bot(pwo.put_column([
                            pwo.put_text(
                                f"You did it! You won within {counter} {'guess' if counter == 1 else 'guesses'}!\nI was thinking about {groundtruth}:"),
                            None,
                            pwo.put_image(img), None,
                            pin.put_actions(name="continue", buttons=["Start next round"])
                        ], size="auto"))

                break

            # if counter == 10:
            #    #todo add "you took too many attempts" popup.
            #    break

            current_prompt = hierarchy[pos + 1]

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
