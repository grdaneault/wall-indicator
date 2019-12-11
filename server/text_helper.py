from math import floor, log10
from sigfig import round

SUFFIXES = [' ', 'k', 'M', 'B', 'T', 'Q']


def left_pad(s, target_length):
    return " " * (target_length - len(s)) + s


def num_to_sci(val, available_digits=4):
    if len(str(val).replace(".", "")) <= available_digits:
        return left_pad(str(val), available_digits)

    sf = round(val, available_digits - 1)

    index = 0 if val == 0 else floor(log10(sf) / 3)
    converted = sf / 10 ** (index * 3)
    if converted == int(converted):
        converted = int(converted)

    return left_pad(f'{converted}{SUFFIXES[index]}', available_digits)
