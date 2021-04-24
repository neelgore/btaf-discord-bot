import discord
import re
import datetime
import pytz
import asyncio
from collections import defaultdict


OK_WORDS = frozenset({word.casefold() for word in ['no', 'yep', 'pog', 'true', 'huh', 'chad']})
#words that aren't necessarily trying to use an emote

NOT_RSVPS = frozenset({word.casefold() for word in ['no', 'kekw', 'depredge', 'sadge', 'smoge', 'nopers',
	'omegalul', 'weirdchamp', 'huh', 'thumbsdown']})
#reacts that don't indicate an RSVP

TIME_REGEX = re.compile('^(0?\d|1[012]):?([0-5]\d)\??$')

REQUIRED_NUMBERS = defaultdict(lambda: 2, {'among us': 6, 'in-house': 8})
#need this many rsvps to ping

PINGS = {}
#message board for if pings are still scheduled, so an async thread can abort if ping was canceled
#key is original message id, value is bot confirmation id


async def deal_with_emotes(message: discord.Message):

	'''Changes replies with animated emote names to reacts of those emotes. Reacts weirdchamp if user
	missed colons in a non-animated emote name. Changes instances of animated emote names to the
	actually animated version'''

	emoji_names = {emoji.name.casefold(): emoji for emoji in message.guild.emojis}
	casefolded = message.content.casefold()
	tokenized = message.content.split()

	if casefolded in emoji_names and message.reference is not None and emoji_names[casefolded].animated:
	#message wants to react an animated emote
		emoji = emoji_names[casefolded]
		original_message = await message.channel.fetch_message(message.reference.message_id)
		await original_message.add_reaction(emoji)
		await message.delete()
		return
		#animated react job is done, so we skip the rest

	violations = False
	animated = {}
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
				for word in tokenized)
			if len(tokenized) == 1:
				await message.channel.send(f'**{message.author.display_name}:**')
				await message.channel.send(new_message)
				#send emote in its own separate message so it appears big
			else:
				await message.channel.send(f'**{message.author.display_name}:** {new_message}')
			await message.delete()

async def handle_ping_and_time(message: discord.Message):

	'''Checks if a message includes role ping(s) and a time. If so, schedules a ping at that time
	if enough people rsvped(reacted) to the original message. 10 minutes after scheduled time,
	individually pings people who rsvped who aren't in a voice channel'''

	time = seconds = None
	if len(message.role_mentions) > 0:
	#if there are role pings
		for word in message.content.split():
			if match := re.match(TIME_REGEX, word):
				if time is not None:
					return
					#multiple times in message because time is already defined
				hour, minute = match.groups()
				time, seconds = scheduled_time(int(hour), int(minute))

	if time is not None:
	#there is a ping and a time
		PINGS[message.id] = (await message.reply(schedule_text(time, seconds))).id
		#send confirmation of ping, store id of this confirmation in case we need to cancel

		await asyncio.sleep(seconds)

		if message_rsvps(message) and message.id in PINGS:
		#message has enough rsvps and ping hasn't been canceled yet
			await message.reply(' '.join(role.mention for role in message.role_mentions))
			#ping the roles at the scheduled time

		await asyncio.sleep(10*60)

		#after 10 minute grace period, individually ping everyone who reacted but isn't in a voice channel
		if (rsvps := message_rsvps(message)) and message.id in PINGS:
			to_be_pinged = {member for member in await rsvps.users().flatten() \
				if member.voice is None or member.voice.channel is None \
				or member.voice.channel.guild != message.guild}

			if len(to_be_pinged) > 0:
				everyone = ' '.join(member.mention for member in to_be_pinged)
				for emote in message.guild.emojis:
					if emote.name.casefold() == 'modcheck'.casefold():
						await message.reply(everyone + '\n' + str(emote))
						break
			del PINGS[message.id]

def schedule_text(time: datetime.datetime, seconds: int) -> str:

	'''Returns a nice string that confirms a ping has been scheduled'''

	m, s = divmod(seconds, 60)
	h, m = divmod(m, 60)
	#convert seconds into hours, minutes, seconds
	iso = str(time.hour%12) + time.isoformat()[13:16] + (' PM ' if time.hour >= 12 else ' AM ')

	return 'Tentative ping scheduled for ' + iso + time.tzname() + ' in ' \
		+ str(int(h)) + (' hour ' if h == 1 else ' hours ') \
		+ str(int(m)) + (' minute ' if m == 1 else ' minutes ') \
		+ str(int(s)) + (' second.' if s == 1 else ' seconds.')
				
def scheduled_time(hour: int, minute: int) -> (datetime.datetime, int):
	'''Returns a datetime.datetime object along with number of seconds until scheduled time given
	an hour and a minute'''
	now = datetime.datetime.now(pytz.timezone('America/Los_Angeles'))
	scheduled_time = now.replace(hour = hour%12, minute = minute, second = 0)
	twelve_hours = datetime.timedelta(seconds=60*60*12)
	while scheduled_time < now:
		scheduled_time += twelve_hours
	return (scheduled_time, (scheduled_time - now).total_seconds())

def message_rsvps(message: discord.Message) -> discord.Reaction or None:
	'''Returns the discord.Reaction most reacted to, which it assumes is the rsvp emote'''
	only_rsvps = [react for react in message.reactions if react.emoji.name.casefold() not in NOT_RSVPS \
		and react.count >= REQUIRED_NUMBERS[react.emoji.name.casefold()]]
	if len(only_rsvps) > 0:
		return sorted(only_rsvps, key = lambda reaction: reaction.count, reverse=True)[0]
	else:
		return None

async def cancel_ping(message: discord.Message):
	'''Deletes bot confirmation message from when the ping was scheduled, deletes the ping from PINGS,
	and sends a message confirming ping cancellation. This message gets removed after 5 seconds to
	prevent clutter'''
	if message.id in PINGS:
		bot_confirmation = await message.channel.fetch_message(PINGS[message.id])
		await bot_confirmation.delete()
		del PINGS[message.id]
		cancel_confirmation = await message.channel.send('Ping canceled.')
		await cancel_confirmation.delete(delay=5)
		
