import discord
import datetime
import pytz
import constants


def scheduled_time(hour: int, minute: int) -> (datetime.datetime, int):

	'''Returns a datetime.datetime object along with number of seconds until scheduled time, given
	an hour and a minute'''

	now = datetime.datetime.now(pytz.timezone('America/Los_Angeles'))
	scheduled = now.replace(hour=hour%12, minute=minute, second=0)
	twelve_hours = datetime.timedelta(seconds=12*60*60)

	while scheduled < now:
		scheduled += twelve_hours
	return (scheduled, (scheduled - now).total_seconds())

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

def message_top_react(message: discord.Message, role: discord.Role = None) -> discord.Reaction or None:
	
	'''Returns the discord.Reaction most reacted to'''

	only_rsvps = [react for react in message.reactions if react.emoji.name.casefold() not in constants.NOT_RSVPS]
	if role is not None:
		only_rsvps = [react for react in only_rsvps \
			if react.count >= constants.REQUIRED_NUMBERS[role.name.casefold()]]
	if len(only_rsvps) > 0:
		max_react = max(only_rsvps, key = lambda react: react.count)
		if [react.count for react in only_rsvps].count(max_react.count) == 1:
			return max_react
	return None

def get_emote(guild: discord.Guild, name: str) -> discord.Emoji or None:

	'''Gets the guild emote with the given name if it exists'''

	for emote in guild.emojis:
		if emote.name.casefold() == name.casefold():
			return emote
	return None

