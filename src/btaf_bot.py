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
	if message.author != client.user:
		violations = set()
		for emoji in message.guild.emojis:
			if emoji.name.casefold() == 'weirdchamp':
				weirdchamp = emoji
				break
		else:
			return
		emoji_names = {emoji.name.casefold(): emoji
			for emoji in message.guild.emojis}
		if len(message.content.split()) == 1
				and message.content.strip().casefold() in emoji_names
				and message.reference:
			emoji = emoji_names[message.content.strip().casefold()]
			await message.reference.add_reaction(emoji)
			await message.delete()
			return
		for word in message.content.split():
			if word.casefold() in emoji_names and word.casefold() not in OK_WORDS:
				violations.add((word, emoji_names[word.casefold()]))
		if len(violations) != 0:
			await message.add_reaction(weirdchamp)
		for violation in violations:
			await message.channel.send(
				f'''Typing {violation[0]} instead of {str(violation[1])} {str(weirdchamp)}''')

if __name__ == '__main__':
	client.run(TOKEN)
