import os
import discord
import helpers
import asyncio
from dotenv import load_dotenv


load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
#Discord token is stored as an environment variable

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents = intents)
#need members intent for some functionalities


@client.event
async def on_ready():
	print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message: discord.Message):
	if message.author == client.user: return
	#ignore bot's own messages

	emoji_names = {emoji.name.casefold(): emoji for emoji in message.guild.emojis}
	#prepare dict of emote names to emote objects

	if helpers.message_is_animated_react(message, emoji_names):
		emoji = emoji_names[message.content.casefold()]
		original_message = await message.channel.fetch_message(message.reference.message_id)
		await original_message.add_reaction(emoji)
		await message.delete()
		return
	#replace replies with animated emote names with a reaction of the emote

	violations = False
	animated = dict()
	for word in message.content.split():
		if word.casefold() in emoji_names and word.casefold() not in helpers.OK_WORDS:
			if not emoji_names[word.casefold()].animated:
				violations = True
			else:
				animated[word] = emoji_names[word.casefold()]
	#populate animated and violations

	if violations:
		await message.add_reaction(helpers.find_emote(client, 'weirdchamp'))
	else:
		if (len(animated) != 0):
			new_message = " ".join((str(animated[w]) if w in animated else w) \
				for w in message.content.split())
			if len(message.content.split()) == 1:
				await message.channel.send(f'**{message.author.display_name}:**')
				await message.channel.send(new_message)
			else:
				await message.channel.send(f'**{message.author.display_name}:** {new_message}')
			await message.delete()
			#delete original message, resend with animated emotes (because bot can use animated emotes)
	if p_and_t := helpers.ping_and_time(message):
		#if message attempts to schedule something (by pinging a role and giving a time)
		roles, time_to_wait = p_and_t
		if time_to_wait > 0:			
			m, s = divmod(time_to_wait, 60)
			h, m = divmod(m, 60)
			schedule = 'Tentative ping scheduled in ' + str(int(h)) + (' hour ' if h == 1 else ' hours ') \
				+ str(int(m)) + (' minute ' if m == 1 else ' minutes ') \
				+ str(int(s)) + (' second.' if s == 1 else ' seconds.')
			helpers.PINGS.add(message.id)
			await message.reply(schedule)
			await asyncio.sleep(time_to_wait)
			if helpers.message_rsvps(message) and message.id in helpers.PINGS:
				await message.reply(' '.join(role.mention for role in roles))
			#ping the roles at the specified time if enough people rsvped
			await asyncio.sleep(10*60)
			#after 10 minute grace period, individually ping everyone who reacted but isn't in a voice channel
			if message.id in helpers.PINGS:
				if rsvps := helpers.message_rsvps(message):
					to_be_pinged = {member for member in await rsvps.users().flatten()\
						if not member.voice or not member.voice.channel	or member.voice.channel.guild != message.guild}
					if len(to_be_pinged) > 0:
						everyone = ' '.join(member.mention for member in to_be_pinged)
						await message.reply(everyone + '\n' + str(emoji_names['modcheck']))
				helpers.PINGS.remove(message.id)

@client.event
async def on_message_edit(before: discord.Message, after: discord.Message):
	await on_message_delete(before)
	await on_message(after)
	#treat message edits as new messages

@client.event
async def on_message_delete(before: discord.Message):
	try:
		await before.remove_reaction(helpers.find_emote(client, 'weirdchamp'), client.user)
	except discord.errors.NotFound:
		pass
	await helpers.cancel_ping(before)

@client.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
	if user == client.user: return
	#ignore bot's own reactions

	if client.user in await reaction.users().flatten():
		if reaction.emoji != helpers.find_emote(client, 'weirdchamp'):
			await reaction.message.remove_reaction(reaction.emoji, client.user)
	#remove react once someone piggybacks, unless piggyback is a weirdchamp shame

if __name__ == '__main__':
	client.run(DISCORD_TOKEN)
