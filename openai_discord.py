import os
import random
import discord
from discord.ext.commands import Bot
import openai
import re
import spacy

nlp = spacy.load("en_core_web_sm")

# Get credentials from dotenv file
from dotenv import load_dotenv

load_dotenv()
import asyncio

openai.api_key = os.getenv("OPENAI_API_KEY")
task_running = False

# Use Bot instead of Discord Client for commands
# Give it ALL THE POWER
intents = discord.Intents.all()
client = Bot("!", intents=intents)

whisperword = False
#For safety ;-)
whisperword_user = ""
whisperword_channel = ""
clothing = []
appearance = ""
mood = ""
user_name = ""
user_description = ""
user_clothing = []

'''
TODO: Character location, sitting, standing, in front of, etc.
TODO: Save context to disk
TODO: Context class. Attributes are lists or strings. 
They can be a user attribute, or a bot attribute.
Each attribute can have the following 
* Trigger phrases mapped to specific attribute methods
* Handler for trigger phrases that takes a comment, checks each phrase against the comment (isTrigger) and then triggers the method mapped to the matched phrase.
* Contains shared sanization methods for natural language list comprehension, 
* Iterate each attribute and dynamically build a context string for the user, and a context string for the bot
'''
class CustomAIContextString:
    '''
    Manages the custom attributes which are used to keep context about the AI locally.
    Context is flattened to a string and sent over to OpenAI along with the conversation.
    '''

    #For safety ;-)
    whisperword = False
    whisperword_user =  ""
    whisperword_channel = ""
    
    attribute_values = {}
    
    # Map a phrase with an attribute name to be added to overall context
    trigger_phrases = {
        "clothing",
        "appearance",
        "mood",
        "user_name",
        "user_description",
    }
    
    def check_trigger_phrase(content):
        '''
        Check the content for a trigger phrase
        '''
        '''
        content_lower = content.lower()
        if "take off your" in content_lower:
            content_str = content_lower[content_lower.find("take off your") + 13:].strip()
            content_str = alphabet.sub("",content_str)
            for index, value in enumerate(clothing):
                if content_str in value:
                    clothing.pop(index)
            clothing_to_str = " ".join(clothing)
            print(f"Clothing: {clothing_to_str}")
        if "put on" in content_lower:
            content_str = content_lower[content_lower.find("put on") + 6:].strip()
            content_str = alphabet.sub("",content_str
            clothing.append(content_str)
            clothing_to_str = " ".join(clothing)
            print(f"Clothing: {clothing_to_str}")
        if content_lower.startswith("you are feeling"):
            content_str = content_lower[content_lower.find("you are feeling") + 15:].strip()
            content_str = alphabet.sub("",content_str)
            mood = content_str
            print(f"I am feeling {content_str}")
        if content_lower.startswith("you are a"):
            content_str = content_lower[content_lower.find("you are a") + 9:].strip()
            content_str = alphabet.sub("",content_str)
            appearance = content_str
            print(f"I am a {content_str}")
        if content_lower.startswith("my name is"):
            content_str = content_lower[content_lower.find("my name is") + 10:].strip()
            content_str = alphabet.sub("",content_str)
            user_name = content_str
            print(f"user_name changed to {user_name}")
        if content_lower.startswith("i am"):
            content_str = content_lower[content_lower.find("i am") + 4:].strip()
            content_str = alphabet.sub("",content_str)
            user_description = content_str
            print(f"user_description updated to {user_description}")
            '''
    '''
    def add_trigger_phrase(trigger_phrase, attribute):
        this.trigger_phrases[trigger_phrase] = attribute
        
    def update_trigger_phrase(trigger_phrase, attribute):
        this.trigger_phrases[trigger_phrase] = attribute
        
    def append_trigger_phrase(trigger_phrase, attribute):
        this.trigger_phrases[trigger_phrase].append(attribute)
        
    def remove_trigger_phrase_list_entry(trigger_phrase, attribute):
    '''

async def getAIResponse(prompt):
    api_json = openai.Completion.create(
        engine="text-davinci-001",
        prompt=prompt,
        temperature=0.8,  # big hot takes
        max_tokens=200,
        frequency_penalty=0.5,
    )
    #print(api_json)

    response = api_json.choices[0].text.strip('"')
    return response



@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))


@client.command(aliases=["ai", "generate"])
async def prompt(ctx, string: str):
    await generateSentence(ctx, prompt=string)



@client.event
async def on_message(message):
    global task_running
    global whisperword
    global whisperword_user
    global whisperword_channel
    global mood
    global clothing
    global appearance
    global user_name
    global user_description
    global user_clothing

    name_str = message.author.name if user_name == "" else user_name
    
    await client.process_commands(message)
    alphabet = re.compile('[^a-zA-Z ]')

    content = message.clean_content
    ctx = await client.get_context(message)
    
    # Escape 
    if (
        message.author == client.user
        or len(content) < 2
        or content.startswith("!")
        or content.startswith(".")  # uber bot prefix
    ):
        return

    if (
        "stfu bot" in content
        and message.author.guild_permissions.administrator
    ):
        await message.reply("fine then fuck you")
        print("Stop command issued")
        await client.close()
        task_running = False  # stop being sussy!!
    
    # Turn on configs
    if "whiporwhil_on" in content:
        whisperword = True
        whisperword_user = message.author.name
        whisperword_channel = ctx.channel.id
        print(f"{client.user.name} configs are now open for {whisperword_user} in channel {whisperword_channel}")    
        
    if "whiporwhil_off" in content:
        whisperword = False
        whisperword_user = ""
        whisperword_channel = ""
        print(f"{client.user.name} configs are now closed")
    
    # Commands once configs are on. We let the AI handle the responses to keep things interesting
    if whisperword == True:
        content_lower = content.lower()
        if "take off your" in content_lower:
            content_str = content_lower[content_lower.find("take off your") + 13:].strip()
            content_str = alphabet.sub("",content_str)
            for index, value in enumerate(clothing):
                if content_str in value:
                    clothing.pop(index)
            clothing_to_str = " ".join(clothing)
            print(f"Clothing: {clothing_to_str}")
        if "take off my" in content_lower:
            content_str = content_lower[content_lower.find("take off my") + 11:].strip()
            content_str = alphabet.sub("",content_str)
            for index, value in enumerate(user_clothing):
                if content_str in value:
                    user_clothing.pop(index)
            clothing_to_str = " ".join(user_clothing)
            print(f"{user_name}'s clothing: {clothing_to_str}")
        if content_lower.startswith("i put on"):
            content_str = content_lower[content_lower.find("i put on") + 8:].strip()
            if "," in content_str or "and" in content_str:
                # Ghetto fabulous natural language processing for multiple clothes
                content_str = content_str.replace(" and", ",")
                content_str = content_str.replace(",,", ",")
                [user_clothing.append(article.strip()) for article in content_str.split(",")]
            else: 
                user_clothing.append(content_str)
            user_clothing_to_str = " ".join(user_clothing)
            print(f"{user_name}'s clothing: {user_clothing_to_str}")
        elif "put on" in content_lower:
            content_str = content_lower[content_lower.find("put on") + 6:].strip()
            if "," in content_str or "and" in content_str:
                # Ghetto fabulous natural language processing for multiple clothes
                content_str = content_str.replace("and", ",")
                content_str = content_str.replace(",,", ",")
                [clothing.append(article.strip()) for article in content_str.split(",")]
            else: 
                clothing.append(content_str)
            clothing_to_str = " ".join(clothing)
            print(f"Clothing: {clothing_to_str}")
        if content_lower.startswith("you are feeling"):
            content_str = content_lower[content_lower.find("you are feeling") + 15:].strip()
            content_str = alphabet.sub("",content_str)
            mood = content_str
            print(f"I am feeling {content_str}")
        if content_lower.startswith("you are a"):
            content_str = content_lower[content_lower.find("you are a") + 9:].strip()
            content_str = alphabet.sub("",content_str)
            appearance = content_str
            print(f"I am a {content_str}")
        if content_lower.startswith("my name is"):
            content_str = content_lower[content_lower.find("my name is") + 10:].strip()
            content_str = alphabet.sub("",content_str)
            user_name = content_str
            print(f"user_name changed to {user_name}")
        if content_lower.startswith("i am"):
            content_str = content_lower[content_lower.find("i am") + 4:].strip()
            user_description = content_str
            print(f"user_description updated to {user_description}")

    # random chance to respond to a message, always respond if mentioned. Modified to always respond
    # if random.randint(0, 100) < 25 or client.user.mentioned_in(message):

    # in order of chain: third latest reply - second latest reply - latest reply
    # this is fucking stupid
    messages = ["", "", ""]

    # who is involved in the chain
    all_mentions = message.mentions
    all_mentions.append(message.author)

    

    bot_mention = "@" + client.user.display_name
    #print("mention " + bot_mention)
    if content.startswith(bot_mention):
        content = content[len(bot_mention):].strip()

    # add author name to prompt
    messages[2] = f"{message.author.name}: {content}"

    # check if message is a reply
    if message.reference is not None:
        # also contain the referenced message as extra context for the prompt
        reference_message = await ctx.channel.fetch_message(
            message.reference.message_id
        )
        messages[1] = f"{reference_message.author.name}: {reference_message.clean_content}"
        all_mentions += reference_message.mentions

        # further down the rabbit hole
        if reference_message.reference is not None:
            first_in_chain = await ctx.channel.fetch_message(
                reference_message.reference.message_id
            )
            messages[
                0
            ] = f"{first_in_chain.author.name}: {first_in_chain.clean_content}"
            all_mentions += first_in_chain.mentions

    # Start the prompt with necessary context
    # whisperword represents keywords to change the nature of the prompt. 
    if whisperword == True and whisperword_user == message.author.name and whisperword_channel == ctx.channel.id:
        clothing_str = ""
        mood_str = ""
        appearance_str = ""
        user_description_str = ""
        user_clothing_str = ""
        if len(clothing) != 0:
            clothing_to_str = ", ".join(clothing)
            clothing_str = f"You are wearing {clothing_to_str}. "
        if len(user_clothing) != 0:
            user_clothing_to_str = ", ".join(user_clothing)
            user_clothing_str = f"{name_str} is wearing {user_clothing_to_str}. "
        if mood != "":
            mood_str = f"You are feeling {mood}. "
        if appearance != "":
            appearance_str = f"You are a {appearance}. "
        if user_description != "":
            user_description_str = f"{name_str} is {user_description}. "
        user_prompt = f"Your name is {client.user.name}. {appearance_str}{mood_str}{clothing_str}You are talking to {name_str}. {user_description_str}{user_clothing_str}"
    else:
        name_str = message.author.name if user_name == "" else user_name
        user_prompt = f"Your name is {client.user.name}. You are talking to {name_str}. "

    # Add the last bit of the prompt (currently "GreggsBot: ")
    user_prompt += "\n".join(messages).strip() + f"\n{client.user.display_name}: "
    print(user_prompt)

    # we have finished building a prompt, send it to the API
    await generateSentence(ctx, message, user_prompt)



# Actual function to generate AI sentences
async def generateSentence(ctx, respond_to=None, prompt=""):
    if len(prompt) == 0:
        return


    async with ctx.typing():
        #print("Querying API...")

        response = await getAIResponse(prompt)

        if response == "":
            print("Error generating sentence. Skill issue")
            return

    # either reply to a user or just send a message
    if respond_to != None:
        await respond_to.reply(response)
    else:
        await ctx.send(response)


# Run bot
print("Logging in...")
client.run(os.environ["DISCORD_TOKEN"])
