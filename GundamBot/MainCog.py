from Gundam import Gundam
import random
import discord
from discord.ext import tasks, commands
import csv
import requests
from bs4 import BeautifulSoup
import io
import aiohttp
import re
import asyncio

class MainCog(commands.Cog, name='General'):
    def __init__(self, bot):
        self.bot = bot
        self.listOfGundams = []
        self.GOTDChannels = []

        # load list of gundams into memory
        with open('Gundams.csv', 'r', encoding='ascii') as f:
            csv_reader = csv.reader(f, delimiter=',')
            for row_values in csv_reader:
                gundam = Gundam(row_values[0], row_values[1])
                self.listOfGundams.append(gundam)
        
        # if there were any channels subscribed to GotD, load them into memory
        with open('GOTDChannels.csv', 'r') as f:
            for line in f.readlines():
                self.GOTDChannels.append(int(line))
        
        # pylint: disable=no-member
        self.gundamOfTheDayTask.start()
    
    def cog_unload(self):
        # pylint: disable=no-member
        self.gundamOfTheDayTask.cancel()

    #################################################
    # Bot Commands
    #################################################

    # !gundam random
    random_HELP = 'Links a random Gundam ONCE within channel'
    @commands.command(name='random', help=random_HELP)
    async def randomGundam(self, ctx):
        randomGundam = random.choice(self.listOfGundams)
        response = randomGundam.name + ' ' + randomGundam.URL
        await ctx.send(response)
    
    # !gundam gtg
    random_HELP = 'I give you an image, you GUESS THAT GUNDAM (gtg)!'
    @commands.command(name='gtg', help=random_HELP)
    async def guessThatGundam(self, ctx):

        randomGundam = random.choice(self.listOfGundams)

        # send imageURL of randomly chosen Gundam
        try:
            page = requests.get(randomGundam.URL)
            print('randomGundam.name: ' + randomGundam.name)
            print('randomGundam.URL: ' + randomGundam.URL)
            soup = BeautifulSoup(page.text, features="html.parser")
            tag = soup.find("meta",  property="og:image")
            imgURL = tag['content']
            async with aiohttp.ClientSession() as session:
                async with session.get(imgURL) as resp:
                    if resp.status != 200:
                        return await ctx.send('Sorry. Guess That Gundam is not working right now because Gundam Wikia seems to be down. Contact cherry#1048 for help!')
                    data = io.BytesIO(await resp.read())
                    await ctx.send('Guess This Gundam!',file=discord.File(data, 'guessthatgundam.png'))
            
            # define whether or not user is correct or not
            def check(m):
                guess = m.content
                answer = randomGundam.name
                answer = re.sub("(?i)Gundam","", answer)
                answer = re.sub("(?i)Gundam ","", answer)
                answer = re.sub("(?i)(MSV only)","", answer)
                answer = re.sub("(?i)(MSV/Manga only)","", answer)
                answer = re.sub("(?i)(Manga only)","", answer)
                answer = re.sub("(?i)(Game only)","", answer)
                answer = re.sub("(?i)(Novel only)","", answer)
                answer = re.sub("(?i)(OVA only)","", answer)
                answer = re.sub("(?i)(Manga/Novel only)","", answer)
                answer = re.sub("(?i)(MSV/Game only)","", answer)
                answer = re.sub("(?i)(Hobby Japan only)","", answer)
                answer = answer.replace("\"","")
                answer = answer.replace("(","")
                answer = answer.replace(")","")
                answer = re.sub(r'[^\x00-\x7f]',r'', answer)
                answer = answer.replace("  "," ")
                answerKeywords = answer.lower().split()
                guessKeywords = guess.lower().split()

                return any(item in guessKeywords for item in answerKeywords)

            # await for user reply
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=30.0)
            except asyncio.TimeoutError:
                await ctx.send('Too much time has passed. Try again next time, {.author}'.format(ctx) +  '! Full Answer: ' + randomGundam.name)
            else:
                if msg.author == self.bot.user: # do not reply to self
                    return
                await ctx.send('Good job, {.author}! Full Answer: '.format(msg) + randomGundam.name)
        except requests.exceptions.RequestException as e:
            await ctx.send('Sorry. Guess That Gundam is not working right now. Contact cherry#1048 for help!')
            print(e)

    # !gundam addGOTD
    addGOTD_HELP = 'Links a random Gundam EVERY 24 HOURS within channel'
    @commands.command(name='addGOTD', help=addGOTD_HELP)
    async def setChannelForGundamOfTheDay(self, ctx):
        channel = ctx.channel
        if channel.id not in self.GOTDChannels:
            # Save channel id into memory
            self.GOTDChannels.append(channel.id)

            randomGundam = random.choice(self.listOfGundams)
            response = 'Random Gundam Of The Day: ' + randomGundam.name + ' ' + randomGundam.URL
            await ctx.send('You have successfully added GOTD (Gundam Of The Day) to this channel! \nA random Gundam will be sent to this channel EVERY 24 HOURS! \nHere\'s a sneak peek 👀 \n' + response)

            # Write channel id into persistent memory, even if bot gets turned off.
            # Since this takes a while, move it after ctx.send()
            with open('GOTDChannels.csv', 'a+') as f:
                # Move read cursor to the start of file.
                f.seek(0)
                # If file is not empty then append '\n'
                data = f.read(100)
                if len(data) > 0:
                    f.write("\n")
                # Append text at the end of file
                f.write(str(channel.id))
        else:
            await ctx.send('Oops! Looks like you already enabled GOTD for this channel!')
    
    # !gundam removeGOTD
    removeGOTD_HELP = 'Removes linking a random Gundam EVERY 24 HOURS within channel'
    @commands.command(name='removeGOTD', help=removeGOTD_HELP)
    async def removeChannelForGundamOfTheDay(self, ctx):
        channel = ctx.channel
        if channel.id not in self.GOTDChannels:
            await ctx.send('You haven\'t even added GOTD for this channel yet! You cannot remove what you have not added.')
        else:
            # Remove channel id into memory
            self.GOTDChannels.remove(channel.id)

            await ctx.send('You have successfully removed GOTD from this channel... you monster. Even Bright has never slapped me like you did.')

            # Write channel id into persistent memory, even if bot gets turned off
            # Since this takes a while, move it after ctx.send()
            with open("GOTDChannels.csv", "r") as f:
                lines = f.readlines()
            with open("GOTDChannels.csv", "w") as f:
                for line in lines:
                    if line.strip("\n") != str(channel.id):
                        f.write(line)

    #################################################
    # Event Handlers
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send('Thanks for inviting me to the server \'{}\'! Type \'!gundam help\' for all of my commands! \nContact cherry#1048 for questions, issues, concerns, etc.'.format(guild.name))
                break

    #################################################
    # Background Tasks
    @tasks.loop(hours=24) #hours=24
    async def gundamOfTheDayTask(self):
        randomGundam = random.choice(self.listOfGundams)
        response = 'Random Gundam Of The Day: ' + randomGundam.name + ' ' + randomGundam.URL
        print('Printing all channels for GOTD:')
        print(self.GOTDChannels)
        for GOTDChannel in self.GOTDChannels:
            channel = self.bot.get_channel(GOTDChannel)
            if channel is not None:
                await channel.send(response)
            else:
                print('ERROR')
    
    @gundamOfTheDayTask.before_loop
    async def before(self):
        await self.bot.wait_until_ready()
        print("Sending Gundam of the Day...")