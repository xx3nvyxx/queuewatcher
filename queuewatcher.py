from builtins import input
from discord.ext import tasks
from time import time,strftime
from ntfy.backends.pushover import notify
from os import path
import datetime
import discord
import yaml
import sys

state_filename = "queuewatcher_state.yml"
state = {}
sounds = ["pushover", "bike", "bugle", "cashregister", "classical", "cosmic",
"falling", "gamelan", "incoming", "intermission", "magic", "mechanical",
"pianobar", "siren", "spacealarm", "tugboat", "alien", "climb", "persistent",
"echo", "updown", "vibrate", "none"]

def readState():
    global state
    if path.exists(state_filename):
        with open(state_filename, 'r') as state_file:
            state = yaml.safe_load(state_file)
    else:
        print("State file does not exist")
    if (state == None):
        state = {}
    if ("members" not in state):
        state["members"] = {}
    if ("config" not in state):
        state["config"] = {}
    if ("admin" not in state["config"]):
        state["config"]["admin"] = int(input("User ID of the admin user: "))
    if ("discord" not in state["config"]):
        state["config"]["discord"] = input("Discord client token: ")
    if ("pushover" not in state["config"]):
        state["config"]["pushover"] = input("Pushover api token: ")
    if ("guilds" not in state):
        state["guilds"] = {}
    writeState()

def writeState():
    with open(state_filename, 'w') as state_file:
        dump = yaml.dump(state, default_flow_style=False)
        state_file.write(dump)

class QueueWatcher(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        readState()
        self.UserCheck.start()

    async def short_activity(self, act):
        if act == "In the menus":
            return "Menus"
        elif act == "nopixel RP | Signup @ nopixel.net":
            return "Whitelist"
        elif act == "NoPixel RP | Public Purple | Visit us @ nopixel.net":
            return "Public Purple"
        elif act == "NoPixel RP | Public Green | Visit us @ nopixel.net":
            return "Public Green"
        else:
            print("details: " + act)
            return "Other Server"

    async def on_ready(self):
        print(strftime("%Y-%m-%d %H:%M:%S") + " - Bot starting")
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('-------')

    async def on_error(event, args, kwargs):
        sys.exit(1)

    async def on_message(self, message):
        global state

        if message.author == self.user:
            return

        if message.guild == None:
            return

        if message.content.startswith("!QueueWatcher") or message.content.startswith("!queuewatcher"):
            text = message.content.split(" ")
            if len(text) == 1:
                await message.add_reaction('\N{CROSS MARK}')
                return
            if text[1] == "ping":
                if message.author.id != state["config"]["admin"]:
                    await message.add_reaction('\N{CROSS MARK}')
                    return
                await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                await message.channel.send("blargh")
            if text[1] == "errortest":
                if message.author.id != state["config"]["admin"]:
                    await message.add_reaction('\N{CROSS MARK}')
                    return
                await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                raise discord.InvalidData
            if text[1] == "channelLock":
                if message.author.id != state["config"]["admin"] and message.author.guild_permissions.administrator != True:
                    await message.add_reaction('\N{CROSS MARK}')
                    return
                if message.guild.id not in state["guilds"]:
                    state["guilds"][message.guild.id] = message.channel.id
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                else:
                    await message.add_reaction('\N{CROSS MARK}')
                    return
            if text[1] == "channelUnlock":
                if message.author.id != state["config"]["admin"] and message.author.guild_permissions.administrator != True:
                    await message.add_reaction('\N{CROSS MARK}')
                    return
                if message.guild.id in state["guilds"]:
                    state["guilds"].pop(message.guild.id, None)
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                else:
                    await message.add_reaction('\N{CROSS MARK}')
                    return
            if text[1] == "register":
                if message.author.id not in state["members"]:
                    state["members"][message.author.id] = {}
                state["members"][message.author.id]["channel"] = message.channel.id
                state["members"][message.author.id]["guild"] = message.guild.id
                await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
            if text[1] == "status":
                target = message.author.id
                if len(text) == 2:
                    if message.author.id not in state["members"]:
                        await message.channel.send("User not registered")
                        await message.add_reaction('\N{CROSS MARK}')
                        return
                    elif state["members"][message.author.id]["guild"] != message.guild.id:
                        await message.channel.send("User not associated with this discord server.")
                        await message.add_reaction('\N{CROSS MARK}')
                        return
                else:
                    target = int("".join(filter(str.isdigit, text[2])))
                    if target != message.author.id:
                        if message.author.id != state["config"]["admin"] and message.author.guild_permissions.administrator != True:
                            await message.add_reaction('\N{CROSS MARK}')
                            return
                        if message.author.id != state["config"]["admin"] and state["members"][target][guild] != message.guild.id:
                            await message.channel.send("User not associated with this discord server.")
                            await message.add_reaction('\N{CROSS MARK}')
                            return
                await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                response = "User details for "+ str(target) + "\n"
                if "nickname" in state["members"][target]:
                    response += "nickname: " + str(state["members"][target]["nickname"]) + "\n"
                if "enabled" in state["members"][target]:
                    response += "enabled: " + str(state["members"][target]["enabled"]) + "\n"
                if "status" in state["members"][target]:
                    response += "status: " + str(state["members"][target]["status"]) + "\n"
                if "crashdetection" in state["members"][target]:
                    response += "crashdetection: " + str(state["members"][target]["crashdetection"]) + "\n"
                if "ignorepublic" in state["members"][target]:
                    response += "ignorepublic: " + str(state["members"][target]["ignorepublic"]) + "\n"
                if "allowdms" in state["members"][target]:
                    response += "allowdms: " + str(state["members"][target]["allowdms"]) + "\n"
                if "repeat" in state["members"][target]:
                    response += "repeat: " + str(state["members"][target]["repeat"]) + "\n"
                if "pushover" in state["members"][target]:
                    response += "pushover: enabled (user key hidden)\n"
                if "priority" in state["members"][target]:
                    response += "priority: " + str(state["members"][target]["priority"]) + "\n"
                if "sound" in state["members"][target]:
                    response += "sound: " + str(state["members"][target]["sound"]) + "\n"
                await message.channel.send(content=response, delete_after=60)
            writeState()
            if message.author.id not in state["members"]:
                await message.add_reaction('\N{CROSS MARK}')
                return
            if text[1] == "unregister":
                state["members"].pop(message.author.id, None)
                await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
            if text[1] == "nickname":
                if len(text) == 2:
                    state["members"][message.author.id].pop("nickname", None)
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                else:
                    state["members"][message.author.id]["nickname"] = text[2]
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
            if text[1] == "allowfollows":
                if len(text) == 2 or text[2] == "off":
                    state["members"][message.author.id].pop("allowfollows", None)
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                    await message.delete(delay=1)
                elif len(text) > 2 and text[2] == "on":
                    state["members"][message.author.id]["allowfollows"] = True
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                    await message.delete(delay=1)
                else:
                    await message.add_reaction('\N{CROSS MARK}')
                    return
            if text[1] == "follow":
                if len(text) == 2:
                    await message.add_reaction('\N{CROSS MARK}')
                else:
                    followee = int("".join(filter(str.isdigit, text[2])))
                    if followee not in state["members"]:
                        await message.add_reaction('\N{CROSS MARK}')
                        await message.delete(delay=1)
                        return
                    if not state["members"][followee].get("allowfollows", False):
                        await message.add_reaction('\N{CROSS MARK}')
                        await message.delete(delay=1)
                        return
                    followers = state["members"][followee].get("followers", set())
                    state["members"][followee]["followers"] = followers | set([message.author.id])
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                await message.delete(delay=1)
            if text[1] == "unfollow":
                if len(text) == 2:
                    await message.add_reaction('\N{CROSS MARK}')
                else:
                    followee = int("".join(filter(str.isdigit, text[2])))
                    if followee not in state["members"]:
                        await message.add_reaction('\N{CROSS MARK}')
                        await message.delete(delay=1)
                        return
                    followers = state["members"][followee].get("followers", set())
                    state["members"][followee]["followers"] = followers - set([message.author.id])
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                await message.delete(delay=1)
            if text[1] == "clearfollows":
                state["members"][message.author.id].pop("followers", None)
                await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                await message.delete(delay=1)
            if text[1] == "crashdetection":
                if len(text) == 2 or text[2] == "off":
                    state["members"][message.author.id].pop("crashdetection", None)
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                elif len(text) > 2 and text[2] == "on":
                    state["members"][message.author.id]["crashdetection"] = True
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                else:
                    await message.add_reaction('\N{CROSS MARK}')
                    return
            if text[1] == "ignorepublic":
                if len(text) == 2 or text[2] == "off":
                    state["members"][message.author.id].pop("ignorepublic", None)
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                elif len(text) > 2 and text[2] == "on":
                    state["members"][message.author.id]["ignorepublic"] = True
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                else:
                    await message.add_reaction('\N{CROSS MARK}')
                    return
            if text[1] == "allowdms":
                if len(text) == 2 or text[2] == "off":
                    state["members"][message.author.id].pop("allowdms", None)
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                elif len(text) > 2 and text[2] == "on":
                    state["members"][message.author.id]["allowdms"] = True
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                else:
                    await message.add_reaction('\N{CROSS MARK}')
                    return
            if text[1] == "pushover":
                if len(text) == 2:
                    state["members"][message.author.id].pop("pushover", None)
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                else:
                    state["members"][message.author.id]["pushover"] = text[2]
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                    await message.delete(delay=2)
            if text[1] == "sound":
                if len(text) == 2:
                    state["members"][message.author.id].pop("sound", None)
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                elif len(text) > 2 and text[2] in sounds:
                    state["members"][message.author.id]["sound"] = text[2]
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                else:
                    await message.add_reaction('\N{CROSS MARK}')
                    return
            if text[1] == "priority":
                if len(text) == 2:
                    state["members"][message.author.id].pop("priority", None)
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                elif len(text) > 2 and text[2] in ["-2","-1","0","1"]:
                    state["members"][message.author.id]["priority"] = int(text[2])
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                else:
                    await message.add_reaction('\N{CROSS MARK}')
                    return
            if text[1] == "repeat":
                if len(text) == 2 or not text[2].isnumeric():
                    await message.add_reaction('\N{CROSS MARK}')
                    return
                state["members"][message.author.id]["repeat"] = int(text[2])
                await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
            if text[1] == "on":
                state["members"][message.author.id]["enabled"] = True
                await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
            if text[1] == "off":
                state["members"][message.author.id]["enabled"] = False
                state["members"][message.author.id]["status"] = "Unknown"
                await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
            writeState()

    @tasks.loop(seconds=5)
    async def UserCheck(self):
        try:
            #clear older messages
            for gid in state["guilds"]:
                channel = self.get_channel(state["guilds"][gid])
                before = datetime.datetime.utcnow() - datetime.timedelta(seconds=60)
                after = datetime.datetime.utcnow() - datetime.timedelta(days=1)
                async for message in channel.history(before=before, after=after):
                    if message.author == self.user and message.created_at <= (datetime.datetime.utcnow() - datetime.timedelta(seconds=600)):
                        await message.delete()
                    elif message.content.startswith("!QueueWatcher") or message.content.startswith("!queuewatcher"):
                        await message.delete()
            
            for memberID in state["members"]:
                guild = self.get_guild(state["members"][memberID]["guild"])
                member = guild.get_member(memberID)
                status = "Unknown"
                start = int(time()*1000)
                for activity in member.activities:
                    try:
                        if activity.application_id != 382624125287399424:
                            continue
                    except (AttributeError, TypeError):
                        continue
                    status = await self.short_activity(activity.details)
                    start = activity.timestamps.get("start")
                    break
                prevStatus = state["members"][memberID].get("status", "Unknown")
                if status != prevStatus and prevStatus not in ["Unknown", "Menus"]:
                    name = state["members"][memberID].get("nickname", str(member))
                    message = name + " is no longer in the " + prevStatus + " server. "
                    print(strftime("%Y-%m-%d %H:%M:%S") + " - " + message)
                userset = state["members"][memberID].get("followers", set()) | {memberID}
                for toUser in userset:
                    if status != prevStatus:
                        state["members"][toUser].pop(memberID, None)
                        if toUser == memberID:
                            state["members"][memberID]["status"] = status
                        writeState()
                    if state["members"][toUser].get("enabled", True) == False:
                        continue
                    if status != "Unknown" or (status == "Unknown" and prevStatus == "Menus"):
                        await self.sendMessage(toUser, memberID, status, prevStatus, start)
        except discord.DiscordException:
            print(strftime("%Y-%m-%d %H:%M:%S") + " - A discord error occurred")
            return

    async def sendMessage(self, toMemberID, aboutMemberID, status, prevStatus, activityStart):
        if state["members"][aboutMemberID].get("enabled", True) == False:
            return
        aboutGuild = self.get_guild(state["members"][aboutMemberID]["guild"])
        aboutMember = aboutGuild.get_member(aboutMemberID)
        name = state["members"][aboutMemberID].get("nickname", str(aboutMember))
        if status == "Other Server":
            return
        if status == "Unknown":
            if not (state["members"][toMemberID].get("crashdetection", False)):
                return
            message = name + " has left queue or an error occurred. Please check if FiveM or the queue crashed."
        if status == "Menus":
            if prevStatus == "Unknown":
                if state["members"][toMemberID].get("queuejoin", False):
                    message = name + " has opened FiveM and is in the menus. "
                else:
                    return
            else:
                if state["members"][toMemberID].get("crashdetection", False):
                    message = name + " has left the game, was kicked, or FiveM crashed. "
                else:
                    return
        if (status == "Public Purple" or status == "Public Green"):
            if state["members"][toMemberID].get("ignorepublic", False):
                return
            message = name + " is in the " + status + " server. "
        if status == "Whitelist":
            message = name + " is in the " + status + " server. "
        if state["members"][toMemberID].get(aboutMemberID, 0) == 0:
            start = state["members"][toMemberID][aboutMemberID] = activityStart
        else:
            start = state["members"][toMemberID][aboutMemberID]
        increment = int(600000 / state["members"][toMemberID].get("repeat", 1))
        cur_time = int(time()*1000)
        dur = int(int(cur_time - activityStart) / 1000)
        if status != "Unknown":
            message = message + "Duration: " + str(dur) + "s"
        if cur_time >= start and cur_time < activityStart + 600000:
            state["members"][toMemberID][aboutMemberID] = state["members"][toMemberID][aboutMemberID] + increment
            if "pushover" in state["members"][toMemberID]:
                notify("Queue Notification", message,
                        state["members"][toMemberID]["pushover"],
                        api_token=state["config"]["pushover"],
                        priority=state["members"][toMemberID].get("priority", 0),
                        sound=state["members"][toMemberID].get("sound", None))
            elif state["members"][toMemberID].get("allowdms", False):
                    toGuild = self.get_guild(state["members"][toMemberID]["guild"])
                    toMember = aboutGuild.get_member(toMemberID)
                    await toMember.send(content=message)
            elif toMemberID == aboutMemberID:
                channel = self.get_channel(state["guilds"].get(guild.id, state["members"][toMemberID]["channel"]))
                await channel.send(aboutMember.mention + " has been in the " + status + " server for " + str(dur) + "s")
            if toMemberID == aboutMemberID and status != "Unknown":
                print(strftime("%Y-%m-%d %H:%M:%S") + " - " + message)

    @UserCheck.before_loop
    async def preload(self):
        await self.wait_until_ready()


intents = discord.Intents.default()
intents.members = True
intents.presences = True

client = QueueWatcher(intents=intents)
client.run(state["config"]["discord"])

