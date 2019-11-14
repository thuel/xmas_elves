"""
Module providing user input verification methods.
Ev. work with https://github.com/nicr9/pydialog (fork it and bump it to pyhton 3)
"""

def yes_or_no(question, default="no"):
    """
    Returns True if question is answered with yes else False.

    default: by default False is returned if there is no input.
    """
    answers = "yes|[no]" if default == "no" else "[yes]|no"
    prompt = "{} {}: ".format(question, answers)
    while True:
        answer = input(prompt).lower()
        if answer == '':
            answer = default
        if answer in ['no', 'n']:
            return False
        elif answer in ['yes', 'y']:
            return True

