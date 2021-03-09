import os
import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
client = discord.Client()

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
		for word in message.content.split():
			if word.casefold() in emoji_names:
				violations.add((word, emoji_names[word.casefold()]))
		if len(violations) != 0:
			await message.add_reaction(weirdchamp)
		for violation in violations:
			await message.channel.send(
				f'''Typing {violation[0]} instead of {str(violation[1])} {str(weirdchamp)}''')

if __name__ == '__main__':
	client.run(TOKEN)
