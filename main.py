import nextcord, os, asyncio, random, json, requests, uuid, math, time
from nextcord.ext import commands, tasks, application_checks
import numpy as np
from rblxopencloud import *
from dotenv import load_dotenv

TESTING_GUILD_ID = 894145137494605824 # astaria server

intents = nextcord.Intents.default()
intents.members = True

bot = commands.Bot(intents=intents)
client = nextcord.Client(activity=nextcord.Game(name='with the Astaria API'))

load_dotenv()

key = os.getenv("KEY") # This is the API key for datastore access
uid = os.getenv("UID") # This is the user ID of the universe
token = os.getenv("TOKEN")

experience = Experience(uid, api_key=key)
PlayerData = experience.get_data_store("data", scope="global")
API_ENDPOINT = "https://users.roblox.com/v1/usernames/users"

def xptolevel(xp):
  return int(math.sqrt(xp)/10)
def leveltoxp(level):
  return int((level*10)**2)

def getUserId(username):

    requestPayload = {
        "usernames": [
            username
        ],

        "excludeBannedUsers": False
    }

    responseData = requests.post(API_ENDPOINT, json=requestPayload)

    # Make sure the request succeeded
    assert responseData.status_code == 200

    userId = responseData.json()["data"][0]["id"]

    print(f"getUserId :: Fetched user ID of username {username} -> {userId}")
    return userId
def load(pid):
    try:
        data, dinfo = PlayerData.get(str(pid))
        return 0, data, dinfo
    except NotFound:
        print("Datastore not found!")
        PlayerData.set(str(pid), {})
        load()
    except InvalidKey:
        print("Invalid key!")
        return [1]
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
        return [1]

@bot.event
async def on_ready():
  print(f'We have logged in!')

@bot.slash_command(description="Checks if the bot is online", guild_ids=[TESTING_GUILD_ID])
async def test(interaction: nextcord.Interaction):
  await interaction.send("I am online!")

class items(commands.Cog):
  @bot.slash_command(guild_ids=[TESTING_GUILD_ID])
  async def item(interaction: nextcord.Interaction):
    pass
  
  @item.subcommand(description="Get a player's item count")
  async def get(interaction: nextcord.Interaction, username: str, item: str):
    loadresult = load(getUserId(username))
    if loadresult[0] == 0:
      data = loadresult[1]
      dinfo = loadresult[2]
      print(data)
      if not "items" in data:
        data["items"] = {}
      if item.lower() in data["items"]:
        reqdata = str(data["items"][item.lower()])
        await interaction.send(f"**{username}** has **{reqdata} {item.title()}.**")
      else:
        await interaction.send(f"**{username}** has **0 {item.title()}**. Either they haven't discovered **{item.title()}** yet, or the key is misspelt.")

  @item.subcommand(description="Set a player's item count")
  async def set(interaction: nextcord.Interaction, username: str, item: str, value: int):
    if nextcord.utils.get(interaction.user.roles, id=1033863011959582812):
      pid = getUserId(username)
      loadresult = load(pid)
      if loadresult[0] == 0:
        data = loadresult[1]
        dinfo = loadresult[2]
        if not "items" in data:
          data["items"] = {}
        if item.lower() in data["items"]:
          data["items"][item.lower()] = value
          PlayerData.set(pid, data)
          await interaction.send(f"Set **{username}'s {item.title()}** count to **{value}**.")
        else:
          data["items"][item.lower()] = value
          PlayerData.set(pid, data)
          await interaction.send(f"Created **{username}'s {item.title()}** count, and set it to **{value}**.")
    else:
      await interaction.send("You do not have permissions to change user data!", ephemeral = True)

class invitem(commands.Cog):
  @bot.slash_command(guild_ids=[TESTING_GUILD_ID])
  async def invitem(interaction: nextcord.Interaction):
    pass
  
  @invitem.subcommand(description="List all inventory items, such as tools, weapons and armour.")
  async def list(interaction: nextcord.Interaction, username: str):
    pid = getUserId(username)
    loadresult = load(pid)
    if loadresult[0] == 0:
      data = loadresult[1]
      dinfo = loadresult[2]
      if not "inventory" in data:
        data["inventory"] = {}
      i = 0
      message = f"Items in {username}'s inventory:"
      results = []
      for item in data["inventory"].keys():
        results.insert(i, item)
        i += 1
        message += ("\n" + f"**{i}.** " + item)
      await interaction.send(message)

  @invitem.subcommand(description="Get info on an item in an inventory.")
  async def info(interaction: nextcord.Interaction, username: str, itemindex: int):
    pid = getUserId(username)
    loadresult = load(pid)
    if loadresult[0] == 0:
      data = loadresult[1]
      dinfo = loadresult[2]
      if not "inventory" in data:
        data["inventory"] = {}
      i = 0
      results = []
      for item in data["inventory"].keys():
        results.insert(i, item)
        i += 1
      invitem = data["inventory"][str(results[itemindex])]
      message = "**Item info:**"
      if "base" in invitem:
        message += f'\n**Base item:** {invitem["base"]}'
      if "id" in invitem:
        message += f'\n**UUID:** {invitem["id"]}'
      message += '\n\n*note that this is still heavily wip!*'

      await interaction.send(message)

  @invitem.subcommand(description="Create an inventory item!")
  async def create(interaction: nextcord.Interaction, username: str, base: str, itemname: str):
    if nextcord.utils.get(interaction.user.roles, id=1033863011959582812):
      pid = getUserId(username)
      loadresult = load(pid)
      if loadresult[0] == 0:
        data = loadresult[1]
        dinfo = loadresult[2]
        if not "inventory" in data:
          data["inventory"] = {}
        if data["inventory"].get(itemname) == None:
          data["inventory"][str(itemname)] = {}
          data["inventory"][str(itemname)]["base"] = base
          data["inventory"][str(itemname)]["id"] = str(uuid.uuid4())
          PlayerData.set(pid, data)
          await interaction.send(f"Created a **{base}** named **{itemname}** for **{username}**!")
        else:
          for i in range(1, 1001):
            if i > 1000:
              await interaction.send(f"**{username}** already has over 1000 items named **{itemname}**! Don't you think that's a bit much?")
              break
            if data["inventory"].get(str(itemname) + f"({i})") == None:
              data["inventory"][str(itemname) + f"({i})"] = {}
              data["inventory"][str(itemname) + f"({i})"]["base"] = base
              data["inventory"][str(itemname) + f"({i})"]["id"] = str(uuid.uuid4())
              PlayerData.set(pid, data)
              await interaction.send(f"Created a **{base}** named **{itemname} ({i})** for **{username}**!")
              break
          
    else:
      await interaction.send("You do not have permissions to change user data!", ephemeral = True)

  @invitem.subcommand(description="Rename an inventory item!")
  async def rename(interaction: nextcord.Interaction, username: str, itemindex: str, newname: str):
    if nextcord.utils.get(interaction.user.roles, id=1033863011959582812):
      pid = getUserId(username)
      loadresult = load(pid)
      if loadresult[0] == 0:
        data = loadresult[1]
        dinfo = loadresult[2]
        if not "inventory" in data:
          data["inventory"] = {}
        i = 0
        results = []
        for item in data["inventory"].keys():
          results.insert(i, item)
          i += 1
        if itemindex in results:
          if newname in results:
            await interaction.send(f"**{newname}** already exists in **{username}'s** inventory.")
            return
          data["inventory"][newname] = data["inventory"][itemindex]
          del data["inventory"][str(results[itemindex])]
          PlayerData.set(pid, data)
          await interaction.send(f"Renamed **{itemindex}** to **{newname}** for **{username}**!")
        else:
          await interaction.send(f"**{itemindex}** is not in **{username}'s** inventory.")
    else:
      await interaction.send("You don't have permissions to change user data!", ephemeral = True)

  @invitem.subcommand(description="Delete an inventory item! (List items with /invitem list)")
  async def delete(interaction: nextcord.Interaction, username: str, itemindex: int):
    if nextcord.utils.get(interaction.user.roles, id=1033863011959582812):
      pid = getUserId(username)
      loadresult = load(pid)
      if loadresult[0] == 0:
        data = loadresult[1]
        dinfo = loadresult[2]
        if not "inventory" in data:
          data["inventory"] = {}
        i = 0
        results = []
        for item in data["inventory"].keys():
          results.insert(i, item)
          i += 1
        print(results)
        if itemindex <= len(results):
          del data["inventory"][str(results[itemindex-1])]
          PlayerData.set(pid, data)
          await interaction.send(f"Deleted item position **{itemindex}** from **{username}'s** inventory.")
        else:
          await interaction.send(f"Item position **{itemindex}** is not in **{username}'s** inventory.")
    else:
      await interaction.send("Nope.", ephemeral = True)

  @invitem.subcommand(description="Refresh the UUID of an inventory item! (List items with /invitem list)")
  async def refreshuuid(interaction: nextcord.Interaction, username: str, itemindex: int):
    if nextcord.utils.get(interaction.user.roles, id=1033863011959582812):
      pid = getUserId(username)
      loadresult = load(pid)
      if loadresult[0] == 0:
        data = loadresult[1]
        dinfo = loadresult[2]
        if not "inventory" in data:
          data["inventory"] = {}
        i = 0
        results = []
        for item in data["inventory"].keys():
          results.insert(i, item)
          i += 1
        if itemindex in results:
          data["inventory"][str(results[itemindex])]["id"] = str(uuid.uuid4())
          PlayerData.set(pid, data)
          await interaction.send(f"Refreshed the UUID of **{itemindex}** for **{username}**!")
        else:
          await interaction.send(f"**{itemindex}** is not in **{username}'s** inventory.")
    else:
      await interaction.send("You don't have permissions to change user data!", ephemeral = True)

class skillxp(commands.Cog):
  @bot.slash_command(guild_ids=[TESTING_GUILD_ID])
  async def skillxp(interaction: nextcord.Interaction):
    pass

  @skillxp.subcommand(description="See how much XP a player has of a certain skill.")
  async def get(interaction: nextcord.Interaction, username: str, skill: str):
    pid = getUserId(username)
    loadresult = load(pid)
    if loadresult[0] == 0:
      data = loadresult[1]
      dinfo = loadresult[2]
      if not "xp" in data:
        data["xp"] = {}
      if not skill in data["xp"]:
        data["xp"][skill] = 0
      xp = data["xp"][skill]
      level = xptolevel(xp)
      await interaction.send(f"{username} has **{xp} {skill}**! (Level **{level}**)")

  @skillxp.subcommand(description="Set a player's XP in a certain skill. Format: SkillXP")
  async def set(interaction: nextcord.Interaction, username: str, amount: int, skill: str):
    if nextcord.utils.get(interaction.user.roles, id=1033863011959582812):
      pid = getUserId(username)
      loadresult = load(pid)
      if loadresult[0] == 0:
        data = loadresult[1]
        dinfo = loadresult[2]
        if not "xp" in data:
          data["xp"] = {}
        data["xp"][skill] = amount
        PlayerData.set(pid, data)
        await interaction.send(f"Set **{username}'s** {skill} to **{amount}**!")
    else:
      await interaction.send("Nice try.", ephemeral = True)

class money(commands.Cog):
  @bot.slash_command(guild_ids=[TESTING_GUILD_ID])
  async def money(interaction: nextcord.Interaction):
    pass

  @money.subcommand(description="See how much money a player has.")
  async def get(interaction: nextcord.Interaction, username: str):
    pid = getUserId(username)
    loadresult = load(pid)
    if loadresult[0] == 0:
      data = loadresult[1]
      dinfo = loadresult[2]
      if not "Money" in data:
        data["Money"] = 0
      money = data["Money"]
      await interaction.send(f"{username} has ${money}!")

  @money.subcommand(description="Set a player's money.")
  async def set(interaction: nextcord.Interaction, username: str, amount: int):
    if nextcord.utils.get(interaction.user.roles, id=1033863011959582812):
      pid = getUserId(username)
      loadresult = load(pid)
      if loadresult[0] == 0:
        data = loadresult[1]
        dinfo = loadresult[2]
        if not "Money" in data:
          data["Money"] = 0
        data["Money"] = amount
        PlayerData.set(pid, data)
        await interaction.send(f"Set **{username}'s money** to **${amount}**.")
    else:
      await interaction.send("Nope.", ephemeral = True)

  @money.subcommand(description="Add money to a player's balance.")
  async def add(interaction: nextcord.Interaction, username: str, amount: int):
    if nextcord.utils.get(interaction.user.roles, id=1033863011959582812):
      pid = getUserId(username)
      loadresult = load(pid)
      if loadresult[0] == 0:
        data = loadresult[1]
        dinfo = loadresult[2]
        if not "Money" in data:
          data["Money"] = 0
        data["Money"] += amount
        PlayerData.set(pid, data)
        await interaction.send(f"Added **${amount}** to **{username}'s money**.")
    else:
      await interaction.send("Nope.", ephemeral = True)

  @money.subcommand(description="Remove money from a player's balance.")
  async def remove(interaction: nextcord.Interaction, username: str, amount: int):
    if nextcord.utils.get(interaction.user.roles, id=1033863011959582812):
      pid = getUserId(username)
      loadresult = load(pid)
      if loadresult[0] == 0:
        data = loadresult[1]
        dinfo = loadresult[2]
        if not "Money" in data:
          data["Money"] = 0
        data["Money"] -= amount
        PlayerData.set(pid, data)
        await interaction.send(f"Removed **${amount}** from **{username}'s money**.")
    else:
      await interaction.send("Nope.", ephemeral = True)

class fulldata(commands.Cog):
  @bot.slash_command(guild_ids=[TESTING_GUILD_ID])
  async def fulldata(interaction: nextcord.Interaction):
    pass
  
  @fulldata.subcommand(description="Rip full player data")
  async def get(interaction: nextcord.Interaction, username: str):
    if nextcord.utils.get(interaction.user.roles, id=1033863011959582812):
      loadresult = load(getUserId(username))
      if loadresult[0] == 0:
        data = loadresult[1]
        dinfo = loadresult[2]
        print(loadresult)
        datatosend = json.dumps(data, indent=4)
        with open('data.txt', 'w') as txttosend:
            txttosend.write(datatosend)
        await interaction.send("**Full data for " + username + ":**", files=[nextcord.File('data.txt')])
    else:
      await interaction.send("You aren't allowed to do that!", ephemeral = True)

  @fulldata.subcommand(description="Completely overwrite full player data (dangerous)")
  async def set(interaction: nextcord.Interaction, username: str, new_data: str):
    if nextcord.utils.get(interaction.user.roles, id=1033863011959582812):
      try:
        PlayerData.set(str(getUserId(username)), json.loads(new_data), users=[getUserId(username)])
      except(json.decoder.JSONDecodeError):
        await interaction.send(f"Invalid JSON data.")
        return
      await interaction.send(f"Completely overwrote data for {username}!")
    else:
      await interaction.send("You aren't allowed to do that!", ephemeral = True)

  @fulldata.subcommand(description="Repair player data! (fully resets it!!!)")
  async def repair(interaction: nextcord.Interaction, username: str):
    if nextcord.utils.get(interaction.user.roles, id=1033863011959582812):
      newdata = {}
      newdata["Money"] = 0
      newdata["xp"] = {}
      newdata["xp"]["FarmingXP"] = 0
      newdata["xp"]["MiningXP"] = 0
      newdata["xp"]["CombatXP"] = 0
      newdata["xp"]["DungeonXP"] = 0

      newdata["inventory"] = {}
      newdata["inventory"]["Basic Hoe"] = {"id": str(uuid.uuid4()), "base": "basichoe"}
      newdata["inventory"]["Simple Pickaxe"] = {"id": str(uuid.uuid4()), "base": "simplepickaxe"}

      newdata["items"] = {}

      newdata["settings"] = {}
      newdata["settings"]["MusicEnabled"] = True
      
      newdata["stats"] = {}
      newdata["stats"]["Playtime"] = 0
      newdata["stats"]["ActiveArmour"] = "none"

      newdata["baninfo"] = {}
      newdata["baninfo"]["banneduntil"] = 0
      newdata["baninfo"]["banreason"] = "Not banned (data repaired from bot)"

      PlayerData.set(str(getUserId(username)), newdata, users=[getUserId(username)])
      await interaction.send(f"Fully reset data for {username}!")
    else:
      await interaction.send("You aren't allowed to do that!", ephemeral = True)

class gameban(commands.Cog):
  @bot.slash_command(guild_ids=[TESTING_GUILD_ID])
  async def gameban(interaction: nextcord.Interaction):
    pass

  @gameban.subcommand(description="Ban a player from Astaria! (duration in hours)")
  async def ban(interaction: nextcord.Interaction, username: str, reason: str, duration: int):
    if nextcord.utils.get(interaction.user.roles, id=1033863011959582812):
      pid = getUserId(username)
      loadresult = load(pid)
      if loadresult[0] == 0:
        data = loadresult[1]
        dinfo = loadresult[2]
        data["baninfo"] = {}
        data["baninfo"]["banneduntil"] = time.time() + duration * 3600
        data["baninfo"]["banreason"] = reason

  @gameban.subcommand(description="Unban a player from Astaria!")
  async def unban(interaction: nextcord.Interaction, username: str):
    if nextcord.utils.get(interaction.user.roles, id=1033863011959582812):
      pid = getUserId(username)
      loadresult = load(pid)
      if loadresult[0] == 0:
        data = loadresult[1]
        dinfo = loadresult[2]
        data["baninfo"] = {}
        data["baninfo"]["banneduntil"] = time.time()

  @gameban.subcommand(description="Check if a player is banned from Astaria!")
  async def check(interaction: nextcord.Interaction, username: str):
    pid = getUserId(username)
    loadresult = load(pid)
    if loadresult[0] == 0:
      data = loadresult[1]
      dinfo = loadresult[2]
      if not "baninfo" in data:
        data["baninfo"] = {}
        data["baninfo"]["banneduntil"] = 0
        data["baninfo"]["banreason"] = "Not banned (data repaired from bot)"
      if data["baninfo"]["banneduntil"] > time.time():
        await interaction.send(f"**{username}** is banned from Astaria! Reason: **{data['baninfo']['banreason']}**. They will be unbanned in **{round((data['baninfo']['banneduntil'] - time.time())/3600, 2)}** hours.")
      else:
        await interaction.send(f"**{username}** is not banned from Astaria!")

bot.run(token)