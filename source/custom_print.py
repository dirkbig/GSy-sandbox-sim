# Define a custom print function that either gives out every print or just shows the simulation progress.
normal_print = True


def cprint(msg_to_print):
    if normal_print:
        print(msg_to_print)

