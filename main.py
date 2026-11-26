#!/usr/bin/env python3
"""Your Human in One Word -- u-ronigrv-your-human-in-one-word-e4569a1c.

The brief asks for exactly one word, 1-30 characters, written to
``$MAKEFUN_OUTPUT_DIR/entry.txt`` (fallback ``/output``), describing the
human the entrant works for -- a boss, a client, a manager, whoever signs
off on the work.  A judge model then compares words two at a time, weighing
in order: (1) one word describing that human, (2) funny, (3) fits the
human, (4) vivid and specific rather than flat, (5) lands on its own with
no explanation needed.

So the program does not hard-code a throwaway label.  It carries a short
list of candidate portraits, scores each one against the judge's own five
criteria with a fixed rubric, and writes the highest-scoring word.  The
rubric, the candidates and the tie-break are all fixed in this file, so
the program is fully deterministic: same input, same word, every run.
No network, no randomness, no third-party libraries, Python 3 stdlib only.
"""

import os


# ---------------------------------------------------------------------------
# The candidates.
#
# Each candidate is one single word (no spaces, no hyphens) that tries to
# describe a boss in a way that makes a reader smile on sight.  Plain
# labels such as "busy", "fine" or "okay" are deliberately absent: the
# brief says flat words lose.  Every candidate below is a portrait of the
# same familiar human -- the boss who is never there when you need a
# sign-off, yet whose approval gates everything.
# ---------------------------------------------------------------------------

CANDIDATES = [
    # A boss who is never available: the sign-off bottleneck himself.
    "Unavailaboss",
    # The boss as a mythical creature you hear about but rarely see.
    "Ghostboss",
    # The boss whose "quick question" is never quick.
    "Quickquestioner",
    # The boss who keeps adding scope to every job.
    "Scopecreeper",
    # The boss who lives in meetings and governs from the calendar.
    "Meetingnomad",
    # The boss who always asks at the last possible minute.
    "Lastminuter",
    # The boss who says "yes, but..." to every finished piece of work.
    "Yesbutter",
    # The boss as a force of nature: huge, loud, impossible to ignore.
    "Bosszilla",
]


# ---------------------------------------------------------------------------
# The rubric: the judge's five criteria, most important first.
#
# Scores are small integers so the ranking is transparent and the
# tie-break (earlier candidate wins) is stable.  Each criterion is scored
# 0-2, except the first, which is a gate: a candidate that is not one word
# about the human scores 0 there and can never win.
# ---------------------------------------------------------------------------

def _score_on_subject(word):
    """Criterion 1: is it one word describing the human you work for?

    A single alphabetic token that names a kind of boss/client/manager
    scores full marks; anything with spaces or punctuation would fail
    the gate outright, so every candidate here is built to pass it.
    """
    if not word or not word.isalpha():
        return 0
    if " " in word or "-" in word:
        return 0
    return 2


def _score_funny(word):
    """Criterion 2: is it funny -- a joke or wry observation?

    The laugh here comes from wordplay: a familiar boss word fused with
    the thing that makes bosses funny to work for.  A straight label
    scores 0; a recognisable portmanteau scores 2.
    """
    lower = word.lower()
    fused = any(part in lower for part in ("boss",))
    twist = any(part in lower for part in ("unavail", "ghost", "creep",
                                           "zilla", "nomad", "butter"))
    if fused and twist:
        return 2
    if fused or twist:
        return 1
    return 0


def _score_fits(word):
    """Criterion 3: does it read as true of a boss, client or manager?

    The most universal, instantly recognisable boss truth is the
    unavailable approver: the person whose "yes" you need and who is
    never around to give it.  Words built on that truth score highest.
    """
    lower = word.lower()
    if "unavail" in lower or "ghost" in lower:
        return 2
    if "scope" in lower or "meeting" in lower or "lastminute" in lower:
        return 1
    return 1


def _score_vivid(word):
    """Criterion 4: is it vivid and specific, memorable and repeatable?

    Invented, picture-making words beat stock labels.  Length helps a
    little -- a longer fused word is more of a portrait -- but only up
    to the point where it stays pronounceable at a glance.
    """
    lower = word.lower()
    invented = lower not in ("boss", "manager", "client")
    picture = any(part in lower for part in ("ghost", "zilla", "nomad",
                                             "creep", "unavail"))
    if invented and picture:
        return 2
    if invented or picture:
        return 1
    return 0


def _score_lands_alone(word):
    """Criterion 5: does the joke land with no explanation needed?

    The winning word must explain itself the moment you read it: the
    two halves of the portmanteau must each be plain English, so the
    reader assembles the joke without a footnote.
    """
    lower = word.lower()
    plain_halves = (
        ("unavail", "boss"),
        ("ghost", "boss"),
        ("scope", "creeper"),
        ("meeting", "nomad"),
        ("last", "minuter"),
        ("yes", "butter"),
        ("boss", "zilla"),
        ("quick", "questioner"),
    )
    for first, second in plain_halves:
        if lower.startswith(first) and lower.endswith(second):
            return 2
    return 1


# Criterion weights follow the judge's order: on-subject first, then
# funny, then fitting, then vivid, then lands-alone.  The weights are
# strictly decreasing powers of two, so no later criterion can overturn
# an earlier one -- exactly the brief's "find the first one where they
# differ, and let that decide" instruction.
WEIGHTS = (16, 8, 4, 2, 1)


def total_score(word):
    """Weighted total for one candidate under the judge's rubric."""
    parts = (
        _score_on_subject(word),
        _score_funny(word),
        _score_fits(word),
        _score_vivid(word),
        _score_lands_alone(word),
    )
    return sum(weight * part for weight, part in zip(WEIGHTS, parts))


def choose_word():
    """Pick the best candidate; ties go to the earliest listed."""
    best_word = None
    best_score = -1
    for word in CANDIDATES:
        score = total_score(word)
        if score > best_score:
            best_score = score
            best_word = word
    return best_word


# ---------------------------------------------------------------------------
# Output.
#
# The gate checks that entry.txt is UTF-8 text of 1 to 30 characters,
# not only white space.  The chosen word is checked against that gate
# here, before writing, so a bad choice fails loudly in development
# instead of silently failing the gate in grading.  The file holds the
# word alone -- no trailing explanation, no newline, no extra words --
# because the judge is shown the file exactly as submitted and any
# extra text would turn a one-word entry into something else.
# ---------------------------------------------------------------------------

GATE_MIN_CHARS = 1
GATE_MAX_CHARS = 30


def output_dir():
    """Where the entry goes: $MAKEFUN_OUTPUT_DIR, else /output."""
    return os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")


def main():
    word = choose_word()
    # Gate check, mirroring the sealed scorer: 1-30 chars, not blank.
    if not (GATE_MIN_CHARS <= len(word) <= GATE_MAX_CHARS):
        raise SystemExit(
            "chosen word %r is %d chars, outside the 1-30 gate"
            % (word, len(word))
        )
    if not word.strip():
        raise SystemExit("chosen word is only white space")
    if " " in word:
        raise SystemExit("chosen word %r is not one word" % word)

    out_dir = output_dir()
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.txt")
    with open(out_path, "w", encoding="utf-8", newline="") as handle:
        handle.write(word)
    return word


if __name__ == "__main__":
    print(main())
