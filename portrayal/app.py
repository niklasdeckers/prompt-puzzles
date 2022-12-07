from argparse import ArgumentParser

import pywebio as pw
import pywebio.output as pwo
import pywebio.pin as pin

from util import get_generated_images

# todo also add ad-hoc experiment where you only have 1 try

task_data = [
    ("Malerischer Eiffelturm",
     "malerischer_eiffelturm.png",
     ["Auf dem Gemälde sind genau zwei Wolken zu sehen.",
      "Auf der linken Seite des Eiffelturms sind mehr Bäume als auf der rechten Seite.",
      "Genau eines der Ohren des Malers ist sichtbar.",
      "Der Maler trägt einen Hut.",
      "Auf dem Hemd des Malers sind Streifen.",
      "Der Mund des Malers ist geöffnet.",
      "Der Maler hält einen Pinsel.",
      "Die Staffelei hat genau drei Beine.",
      "Auf der Palette des Malers sind mindestens vier Farben zu sehen.",
      "Der Maler hat einen Schnurrbart."]),
    ("PC User",
     "pc_user.png",
     ["Die Tastatur des Computers ist zu sehen.",
      "Mindestens vier der Finger des Teufelchens sind sichtbar.",
      "Der Schwanz des Teufelchens ist sichtbar.",
      "An den Füßen oder Hufen des Teufelchens sind genau zwei Klauen sichtbar.",
      "Die Hörner des Teufelchens sind näher am oberen Bildrand als der Computer.",
      "Ein Kabel verbindet den Monitor mit dem Computer.",
      "Das Teufelchen hat eine spitze Nase und spitze Ohren.",
      "Das Teufelchen lächelt.",
      "Der Stuhl, auf dem das Teufelchen sitzt, hat weder zwei noch vier Beine.",
      "Das Teufelchen hat einen Spitzbart."]),
    ("Nahrungskette",
     "nahrungskette.png",
     ["Es ist genau ein Auge des Fisches sichtbar.",
      "Auf dem Kopf des Mannes sind keine Haare zu sehen.",
      "Der Kopf des Fisches ist näher an der Wasseroberfläche als das Seegras.",
      "Die Sonne steht links des Mannes.",
      "Der Fisch befindet sich links des Tisches.",
      "Die Gabel, die der Fisch hält, hat genau drei Zinken.",
      "Der Wurm ist auf einem Haken, der seinerseits mit einer Leine an der Angel befestigt ist.",
      "Sowohl beim Tisch als auch beim Stuhl sind genau zwei Beine sichtbar.",
      "Der Mann im Boot schaut auf die rechte Seite des Bildes.",
      "Auf dem Fischkörper sind mindestens fünf Schuppen zu sehen."])

]


def wrap_prompt(prompt):
    return f"{prompt}"  # currently, no wrapping is applied


def check_form(data):
    if not data["guess"]:
        return ("guess", "Please give a description.")
    # todo add nsfw check?


def main():
    pwo.put_markdown("""
    # Portrayal 🎨

    - Try to describe the given image using a prompt.
    - The software will then generate an image from your prompt. The more it matches the original image, the better!
    ---
    """)
    pwo.put_row([
        pwo.put_scope('target'),
        pwo.put_scrollable(pwo.put_scope('scrollable'), height=600)])

    for title, filename, verification_groundtruth in task_data:  # loop of multiple games
        pwo.clear('scrollable')
        counter = 0

        with pwo.use_scope('target', clear=True):
            pwo.put_image(open(f"data/{filename}", 'rb').read())

        with pwo.use_scope('input', clear=True):
            pwo.put_markdown("""
            ## Your prompt
            Please enter your prompt and submit it for preview to see the result. You may then modify the prompt again. 
            Once you are happy with the result, submit it definitively to have it evaluated.
            """)
            placeholder = "a man, black and white cartoon drawing on a white background"
            pin.put_textarea(name="guess", placeholder=placeholder, value=placeholder)
            previously_preliminary = False

            def put_buttons(preliminary=True):
                nonlocal previously_preliminary
                if not (previously_preliminary and preliminary):
                    with pwo.use_scope('buttons', clear=True):
                        pin.put_actions(name='submit', buttons=[{"label": 'Submit for preview',
                                                                 "value": 'submit1',
                                                                 "disabled": not preliminary,
                                                                 },
                                                                {
                                                                    "label": 'Submit definitively (I am happy with my results)',
                                                                    "value": 'submit2',
                                                                    "disabled": preliminary,
                                                                }
                                                                ])
                previously_preliminary = preliminary

            put_buttons()
            pin.pin_on_change(name='guess', onchange=lambda _: put_buttons(), clear=True)

        while True:  # game loop

            while True:  # until the user submits valid input
                pin.pin_wait_change("submit")
                feedback = check_form(pin.pin)
                if feedback is None:
                    break
                else:
                    pwo.popup(title="Error!", content=feedback[1])

            guess = pin.pin['guess']
            prompt = wrap_prompt(guess)

            if pin.pin["submit"] == "submit2":
                break  # definitive submission

            counter += 1

            with pwo.use_scope('scrollable'):
                pwo.put_html("<hr>", position=0)
                with pwo.put_loading(position=0):
                    pwo.put_column([
                        pwo.put_image(get_generated_images(prompt, seed=42)[0]),  # todo maybe use random seed here?
                        pwo.put_text(f"\nAttempt {counter}:\n{guess}"),
                    ], size="auto", position=0)

            put_buttons(preliminary=False)

        with pwo.popup("Decide!", closable=False) as s:
            with pwo.put_loading():
                pwo.put_column([
                    pwo.put_image(get_generated_images(prompt, seed=43)[0]),
                    # using a different seed to verify generalization
                    pwo.put_markdown("""
                    ---
                    Please tick all statements that are correct regarding the image above. 
                    """),
                    pin.put_checkbox(name="choices",
                                     options=[(question, i) for i, question in enumerate(verification_groundtruth)]),
                    pin.put_actions(name="done", buttons=["Done"])
                ], size="auto")

        pin.pin_wait_change("done")

        with pwo.popup("Thanks!", closable=False) as s:
            pwo.put_column([
                pwo.put_text(f"You managed to recreate the given image by "
                             f"{len(pin.pin['choices'])} of {len(verification_groundtruth)} criteria."),
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
