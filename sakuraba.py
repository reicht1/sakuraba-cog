from redbot.core import commands
from redbot.core import errors
import discord
#from discord.ext import commands
#from discord import errors
import html
import json
import markovify
import os
from os import path
from os import makedirs
from random import randint
from redbot.core.data_manager import bundled_data_path
from redbot.core.data_manager import cog_data_path

#global variables. To be treated as constants
global titleFileName
titleFileName = "titles.txt"
global markovFileName
markovFileName = "markov.json"

class Sakuraba(commands.Cog):
    """Uses Markovify to imitate Motoi Sakuraba"""

    #actions performed when cog is first loaded
    def __init__(self, bot):
        dataPath = str(bundled_data_path(self))
        generatedDataPath = str(cog_data_path(self))

        #see if directory for files exists. If not, make it
        if not os.path.exists(dataPath):
            os.makedirs(dataPath)
        
        #check to see if Markov file exists
        if not os.path.exists(generatedDataPath + '/' + markovFileName):
            print("NOTICE: Markov file does not exist. Checking to see if it can be generated.")
            #if not check to see if titles.txt exists
            if not os.path.exists(dataPath + '/' + titleFileName):
                print("ERROR: Source '" + titleFileName + "' does not exist. Cannot build markov file")
            else:
                print("NOTICE: title file exists, attempting to build Markov file.")
                self.createMarkovFile()            
        self.bot = bot

    #creates markov file which contains markov chains
    def createMarkovFile(self):
        dataPath = str(bundled_data_path(self))
        generatedDataPath = str(cog_data_path(self))     
        with open(dataPath + '/' + titleFileName, 'r') as file:
            model = None
            for line in file:
                line = self.escapeString(line.lower())
                newModel = markovify.Text(line, retain_original=False, state_size=1)
                if model:
                    model = markovify.combine(models=[model, newModel])
                else:
                    model = newModel

            with open(generatedDataPath + '/' + markovFileName, 'w+') as markovFile:
                print("dumped markov file at " + generatedDataPath + '/' + markovFileName)
                json.dump(model.to_json(), markovFile, indent=4)
                
        print("NOTICE: Successfully created Markov file.")

   #html escape string
    def escapeString(self, message):
        message = html.escape(message)
        message = message.replace("(", "&#x28;")
        message = message.replace(")", "&#x29;")
        return message
        
    #unescape string from html codes
    def unescapeString(self, message):
        message = html.unescape(message)
        message = message.replace("&#x28;", "(")
        message = message.replace("&#x29;", ")")
        return message
    
    #see if phrase is in original dictionary
    def findInFile(self, phrase, file):
    #for finding a phrase in a file.
        with open(file, 'r') as openedFile:
            for line in openedFile:
                if line.replace("\n", "").lower().find(phrase.lower()) != -1:
                    return True
        return False

    @commands.command(pass_context=True, no_pm=False)		
    async def sakuraba(self, ctx):
        """Creates a title like Motoi Sakuraba would."""
        dataPath = str(bundled_data_path(self))
        generatedDataPath = str(cog_data_path(self))
        try:
            with open(generatedDataPath + '/' + markovFileName, 'r') as file:
                try:
                    #load data from Markov file
                    jsonData = json.load(file)
                    model = markovify.NewlineText.from_json(str(jsonData))
                    await ctx.trigger_typing()

                    #generate titles until you get one that doesn't already exist in the source corpus
                    while True:
                        resultMessage = model.make_sentence(tries=1000, max_overlap_ratio = 0.45)       
                        resultMessage = self.unescapeString(resultMessage)
                        if self.findInFile(resultMessage, dataPath + '/' + titleFileName):
                            True
                        else:
                            break
                    
                    #randomly assign the title to be either in all caps or with standard title capitolization 
                    if randint(0,1) == 1:
                        resultMessage = resultMessage.upper()
                    else:
                        resultMessage = resultMessage.title()             
                    
                    #output the result
                    print("Sakuraba:" + resultMessage)
                    await ctx.send(resultMessage)
                    
                except ValueError:
                    print("ERROR: Sakuraba: Could not get markov model from user JSON file!")
                    await ctx.send("ERROR: Sakuraba: Could not get markov model from user JSON file!")
                    # I guess the array didn't exist in the text file or something.
                    return
                except KeyError:
                    print("Error: No Sakuraba data loaded.")
                    await ctx.send("Error: No Sakuraba data loaded.")
        except FileNotFoundError:
            print("Error: Sakuraba Markov file does not exist. Try reloading this cog.")
            await ctx.send("Error: Sakuraba Markov file does not exist. Try reloading this cog.")
