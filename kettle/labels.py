"""The 9 SINS activities, the words Kettle shows for them, and their colour tokens.

Every other module imports from here, so renaming an activity on screen is a one-line change.
"""

# SINS / DCASE 2018 Task 5 class names, in the official (alphabetical) order.
CLASSES: list[str] = [
    "absence",
    "cooking",
    "dishwashing",
    "eating",
    "other",
    "social_activity",
    "vacuum_cleaner",
    "watching_tv",
    "working",
]

# What a caregiver or parent reads. Plain words; "absence" becomes "Quiet" (heard, nothing happening).
DISPLAY: dict[str, str] = {
    "absence": "Quiet",
    "cooking": "Cooking",
    "dishwashing": "Washing up",
    "eating": "Eating",
    "other": "Some activity",
    "social_activity": "Conversation",
    "vacuum_cleaner": "Vacuuming",
    "watching_tv": "Talking / TV",
    "working": "Typing",
    "kitchen": "Kitchen activity",      # not a head class: a stretch the general tags heard as kitchen, without saying which
}

# Lower-case form for sentences ("Sounds like washing up").
PHRASE: dict[str, str] = {
    "absence": "quiet",
    "cooking": "cooking",
    "dishwashing": "washing up",
    "eating": "eating",
    "other": "some activity",
    "social_activity": "conversation",
    "vacuum_cleaner": "vacuuming",
    "watching_tv": "talking / TV",
    "working": "typing",
    "kitchen": "kitchen activity",
}

# CSS custom property for each activity colour (defined in static/app.css).
COLOUR_TOKEN: dict[str, str] = {
    "absence": "--act-empty",
    "cooking": "--act-cooking",
    "dishwashing": "--act-washing",
    "eating": "--act-eating",
    "other": "--act-moving",
    "social_activity": "--act-talk",
    "vacuum_cleaner": "--act-vacuum",
    "watching_tv": "--act-tv",
    "working": "--act-working",
    "kitchen": "--act-kitchen",
}

# Caregiver-level group: "kitchen activity" for the rule "kitchen activity by 10:00 AM".
MEAL: set[str] = {"cooking", "dishwashing", "eating", "kitchen"}

# Anything that is not "Quiet" counts as "some sound of activity".
ACTIVE: set[str] = (set(CLASSES) | {"kitchen"}) - {"absence"}

# When TV and Conversation are this close, the screen says "Talking / TV" instead of guessing.
TALK_OR_TV_MARGIN: float = 0.15
