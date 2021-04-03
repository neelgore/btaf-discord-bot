import os
import discord
from dotenv import load_dotenv


load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
client = discord.Client()


@client.event
async def on_ready():
	print(f'{client.user} has connected to Discord!')
	client.OK_WORDS = {word.casefold() for word in ['no', 'yep', 'pog', 'true', 'huh']}
	for guild in client.guilds:
		for emoji in guild.emojis:
			if emoji.name.casefold() == 'weirdchamp'.casefold():
				client.WEIRDCHAMP = emoji
	#find and save the weirdchamp emote

@client.event
async def on_message(message):
	if message.author == client.user: return
	#ignore bot's own messages

	emoji_names = {emoji.name.casefold(): emoji for emoji in message.guild.emojis}
	#prepare dict of emote names to emote objets

	tokenized = message.content.split()

	if len(tokenized) == 1 and message.content.strip().casefold() in emoji_names \
		and message.reference is not None:
		emoji = emoji_names[message.content.strip().casefold()]
		if emoji.animated:
			original_message = await message.channel.fetch_message(message.reference.message_id)
			await original_message.add_reaction(emoji)
			await message.delete()
		return
	#replace replies with emote names with a reaction of the emote

	violations = False
	animated = dict()
	for word in message.content.split():
		if word.casefold() in emoji_names and word.casefold() not in client.OK_WORDS:
			if not emoji_names[word.casefold()].animated:
				violations = True
			else:
				animated[word] = emoji_names[word.casefold()]
	#populate animated and violations

	if violations:
		await message.add_reaction(client.WEIRDCHAMP)
	else:
		if (len(animated) != 0):
			new = " ".join((str(animated[w]) if w in animated else w) for w in message.content.split())
			if len(new.split()) == 1:
				await message.channel.send(f'**{message.author.display_name}:**')
				await message.channel.send(new)
			else:
				await message.channel.send(f'**{message.author.display_name}:** {new}')
			await message.delete()
			#simulate having Nitro

@client.event
async def on_message_edit(before, after):
	try:
		await after.remove_reaction(client.WEIRDCHAMP, client.user)
	except NotFound:
		pass
	await on_message(after)
	#treat message edits as new messages

@client.event
async def on_reaction_add(reaction, user):
	if user == client.user: return
	#ignore bot's own reactions

	if client.user in await reaction.users().flatten():
		if reaction.emoji != client.WEIRDCHAMP:
			await reaction.message.remove_reaction(reaction.emoji, client.user)
	#remove react once someone piggybacks, piggyback is a weirdchamp shame

if __name__ == '__main__':
	client.run(DISCORD_TOKEN)
