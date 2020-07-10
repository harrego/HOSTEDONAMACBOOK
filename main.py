import math
import time
import datetime
import discord
import sqlite3

db = sqlite3.connect("db.sqlite3")
cursor = db.cursor()

db.execute('''CREATE TABLE IF NOT EXISTS offline_status
              (guild_id integer, user_id integer, time integer)''')
db.execute('''CREATE TABLE IF NOT EXISTS notify_channels
              (guild_id integer, channel_id integer, UNIQUE(guild_id, channel_id))''')

db.commit()

client = discord.Client()

@client.event
async def on_ready():
    print("Logged in")

@client.event
async def on_message(message):
    if message.author.bot != False:
        return
    id_string = "<@!" + str(client.user.id) + ">"
    bad_command_string = "BRO!!!!!!!!!!!! i dont know that command!!!!!! u can say: " + id_string + " channel <notify channel>, this will toggle notifications"

    if message.content.startswith(id_string):

        if message.author.guild_permissions.administrator != True:
            await message.channel.send("BRO!!!!!!!!!!!! IM IGNORING U BCS UR NOT AN ADMIN")
            return

        split = message.content.split()
        if len(split) <= 1:
            await message.channel.send(bad_command_string)
            return
        command = split[1]
        if command.lower() == "channel":
            mentioned_channels = message.channel_mentions
            if len(mentioned_channels) <= 0:
                await message.channel.send("u gotta tell me which channel to notify u in")
                return
            notify_channel = mentioned_channels[0]
            if message.channel.guild.id != message.guild.id:
                await message.channel.send("i need a channel in this server")
                return

            if str(message.channel.type) != "text":
                await message.channel.send("needs to be a text channel")
                return

            try:
                cursor.execute("INSERT INTO notify_channels VALUES (?, ?)", [message.channel.guild.id, notify_channel.id])
                db.commit()
                await message.channel.send("got it ill notify in <#" + str(notify_channel.id) + ">")
            except sqlite3.IntegrityError:
                cursor.execute("DELETE FROM notify_channels WHERE guild_id=? AND channel_id=?", [message.channel.guild.id, message.channel.id])
                db.commit()
                await message.channel.send("okay ill stop notifying in <#" + str(message.channel.id) + ">")
            
        else:
            await message.channel.send(bad_command_string)

@client.event
async def on_member_update(before, after):
    print("update id:", after.id)
    if before.status == after.status:
        return
    if after.bot != True:
        return
    guild_id = after.guild.id
    user_id = after.id
    if str(after.status) == "offline":
        current_time = int(time.time())
        cursor.execute("INSERT INTO offline_status VALUES (?, ?, ?)", [guild_id, user_id, current_time])
        db.commit()
    elif str(after.status) != "offline":
        cursor.execute("SELECT * FROM offline_status WHERE guild_id=? AND user_id=? ORDER BY time DESC", [guild_id, user_id])
        last_offline_event = cursor.fetchone()

        if last_offline_event == None:
            return

        went_offline_time = datetime.datetime.fromtimestamp(last_offline_event[2])
        current_time = datetime.datetime.now()

        difference = current_time - went_offline_time
        minutes_difference = difference / datetime.timedelta(minutes=1)

        formatted_minutes = math.floor(minutes_difference)
        formatted_seconds = round(((minutes_difference % 1) * 60))

        cursor.execute("SELECT * FROM notify_channels WHERE guild_id=?", [guild_id])
        channels = cursor.fetchall()

        for channel in channels:
            channel_id = channel[1]
            discord_channel = client.get_channel(channel_id)
            if discord_channel == None:
                cursor.execute("DELETE FROM notify_channels WHERE channel_id=?", [channel_id])
                db.commit()
                return
            await discord_channel.send("<@!" + str(after.id) + "> was down for " + str(formatted_minutes) + " minutes and " + str(formatted_seconds) + " seconds!!!!!!!! their macbook woke from sleep :)")

@client.event
async def on_guild_remove(guild):
    cursor.execute("DELETE FROM offline_status WHERE guild_id=?", [guild.id])
    cursor.execute("DELETE FROM notify_channels WHERE guild_id=?", [guild.id])
    db.commit()

client.run("")