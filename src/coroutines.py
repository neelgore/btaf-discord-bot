import discord
import re
import asyncio
import constants
import functions


PINGS = {}
#message board for if pings are still scheduled, so an async thread can abort if ping was canceled
#key is original message id, value is bot confirmation message id


async def deal_with_emotes(message: discord.Message):

	'''Changes replies with animated emote names to reacts of those emotes. Reacts weirdchamp if user
	missed colons in a non-animated emote name. Changes instances of animated emote names to the
	actually animated version'''

	OK_WORDS = {'no', 'yep', 'pog', 'true', 'huh', 'chad', 'based'}
	#words that aren't necessarily meaning to use the corresponding emote

	emoji_names = {emoji.name.casefold(): emoji for emoji in message.guild.emojis
		if emoji.name.casefold() not in OK_WORDS}
	casefolded = message.content.casefold()
	tokenized = message.content.split()

	if casefolded in emoji_names and message.reference is not None:
	#message wants to react an animated emote
		emoji = emoji_names[casefolded]
		original_message = await message.channel.fetch_message(message.reference.message_id)
		await original_message.add_reaction(emoji)
		await message.delete()
		return
		#animated react job is done, so we skip the rest

	animated = {word: emoji_names[word.casefold()] for word in tokenized if word.casefold() in emoji_names}
	#populate animated

	if len(animated) > 0:
		new_message = ' '.join((str(animated[word]) if word in animated else word) \
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
	if len(message.role_mentions) != 1 \
			or message.role_mentions[0].name.casefold() not in constants.REQUIRED_NUMBERS:
		return
	role = message.role_mentions[0]
	#do nothing if no role ping or role isn't a pingable role
	
	for word in message.content.split():
		if match := re.match(constants.TIME_REGEX, word):
			if time is not None:
				return
				#multiple times in message because time is already defined
			hour, minute = match.groups()
			time, seconds = functions.scheduled_time(int(hour), int(minute))
	#time is now defined if there is one

	confirmation_text = f'Will ping at {constants.REQUIRED_NUMBERS[role.name.casefold()]} reacts.' \
		if time is None else functions.schedule_text(time, seconds)
	PINGS[message.id] = (await message.reply(confirmation_text, mention_author=False)).id
	#send confirmation of ping, store id of this confirmation in case we need to cancel

	if time is not None:
		await asyncio.sleep(seconds)

		top_react = functions.message_top_react(message)
		if top_react is not None and top_react.count >= constants.REQUIRED_NUMBERS[role.name.casefold()] \
			and message.id in PINGS:
		#message has enough rsvps and ping hasn't been canceled yet
			await message.reply(role.mention, mention_author=False)
			#ping the role at the scheduled time

		del PINGS[message.id]
		await ping_after_n_minutes(message, 5)
	else:
		await asyncio.sleep(12*60*60)
		if message.id in PINGS:
			del PINGS[message.id]

async def ping_after_n_minutes(message: discord.Message, n: int):
	await asyncio.sleep(n*60)

	role = message.role_mentions[0]

	if (top_react := functions.message_top_react(message, role)):
		to_be_pinged = {member for member in await top_react.users().flatten() \
			if member.voice is None or member.voice.channel is None \
			or member.voice.channel.guild != message.guild}

		if len(to_be_pinged) > 0:
			everyone = ' '.join(member.mention for member in to_be_pinged)
			if modcheck := functions.get_emote(message.guild, 'modcheck'):
				await message.reply(everyone + '\n' + str(modcheck), mention_author=False)

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

async def just_hit_react_threshold(message: discord.Message):
	if message.id in PINGS:
		role = message.role_mentions[0]
		if top_react := functions.message_top_react(message, role):
			if message.id in PINGS and top_react.emoji.name.casefold() not in constants.NOT_RSVPS and \
				(await message.channel.fetch_message(PINGS[message.id])).content.startswith('Will ping'):
				if top_react.count == constants.REQUIRED_NUMBERS[role.name.casefold()]:
					await message.reply(f'{role.mention} Just hit {top_react.count} reacts', mention_author=False)
					del PINGS[message.id]
					await ping_after_n_minutes(message, 5)

		
