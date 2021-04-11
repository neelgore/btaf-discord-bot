import re
import discord
import datetime
import pytz
import asyncio
from functools import lru_cache
from collections import defaultdict

OK_WORDS = {word.casefold() for word in ['no', 'yep', 'pog', 'true', 'huh']}
TIME_REGEX = re.compile('^(0?\d|1[012]):?([0-5]\d)\??$')
NOT_RSVPS = {word.casefold() for word in ['no', 'kekw', 'depredge', 'sadge', 'smoge', 'nopers',
	'omegalul', 'weirdchamp', 'huh']}
REQUIRED_NUMBERS = defaultdict(lambda: 1, {'among us': 6, 'in-house': 6})
PINGS = set()

@lru_cache(maxsize=1)
def find_emote(client: discord.Client, name: str) -> discord.Emoji:
	'''finds emote with given name and returns it (case insensitive)'''
	for guild in client.guilds:
		for emoji in guild.emojis:
			if emoji.name.casefold() == name.casefold():
				return emoji

async def deal_with_emotes(message: discord.Message, emoji_names: {str: discord.Emoji}):
	text = message.content.casefold()
	if text in emoji_names and message.reference is not None and emoji_names[text].animated \
		and len(message.content.split()) == 1:
		emoji = emoji_names[message.content.casefold()]
		original_message = await message.channel.fetch_message(message.reference.message_id)
		await original_message.add_reaction(emoji)
		await message.delete()
		return
		#animated react job is done

	violations = False
	animated = {}
	tokenized = message.content.split()
	for word in tokenized:
		if word.casefold() in emoji_names and word.casefold() not in OK_WORDS:
			if not emoji_names[word.casefold()].animated:
				violations = True
				break
			else:
				animated[word] = emoji_names[word.casefold()]
	#populate animated and violations

	if violations:
		await message.add_reaction(emoji_names['weirdchamp'.casefold()])
	else:
		if len(animated) > 0:
			new_message = ' '.join((str(animated[word]) if word.casefold() in animated else word) \
				for word in message.content.split())
			if len(tokenized) == 1:
				await message.channel.send(f'**{message.author.display_name}:**')
				await message.channel.send(new_message)
			else:
				await message.channel.send(f'**{message.author.display_name}:** {new_message}')
			await message.delete()
			#delete original message, resend with animated emotes (because bot can use animated emotes)

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
		if time_to_wait and time_to_wait > 0:
			return message.role_mentions, time_to_wait
		else:
			return None

async def handle_ping_and_time(message: discord.Message, emoji_names: {str: discord.Emoji}):
	time_to_wait = None
	if len(message.role_mentions) > 0:
		for word in message.content.split():
			if match := re.match(TIME_REGEX, word):
				if time_to_wait:
					return
					#multiple times in message
				hour, minute = match.groups()
				time_to_wait = seconds_until_time(int(hour), int(minute))
	if time_to_wait is not None:
		PINGS.add(message.id)
		await message.reply(schedule_text(time_to_wait))
		await asyncio.sleep(time_to_wait)
		if message_rsvps(message) and message.id in PINGS:
			await message.reply(' '.join(role.mention for role in message.role_mentions))
			#ping the roles at the scheduled time if enough people rsvped
		await asyncio.sleep(10*60)
		#after 10 minute grace period, individually ping everyone who reacted but isn't in a voice channel
		if (rsvps := message_rsvps(message)) and message.id in PINGS:
			to_be_pinged = {member for member in await rsvps.users().flatten() \
				if not member.voice or not member.voice.channel or member.voice.channel.guild != message.guild}
			if len(to_be_pinged) > 0:
				everyone = ' '.join(member.mention for member in to_be_pinged)
				await message.reply(everyone + '\n' + str(emoji_names['modcheck']))
			PINGS.remove(message.id)

def schedule_text(time_to_wait: int) -> str:
	m, s = divmod(time_to_wait, 60)
	h, m = divmod(m, 60)
	return 'Tentative ping scheduled in ' + str(int(h)) + (' hour ' if h == 1 else ' hours ') \
		+ str(int(m)) + (' minute ' if m == 1 else ' minutes ') \
		+ str(int(s)) + (' second.' if s == 1 else ' seconds.')
				
def seconds_until_time(hour: int, minute: int) -> int:
	now = datetime.datetime.now(pytz.timezone('America/Los_Angeles'))
	scheduled_time = now.replace(hour = hour, minute = minute, second = 0)
	twelve_hours = datetime.timedelta(seconds=60*60*12)
	while scheduled_time < now:
		scheduled_time += twelve_hours
	return (scheduled_time - now).total_seconds()

def message_rsvps(message: discord.Message) -> [discord.Reaction]:
	only_rsvps = [react for react in message.reactions if react.emoji.name.casefold() not in NOT_RSVPS \
		and react.count >= REQUIRED_NUMBERS[react.emoji.name.casefold()]]
	return sorted(only_rsvps, key = lambda reaction: reaction.count, reverse=True)

async def cancel_ping(message: discord.Message):
	if message.id in PINGS:
		PINGS.remove(message.id)
		await message.channel.send('Ping canceled.')

