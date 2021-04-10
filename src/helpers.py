import re
import discord
import datetime
import pytz
from functools import lru_cache
from collections import defaultdict

OK_WORDS = {word.casefold() for word in ['no', 'yep', 'pog', 'true', 'huh']}
TIME_REGEX = re.compile('^(0?\d|1[012]):?([0-5]\d)\??$')
NOT_RSVPS = {word.casefold() for word in ['no', 'kekw', 'depredge', 'sadge', 'smoge', 'nopers',
	'omegalul', 'weirdchamp', 'huh']}
REQUIRED_NUMBERS = defaultdict(lambda: 1, {'among us': 6, 'in-house': 6})

@lru_cache(maxsize=1)
def find_emote(client: discord.Client, name: str) -> discord.Emoji:
	'''finds emote with given name and returns it (case insensitive)'''
	for guild in client.guilds:
		for emoji in guild.emojis:
			if emoji.name.casefold() == name.casefold():
				return emoji

def message_is_animated_react(message: discord.Message, emoji_names: {str: discord.Emoji}) -> bool:
	'''checks if a message intends to react with an animated emote'''
	text = message.content.casefold()
	return (text in emoji_names and message.reference is not None and emoji_names[text].animated \
	and len(message.content.split()) == 1)

def ping_and_time(message: discord.Message) -> ([discord.Role], int) or None:
	'''checks if a message contains a ping(s) AND a time.
	returns the Roles pinged and time in seconds until the scheduled time'''
	time_to_wait = None
	if message.role_mentions:
		for word in message.content.split():
			if match := re.match(TIME_REGEX, word):
				hour, minute = match.groups()
				hour = int(hour)
				minute = int(minute)
				now = datetime.datetime.now(pytz.timezone('America/Los_Angeles'))
				time_to_wait = (now.replace(hour = hour if now.hour < 12 else hour + 12,
					minute = minute, second = 0) - now).total_seconds()
		if time_to_wait:
			return message.role_mentions, time_to_wait

def message_rsvps(message: discord.Message) -> [discord.Reaction]:
	only_rsvps = [react for react in message.reactions if react.emoji.name.casefold() not in NOT_RSVPS \
		and react.count >= REQUIRED_NUMBERS[react.emoji.name.casefold()]]
	return sorted(only_rsvps, key = lambda reaction: reaction.count, reverse=True)
