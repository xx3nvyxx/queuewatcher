from builtins import input
from discord.ext import tasks
from time import time,strftime
from ntfy.backends.pushover import notify
from os import path
import datetime
import discord
import yaml

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
        elif act == "NoPixel RP | Public Orange | Visit us @ nopixel.net":
            return "Public Orange"
        else:
            print("details:" + act)

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('-------')

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
            if text[1] == "channelLock":
                if message.author.id != 318152863605850113 and message.author.guild_permissions.administrator != True:
                    await message.add_reaction('\N{CROSS MARK}')
                    return
                if message.guild.id not in state["guilds"]:
                    state["guilds"][message.guild.id] = message.channel.id
                    await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                else:
                    await message.add_reaction('\N{CROSS MARK}')
                    return
            if text[1] == "channelUnlock":
                if message.author.id != 318152863605850113 and message.author.guild_permissions.administrator != True:
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
                await message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
            writeState()

    @tasks.loop(seconds=5)
    async def UserCheck(self):
        #clear older messages
        for gid in state["guilds"]:
            channel = self.get_channel(state["guilds"][gid])
            before = datetime.datetime.utcnow() - datetime.timedelta(seconds=60)
            after = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            async for message in channel.history(before=before, after=after):
                if message.author == self.user or message.content.startswith("!QueueWatcher") or message.content.startswith("!queuewatcher"):
                    await message.delete()
            
        #check for other users
        for memberID in state["members"]:
            if state["members"][memberID].get("enabled", True) == False:
                continue
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
            userset = state["members"][memberID].get("followers", set()) | {memberID}
            for toUser in userset:
                if status != prevStatus:
                    state["members"][toUser].pop(memberID, None)
                    if toUser == memberID:
                        state["members"][memberID]["status"] = status
                    writeState()
                if status != "Unknown" or (status == "Unknown" and prevStatus == "Menus"):
                    await self.sendMessage(toUser, memberID, status, start)

    async def sendMessage(self, toMemberID, aboutMemberID, status, activityStart):
        if state["members"][aboutMemberID].get("enabled", True) == False:
            return
        aboutGuild = self.get_guild(state["members"][aboutMemberID]["guild"])
        aboutMember = aboutGuild.get_member(aboutMemberID)
        name = state["members"][aboutMemberID].get("nickname", str(aboutMember))
        if status == "Unknown":
            if not (state["members"][toMemberID].get("crashdetection", False)):
                return
            message = name + " has left queue or an error occurred. Please check if FiveM or the queue crashed."
        if status == "Menus":
            if not (state["members"][toMemberID].get("queuejoin", False)):
                return
            message = name + " has opened FiveM and is in the menus. "
        if (status == "Public Purple" or status == "Public Orange"):
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

