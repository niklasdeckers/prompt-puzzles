import re
from argparse import ArgumentParser

import pywebio as pw
import pywebio.input as pwi
import pywebio.output as pwo

from util import get_generated_images, get_gpt3_response


def check_form(data):  # todo also impose length constraints, and singleline constraints
    err_msg = "Please make a guess."
    if not data["guess"]:
        return ("guess", err_msg)


def verify_guess(groundtruth, A, B):  # todo remove
    gpt3_prompt = f"""What is closer to "{groundtruth}"?
1: "{A}"
2: "{B}"
Answer:"""
    response = get_gpt3_response(gpt3_prompt)
    m = re.search('[1-2]', response)
    if m:
        if m[0] == "1":
            return A
        elif m[0] == "2":
            return B
    return None  # model is confused


def evolve_image(groundtruth, history):
    best = history[-1]["guess"]
    if best:
        image_prompt = f"{best} (pencil drawing)"
    else:
        image_prompt = "confused questionmark"
    return image_prompt


def check_win(groundtruth, history):
    gpt3_prompt = f"""Are these things the same?
1: {history[-1]["guess"]}
2: {groundtruth}
Answer (yes/no):"""
    response = get_gpt3_response(gpt3_prompt)
    m = re.search('yes', response, re.IGNORECASE)
    if m:
        return True
    return False


def main():
    pwo.put_markdown("""
    # dalle-guesser 🧐
    
    I'm thinking of something specific. Can you guess what?
    """)
    pwo.put_scrollable(pwo.put_scope('scrollable'), height=400, keep_bottom=True)
    pwo.put_scope('counter')

    while True:  # loop of multiple games

        groundtruth = "happy poodle"  # todo random selection
        # todo riddle of the day

        pwo.clear('scrollable')
        history = []

        pwo.clear('counter')
        counter = 0

        while True:  # game loop

            with pwo.use_scope('input'):
                data = pwi.input_group("Your next guess", [
                    pwi.input('You are thinking about...', name='guess', value=None if history else "something large"),
                ], validate=check_form)

            guess = data['guess']

            query = f"{guess}?"

            history.append({"guess": guess})

            image_prompt = evolve_image(groundtruth, history)

            counter += 1
            with pwo.use_scope('counter', clear=True):
                pwo.put_text(f"Guess counter: {counter}")

            with pwo.use_scope('scrollable'):
                with pwo.put_loading():
                    pwo.put_row([
                        pwo.put_text(query),
                        pwo.put_image(get_generated_images(image_prompt)[0])
                    ])

            if check_win(groundtruth, history):
                with pwo.use_scope('counter', clear=True):
                    pwo.put_text(f"You did it! You won within {counter} guesses!\nI was thinking about {groundtruth}:")
                    with pwo.put_loading():
                        pwo.put_image(get_generated_images(groundtruth)[0])
                break

        pwi.actions('', ['Start new game'])


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--port", dest="port",
                        help="Port under which the app will be running", default=8081)
    args = parser.parse_args()

    pw.start_server(main, port=args.port, debug=True)
