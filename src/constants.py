import re


OK_WORDS = frozenset(word.casefold() for word in ['no', 'yep', 'pog', 'true', 'huh', 'chad'])
#words that aren't necessarily trying to invoke an emote

NOT_RSVPS = frozenset(word.casefold() for word in ['no', 'kekw', 'depredge', 'sadge', 'smoge', 'nopers',
	'omegalul', 'weirdchamp', 'huh', 'thumbsdown'])
#reacts that don't indicate an RSVP

TIME_REGEX = re.compile('^(0?\d|1[012]):?([0-5]\d)\??$')

REQUIRED_NUMBERS = {'among us': 8, 'in-house': 8, 'coding kyle': 1}

