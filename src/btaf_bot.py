import os
import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
client = discord.Client()

OK_WORDS = {word.casefold() for word in ['no', 'yep', 'pog', 'true', 'huh']}

@client.event
async def on_ready():
	print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
	if message.author == client.user: return
	#ignore bot's own messages

	emoji_names = {emoji.name.casefold(): emoji for emoji in message.guild.emojis}
	#prepare dict of emote names to emote objets

	if len(message.content.split()) == 1 \
			and message.content.strip().casefold() in emoji_names and message.reference:
		emoji = emoji_names[message.content.strip().casefold()]
		original_message = await message.channel.fetch_message(message.reference.message_id)
		await original_message.add_reaction(emoji)
		await message.delete()
		return
	#replace replies with emote names with a reaction of the emote

	for emoji in message.guild.emojis:
		if emoji.name.casefold() == 'weirdchamp':
			weirdchamp = emoji
			break
	else:
		return
	#find the weirdchamp emote and do nothing if it doesn't exist

	violations = dict()
	animated = dict()
	for word in message.content.split():
		if word.casefold() in emoji_names and word.casefold() not in OK_WORDS:
			if not emoji_names[word.casefold()].animated:
				violations[word] = emoji_names[word.casefold()]
			else:
				animated[word] = emoji_names[word.casefold()]
	#populate animated and violations dicts

	if len(violations) == 0:
		if (len(animated) != 0):
			new = " ".join((str(animated[w]) if w in animated else w) for w in message.content.split())
			if len(new.split()) == 1:
				await message.channel.send(f'**{message.author.display_name}:**')
				await message.channel.send(new)
			else:
				await message.channel.send(f'**{message.author.display_name}:** {new}')
			await message.delete()
	else:
		await message.add_reaction(weirdchamp)
		await message.reply('\n'.join(
			f'''Typing {wrong} instead of {str(emoji)} {str(weirdchamp)}''' for wrong, emoji in violations.items()))

@client.event
async def on_message_edit(before, after):
	await on_message(after)
	#treat message edits as new messages

@client.event
async def on_reaction_add(reaction, user):
	if user == client.user: return
	#ignore bot's own reactions

	if client.user in await reaction.users().flatten():
		await reaction.message.remove_reaction(reaction.emoji, client.user)
	#remove react once someone piggybacks

if __name__ == '__main__':
	client.run(TOKEN)
