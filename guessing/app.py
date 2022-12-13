import re
from argparse import ArgumentParser

import pywebio as pw
import pywebio.input as pwi
import pywebio.output as pwo
import pywebio.pin as pin

from util import get_generated_images, get_gpt3_response

task_data = [  # todo use real examples from skribble?
    "tree",
    "happy poodle",
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


def get_hierarchy(groundtruth):  # todo maybe use 3 steps instead of 5? makes it easier for the user.
    prompt = f'''This is a 5 step construction of the term "happy poodle":
1. living being
2. happy living being
3. happy animal
4. happy dog
5. happy poodle
"""
This is a 5 step construction of the term "{groundtruth}":'''
    response = get_gpt3_response(prompt)
    return [term.lower().strip() for term in re.findall(r"\d\. ([a-zA-Z\- ]+)", response)]
    # todo assert that it ends on groundtruth (best: remove in GPT logic and add later)


def get_position_in_hierarchy(guess, hierarchy):
    insertion = "\n".join([f"{i}. {term}" for i, term in enumerate(list(reversed(hierarchy)) + ["anything"])])
    prompt = f'''Given the following list of terms:
1. happy poodle
2. poodle
3. dog
4. animal
5. living being
6. anything
What is the first term that is not more specific than "cat"? Because every cat is an animal (4), but not every cat is a dog (3), and the former is directly behind the latter (4 minus 3 is one), this is
[animal]
"""
Given the following list of terms:
1. red dog
2. colored dog
3. colored animal
4. colored living being
5. living being
6. anything
What is the first term that is not more specific than "colored animal"? Because it itself is in the list, this is
[colored animal]
"""
Given the following list of terms:
{insertion}
What is the first term that is not more specific than "{guess}"? Because'''
    response = get_gpt3_response(prompt)
    term = re.search(r"\[([a-zA-Z\- ]+)\]", response).group(1).lower().strip()
    try:
        ind = hierarchy.index(term)
    except ValueError:
        ind = -1  # this corresponds to "anything"
    return ind


def put_dialog_message_bot(content):
    pwo.put_row([content, None], size='60% 40%')


def put_dialog_message_user(content):
    pwo.put_row([None, content], size='20% 80%')


def main():
    pwo.put_markdown("""
    # Guessing 🧐
    
    I'm thinking of something specific. Can you guess what?
    """)
    pwo.put_scrollable(pwo.put_scope('scrollable'), height=600, keep_bottom=True)

    for groundtruth in task_data:  # loop of multiple games

        pwo.clear('scrollable')
        counter = 0

        hierarchy = get_hierarchy(groundtruth)
        current_prompt = hierarchy[0]  # initial prompt

        while True:  # game loop

            with pwo.use_scope('scrollable'):
                with pwo.put_loading():
                    imgs = get_generated_images(wrap_prompt(current_prompt), seed=42, num_images=4)
                    put_dialog_message_bot(pwo.put_grid([[pwo.put_image(imgs[0]), None,
                                                          pwo.put_image(imgs[1])], [None, None, None],
                                                         [pwo.put_image(imgs[2]), None,
                                                          pwo.put_image(imgs[3])]], cell_widths="50% 10px 50%",
                                                        cell_heights="auto 10px auto"))

                # todo put encouraging random message?

            with pwo.use_scope('input'):  # todo include counter
                data = pwi.input_group("Your next guess", [
                    pwi.input('', name='guess', value=""),
                    pwi.actions(name='submit', buttons=['Submit'])
                ], validate=check_form)  # todo also give default value?

            guess = data['guess']

            # todo write down guess in chatlog with put_dialog_message_user

            counter += 1

            pos = get_position_in_hierarchy(guess, hierarchy)

            if pos == len(hierarchy) - 1:
                with pwo.use_scope('counter', clear=True):
                    pwo.put_text(
                        f"You did it! You won within {counter} guesses!\nI was thinking about {groundtruth}:")  # todo do as chatbox message; also the button in the chat
                    with pwo.put_loading():
                        pwo.put_image(get_generated_images(groundtruth)[0])
                break

                # todo recognize lack of progress and either alternate seed or tell the user that this is not helping.
                # todo what happens if we are too specific (more specific than groundtruth)? just accept, and give the user the groundtruth.

            # if counter == 10:
            #    #todo add "you took too many attempts" popup.
            #    break

            current_prompt = hierarchy[pos + 1]

        with pwo.popup("Thanks!", closable=False) as s:
            pwo.put_column([
                pwo.put_text(f"This puzzle is done."),  # todo include counter and groundtruth
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
