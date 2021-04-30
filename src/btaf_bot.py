import discord
import os
import coroutines
import dotenv


dotenv.load_dotenv()
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

	await coroutines.deal_with_emotes(message)
	#replace messages with animated emotes with bot's version, because bot can use animated emotes

	await coroutines.handle_ping_and_time(message)
	#schedule and perform pings in the future

@client.event
async def on_message_edit(before: discord.Message, after: discord.Message):
	try:
		await before.remove_reaction(functions.get_emote(before.guild, 'weirdchamp'), client.user)
	except:
		pass
	await coroutines.cancel_ping(before)
	await on_message(after)
	#treat message edits as new messages

@client.event
async def on_message_delete(before: discord.Message):
	await coroutines.cancel_ping(before)

@client.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
	if user == client.user: return
	#ignore bot's own reactions

	if client.user in await reaction.users().flatten():
		if reaction.emoji.animated:
			await reaction.message.remove_reaction(reaction.emoji, client.user)
	#remove react if emote was animated, because it must have been a piggyback

	await coroutines.just_hit_react_threshold(reaction.message)

if __name__ == '__main__':
	client.run(DISCORD_TOKEN)

