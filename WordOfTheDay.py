from bs4 import BeautifulSoup as soup
import requests
from requests import HTTPError
from discord.utils import get
import string
import datetime
import discord
from discord.ext import commands
from discord.errors import HTTPException
import re
import os

client = commands.Bot(command_prefix="!")

# define Python user-defined exceptions
class Error(Exception):
    """Base class for other exceptions"""
    pass

class dateFormatIssue(Error):
    """Raised when the date format is incorrect"""
    pass

@client.event
async def on_ready():
    print("Word of the Day bot is ready")

@client.event
async def on_message(message):
    try:
        # if(str(message.author) != "Word of the Day#2026"):
        #     command = message.content.lower()[0:message.content.find(" ")]
        if message.content.lower()[0:5] == ('!help'):
            await message.channel.send("I'm a super basic bot. here are your options.... \n \n"
                                       "!help\t-->\tyou enetered this, you know this pulls up the help menu \n"
                                       "!word\t-->\tthis command will provide a word of the day... \n"
                                       "!word MM/DD/YYYY \t-->\t this command will provide a word of the day "
                                       "for the date specified in the format specified \n"
                                       "!define {Word or phrased to be defined} \t-->\t This command will define"
                                       " a word or phrase you declare after the command.\n"
                                       "!udefine {Word or phrased to be defined} \t-->\t This command"
                                       " will define a word or phrase... but from Urban Dictionary"
                                       "\n\n"
                                       "That concludes the options")
        if message.content.lower()[0:5] == ("!word"):
            dictionarySite = "https://www.merriam-webster.com/word-of-the-day"
            date = message.content.lower()[5:].lstrip()
            if date:
                try:
                    formattedDateObj = datetime.datetime.strptime(date, '%m/%d/%Y')
                    dictionarySite += "/" + str(formattedDateObj.date())
                except:
                    raise dateFormatIssue
            page_html = requests.get(dictionarySite, headers={'User-Agent': 'Mozilla/5.0'}).text
            page_soup = soup(page_html, "html.parser")
            word = page_soup.find("title")
            onlyWord = page_soup.find("div",class_="word-and-pronunciation")
            literaryElement = page_soup.find("span", class_="main-attr")
            pronunciation = page_soup.find("span", class_="word-syllables")
            example = page_soup.find("div", class_="wotd-examples")
            onlyWord = onlyWord.text.replace("play", "").strip()
            definitions = {}

            for iteration,tag in enumerate(page_soup.find_all("p")):
                if tag.text[0:1].isdigit() or tag.text[0:1] == ":":
                    definitions[iteration] = tag.text

            finalmessage = ""
            finalmessage += word.string + "\n"
            finalmessage += literaryElement.string + "\n"
            finalmessage += "Pronunciation: " + pronunciation.text + "\n"
            finalmessage += "Definition(s): \n "
            for definition in definitions:
                finalmessage += definitions[definition] + "\n"
            finalmessage += "Example: " + example.text.replace("Examples\n", "").replace(onlyWord, "**__"+onlyWord+"__**")
            finalmessage += dictionarySite
            await message.channel.send(finalmessage)
        if message.content.lower()[0:7] == "!define":
            defineWord = message.content.lower()[7:].lstrip()
            finalmessage = ""
            if not defineWord:
                finalmessage+= "Please include a word to be defined"
            else:
                site = "https://www.merriam-webster.com/dictionary/"+ defineWord.replace(" ", "%20") + "?src=search-dict-hed"
                try:
                    html_text = requests.get(site, headers={'User-Agent': 'Mozilla/5.0'}).text
                    definitionSoup = soup(html_text, "html.parser")
                    defins = definitionSoup.find_all("span", class_="dt")
                    pronunciation = definitionSoup.find("span", class_="pr")
                    literaryElement = definitionSoup.find("a", class_="important-blue-link")
                    suggestions = definitionSoup.find("p", class_="spelling-suggestions")
                    examples = definitionSoup.find_all("span", class_="ex-sent")
                    if literaryElement is not None:
                        finalmessage += "Word: " +"**" + defineWord.upper() + "**" + "\t-\t" + literaryElement.text + "\n "
                    if pronunciation is not None:
                        finalmessage += "Pronunciation: " + pronunciation.text + "\n"
                    for iteration, defin in enumerate(defins):
                        if defin.text.strip() != "":
                            finalmessage += re.sub(' +', ' ', defin.text.replace("\n", " - ").strip()) + "\n"
                        if iteration ==2:
                            break
                    for example in examples:
                        if(defineWord in example.text.strip()):
                            finalmessage += "Example in a sentence: \n" + example.text.strip().replace(defineWord, "**__"+defineWord+"__**") + "\n"
                            break;
                    if suggestions is not None:
                        finalmessage += "Could not find the word " + defineWord + " in the dictionary, you may have spelled it wrong,\n did you mean one of the following words?\n"
                        suggestions = suggestions.text.replace(" ", ", ")
                        finalmessage += suggestions + "\n"
                    finalmessage += "Reference site: \n" + site
                except HTTPError as err:
                    if err.code == 404:
                        finalmessage += "Could not find word in the dictionary,"
                        await message.channel.send(finalmessage)
                    else:
                        await message.channel.send("Could not find word in the dictionary, but with style...")
                except AttributeError as error:
                    await message.channel.send("Something went wrong parsing the website for a Definition. Just saw it live Sry." + str(error))
                except Exception as exception:
                    await message.channel.send("Just a generic Exception... my bad.\n" + str(exception))
            await message.channel.send(finalmessage)
        if message.content.lower()[0:8]=="!udefine":
            defineWord = message.content.lower()[8:].lstrip()
            finalmessage = ""
            if not defineWord:
                site =""
                finalmessage += "Please include a word to be defined"
            else:
                site = "https://www.urbandictionary.com/define.php?term=" + defineWord.replace(" ","%20")
                try:
                    #requests.headers{'User-Agent': 'Mozilla/5.0','content-length':'2000'}
                    html_text = requests.get(site, headers={'User-Agent': 'Mozilla/5.0'}).text
                    definitionSoup = soup(html_text, "html.parser")
                    defins = definitionSoup.find_all("div", class_="meaning")
                    examples = definitionSoup.find_all("div",class_="example")
                    finalmessage += "**" + defineWord.upper() + "** - " + "\n"
                    #get rid of the word of the day definition
                    if defins:
                        defins.pop(1)
                    else:
                        finalmessage += "Couldn't find that word/phrase. Go to the following site to add one: \n"
                    for iteration, defin in enumerate(defins):
                        finalmessage += "\t: " + defin.text.replace("\n", "").strip() + "\n"
                        if iteration == 2:
                            break
                except HTTPError as err:
                    if err.code == 404:
                        finalmessage += "Could not find word in the dictionary,"
                        await message.channel.send(finalmessage)
                    else:
                        await message.channel.send("Could not find word in the dictionary, but with style...")
                except AttributeError as error:
                    await message.channel.send(
                        "Something went wrong parsing the website for a Definition. Just saw it live Sry." + str(error))
                except Exception as exception:
                    await message.channel.send("Just a generic Exception... my bad.\n" + str(exception))
            finalmessage+= site
            await message.channel.send(finalmessage)
        if message.content.lower()[0:9] == "!auxverbs":
            await message.channel.send("Auxillary Verbs are: " + "am, is, are, was were, "
                                                                 "being, been, be, Have, has, "
                                                                 "had, do, does, did, will, would, "
                                                                 "shall, and should")
        if message.content.lower()[0:16] == "!whosucksatchess" or message.content.lower()[0:6] == "!chess":
            await message.channel.send("Harry sucks at Chess")
        else:
            aux_verbs = ["am", "is", "are", "was" "were", "being", "been", "be", "Have",
                         "has", "had", "do", "does", "did", "will", "would", "shall", "should"]
            if str(message.guild) == "Deez-Bois" and str(message.author) != "DictionaryDick#2026":
                if "ass " in message.content:
                    firstAssLocation = message.content.find("ass ")
                    phrase = message.content[message.content.find("ass "):].replace("ass ", "ass!")
                    firstSpace = phrase.find(" ")
                    if firstSpace == -1:
                        assPhrase = phrase.replace("!", "-")
                    else:
                        assPhrase = phrase[:firstSpace + 1].replace("!", "-")
                    if assPhrase[len(assPhrase.rstrip())-1:].rstrip() == "s":
                        begin = "What are "
                    else:
                        begin = "What's an "
                    if phrase[assPhrase.find('-')+1:len(assPhrase)].rstrip() not in aux_verbs:
                        await message.channel.send(begin + assPhrase.rstrip() + "?", file=discord.File('spongebob.png'))
    except dateFormatIssue:
        await message.channel.send(
            "Incorrect date format included, if you want a word of the day for a specific day it"
            " must be in the following format - \"MM/DD/YYYY\"")
    except AttributeError:
        await message.channel.send("You entered a value that isn't currently supported, likely an issue with a date"
                                   " for the word of the day being too far in the past or a future date.")
    except Exception as exception:
        await message.channel.send("Discord's API can't handle this many definitions, if you want to know"
                                   " the definitions to this word go to: \n" + site + "\n" + str(exception))

key = os.environ.get('DISCORD_DICTIONARY_BOT_KEY')
client.run(key)