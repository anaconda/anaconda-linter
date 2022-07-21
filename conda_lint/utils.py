import argparse
from collections import Counter
import os
from pathlib import Path
import tokenize

LICENSES = Path('conda_lint', 'data', 'licenses.txt')


def file_path(string: str) -> str:
    if os.path.isfile(string):
        return string
    else:
        raise argparse.ArgumentTypeError(f"{string} is not a valid file path.")


def dir_path(string: str) -> str:
    if os.path.isdir(string):
        return string
    else:
        raise argparse.ArgumentTypeError(f"{string} is not a valid directory path.")


# TODO: Make a LicenseChecker class for this
def generate_correction(pkg_license, compfile=LICENSES):
    with open(compfile, 'r') as f:
        words = f.readlines()

    words = [w.strip("\n") for w in words]
    WORDS = Counter(words)

    def P(word, N=sum(WORDS.values())):
        "Probability of `word`."
        return WORDS[word] / N

    def correction(word):
        "Most probable spelling correction for word."
        return max(candidates(word), key=P)

    def candidates(word):
        "Generate possible spelling corrections for word."
        return (known([word]) or known(edits1(word)) or known(edits2(word)) or [word])

    def known(words):
        "The subset of `words` that appear in the dictionary of WORDS."
        return set(w for w in words if w in WORDS)

    def edits1(word):
        "All edits that are one edit away from `word`."
        letters = 'abcdefghijklmnopqrstuvwxyz'
        symbols = '-.0123456789'
        letters += letters.upper() + symbols
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [L + R[1:] for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
        replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
        inserts = [L + c + R for L, R in splits for c in letters]
        return set(deletes + transposes + replaces + inserts)

    def edits2(word):
        "All edits that are two edits away from `word`."
        return (e2 for e1 in edits1(word) for e2 in edits1(e1))

    return correction(pkg_license)


def find_closest_match(string: str) -> str:
    closest_match = generate_correction(string)
    if closest_match == string:
        return None
    return closest_match


def find_location(filename, key: str, val: str) -> int:
    """
    Currently finds the line number of a key,
    after verifying the val is the same (because duplicate keys are possible)
    """
    # TODO: Refactor how this works to deal with multiple keys
    line = -1
    term = key if ":" in key else f"{key}:"
    with open(filename) as f:
        line_iter = iter(f.readlines())
        tokens = list(tokenize.generate_tokens(lambda: next(line_iter)))
    matches = [t for t in tokens if t.line.strip().startswith(term)]
    for m in matches:
        k, v = m.line.strip().split(":")
        if v.strip() != val:
            continue
        else:
            line = m.start[0]
    return line
