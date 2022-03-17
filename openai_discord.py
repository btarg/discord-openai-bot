from cmath import e
from email import message
import logging
import os
from click import FileError
import discord
from discord.ext.commands import Bot
from discord.ext.commands import Context
import openai
import spacy
import json
from conversation_history import ConversationHistory

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


global_contexts = []
CONTEXT_FOLDER =".\\contexts\\"
MAX_CONVERSATION_HISTORY = 10
nl = "\n"

# Define the log format
log_format = (
    '[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s')

# Define basic configuration
logging.basicConfig(
    # Define logging level
    level=logging.INFO,
    # Declare the object we created to format the log messages
    format=log_format,
    # Declare handlers
    handlers=[
        logging.StreamHandler()
    ]
)

class CustomAIContext:
    '''
    Manages the custom attributes which are used to keep context about the AI and environment locally.
    Attributes are upated using trigger phrases within proces_triggers() coming in on content form Discord message. 
    Each trigger is linked to a method that points at a specific attribute to update in the mapping table.
    
    Each attribute is essentially one human sentence to include with the call to OpenAI.
    Some attributes are multi-value and there's special handling for that. They get flattened out.
    Each attribute has its own pretty print phrase as the first element in the tuple. It's prefixed to the pretty 
    print string in front of the data.

    Context should always be in this format:
    "You are {bot name}. {attribute strings}. You are talking to [user name]. {attribute strings}"

    Example: "You are Joebob. You are a junky clown. You are wearing a clown suit, a clown hat. You are talking to 
    Jamin. Jamin is a human male. Jamin is wearing a bananahammock, a windbreaker."
    '''
    
    user_attributes = []
    bot_attributes =  []
    conversation_history = ConversationHistory(5)

    trigger_phrases_maps = {}

    whisperword = False
    whisperword_user = ""
    whisperword_channel = ""

    my_funcs = locals()

    """
    Utility methods
    """
    def trim_triggger_content(self, trigger_phrase, content):
        '''
        Return the text after the trigger phrase
        '''
        phrase_length = len(trigger_phrase)
        content_value = content[content.find(trigger_phrase) + phrase_length:].strip()
        return content_value
    
    def log_attribute_change(self, attribute, content_value):
        content_value_str = content_value
        if type(content_value) is list:
            content_value_str = " ".join(content_value)
        logging.info(f"{attribute}: {content_value_str}")

    """
    Attribute update classes linked from trigger map. make sure all references to attribute_value use index [1] 
    """

    def remove_entry_from_attribute_list(self, attribute_value, content, trigger_phrase):
        '''
        Find any entry containing content_value and remove the first match
        '''
        content_value: str
        content_value = self.trim_triggger_content(trigger_phrase, content)

        # special conditions. Yay. 
        content_value = content_value.replace("my","")
        content_value = content_value.replace("your","")
        content_value = content_value.replace("our","")
        content_value = content_value.replace("the","")

        if content_value.startswith("a "):
            content_value = content_value.replace("a ","")
        
        for index, value in enumerate(attribute_value[1]):
            if content_value in value:
                attribute_value[1].pop(index)
                self.log_attribute_change(attribute_value, content_value)
                return

    def add_entry_to_attribute_list(self, attribute_value, content, trigger_phrase: str):
        # Gate adding things only if sentence starts with them.
        if content.startswith(trigger_phrase.removesuffix("*")):
            content_value = content
            if trigger_phrase.endswith("*") == False:
                content_value = self.trim_triggger_content(trigger_phrase, content)
                
            user_name = self.user_attributes["name"][1]
            content_value = content_value.replace("i have",f"{user_name} has")
            content_value = content_value.replace("i am",f"{user_name} is")

            # attribute[1] is the value itself
            attribute_value[1].append(content_value)

    def set_attribute_value(self, attribute_value, content, trigger_phrase):
        content_value = self.trim_triggger_content(trigger_phrase, content)
        attribute_value[1] = content_value

    ''' 
    Context Loading and Saving
    '''

    def save_context(self, bot_context_save_name) -> str:
        with open(f"{CONTEXT_FOLDER}{self.whisperword_user}_{bot_context_save_name}.botctx", "w") as file:
            output = json.dumps({
                "user_attributes": self.user_attributes,
                "bot_attributes": self.bot_attributes,
                "whisperword": self.whisperword,
                "whisperword_user": self.whisperword_user,
            })
            file.write(output)
        return output

    def load_context(self, bot_context_save_name):
        try:
            with open(f"{CONTEXT_FOLDER}{self.whisperword_user}_{bot_context_save_name}.botctx", "r") as file:
                context = json.loads(file.read())
        except Exception as err:
            raise Exception(err)

        if self.whisperword_user == context["whisperword_user"]:
            for userattr in context["user_attributes"]:
                self.user_attributes[userattr][1] = context["user_attributes"][userattr][1]
            for botattr in context["bot_attributes"]:
                self.bot_attributes[botattr][1] = context["bot_attributes"][botattr][1]
            self.update_trigger_phrase_maps()
            return "Loaded successfully"
        else:
            raise NameError("Context is for a different user.")


    def list_context(self):
        file_list = os.listdir(f"{CONTEXT_FOLDER}")
        ctx_files = [
            file.replace(".botctx","") for file in file_list 
            if file.endswith(".botctx") and file.startswith(self.whisperword_user)
        ]
        ctx_files = [file.replace(f"{self.whisperword_user}_","") for file in ctx_files]
        return ctx_files

    def context_command(self, content) -> str:
        '''
        Process an incoming .[command] message
        '''
        bot_ctx = self

        if (".context.help" in content):
            return "context.[get[] save.[bot|user].[clothing|description] load.[bot|user].[clothing|description]]"

        if (".context" == content):
            return bot_ctx.get_prompt("")
        
        if (content.startswith(".context.load")):
            value = content[content.find(" "):].strip()
            try:
                self.load_context(value)
                return f"I've performed the operation: load the context as {value}"
            except Exception as err:
                return f"{err}"

        if (content.startswith(".context.save")):
            value = content[content.find(" "):].strip()
            if value == "":
                return "Not saved. Name was empty."
            bot_ctx.save_context(value)
            return f"I've performed the operation: save the context as {value}"
            
        if (".context.get" == content):
            return bot_ctx.get_prompt("")
        
        if (".context.list" == content):
            context_list = bot_ctx.list_context()
            return f"Here's the contexts I have: {context_list}"

        if (".context.reset" == content):
            bot_ctx.__init__(self.whisperword_user, self.bot_attributes["name"][1], self.whisperword_channel)
            return f"I've performed the operation: reset the context"

    def proces_content_for_triggers(self, content: str):
        '''
        Trigger phrase Dict has the trigger phrases stored as keys with function calls to update attributes as the values.
        Why did I do it that way? Because i have no idea what I'm doing.

        Iterate over each trigger key and check to see if it matches something in the content. If it does,
        then call the matching method and pass the content along.

        Methods are called with the magic of locals()
        '''

        content = content.lower()
        if content.endswith("."):
            content = content[:len(content)-1]

        for trigger_phrase in self.trigger_phrases_maps:
            trigger_phrase = trigger_phrase.lower()
            if trigger_phrase.replace("*", "") in content:
                attribute_value = self.trigger_phrases_maps[trigger_phrase][0]
                method = self.trigger_phrases_maps[trigger_phrase][1]
                self.my_funcs[method](self, attribute_value, content, trigger_phrase)
                self.save_context("autosave")
                logging.info(f"triggered {trigger_phrase}")
                break
    
    #TODO: Create a method to determine subject and object

    def get_prompt(self, content):
        '''
        Get the AI prompt. 

        Example: "You are Joebob. You are a junky clown. You are wearing a clown suit, a clown hat. You are talking to 
        Jamin. Jamin is a human male. Jamin is wearing a bananahammock, a windbreaker."
        '''
        bot_name = self.bot_attributes["name"][1]
        user_name = self.user_attributes["name"][1]
        context_str = ""
        bot_discussion_context_str = ""
        user_discussion_context_str = ""
        history_context_str = ""

        # Iterate all the bot attributes. 
        # attr[0] is the prefix phrase, it should exist on all attributes
        # attr[1] is the attribute data, it might be empty. It can be a list or a string.
        for attr in self.bot_attributes.values():
            if type(attr[1]) == list:
                if len(attr[1]) != 0:
                    bot_discussion_context_str += attr[0].replace("bot_name", bot_name)
                    bot_discussion_context_str += ", ".join(attr[1])
                    bot_discussion_context_str += ". "
            elif attr[1] != "":
                bot_discussion_context_str += attr[0].replace("bot_name", bot_name)
                bot_discussion_context_str += attr[1]
                bot_discussion_context_str += ". "
        
        # Same exact thing for user attributes. Just replace user_name keyword
        for attr in self.user_attributes.values():
            if type(attr[1]) == list:
                if len(attr[1]) != 0:
                    user_discussion_context_str += attr[0].replace("user_name", user_name)
                    user_discussion_context_str += ", ".join(attr[1])
                    user_discussion_context_str += ". "
            elif attr[1] != "":
                user_discussion_context_str += attr[0].replace("user_name", user_name)
                user_discussion_context_str += attr[1]
                user_discussion_context_str += ". "
        
        context_str = f"Provide only one response as yourself \n" # Because the bot likes to respond for the user sometimes. 
        
        # Make sure everything ends with a newling
        user_discussion_context_str += nl
        bot_discussion_context_str += nl

        # Get the history to append
        history_context_str = self.conversation_history.history_to_str()

        # Add prompts for the targets
        target_prompts = f"{user_name}: {content}{nl}{client.user.display_name}: "

        # Bring everything together
        context_str = f"{bot_discussion_context_str}{user_discussion_context_str}{history_context_str}{target_prompts}"

        return context_str
    
    def update_trigger_phrase_maps(self):
        # attribute phrase appended with a * indicates the attribute phrase is persisted with the rest of the data. This generally requires
        # TODO: COMPLICATED: allow for multiple prepositional phrases.
        # TODO: Create environment attributes separate of user
        self.trigger_phrases_maps = {
            "my name is"                    : [self.user_attributes["name"], "set_attribute_value"],
            "i put on"                      : [self.user_attributes["clothing"], "add_entry_to_attribute_list"], #TODO: use NLP to allow for "i put [a thing] on. Assume the object is myself if none."
            "i take off"                    : [self.user_attributes["clothing"], "remove_entry_from_attribute_list"],
            "you are wearing"               : [self.bot_attributes["clothing"], "add_entry_to_attribute_list"],
            "you are no longer wearing"     : [self.bot_attributes["clothing"], "remove_entry_from_attribute_list"],
            "put on"                        : [self.bot_attributes["clothing"], "add_entry_to_attribute_list"],
            "take off your"                 : [self.bot_attributes["clothing"], "remove_entry_from_attribute_list"], #TODO: I really need to channel "take off" phrase with subject object NLP conditions rather than handling it here
            "you are no longer"             : [self.bot_attributes["description"], "remove_entry_from_attribute_list"],
            "you no longer have"            : [self.bot_attributes["description"], "remove_entry_from_attribute_list"],
            "you are*"                      : [self.bot_attributes["description"], "add_entry_to_attribute_list"],
            "you have*"                     : [self.bot_attributes["description"], "add_entry_to_attribute_list"],
            "i am no longer"                : [self.user_attributes["description"], "remove_entry_from_attribute_list"],
            "i no longer have"              : [self.user_attributes["description"], "remove_entry_from_attribute_list"],
            "i am*"                         : [self.user_attributes["description"], "add_entry_to_attribute_list"],
            "i have*"                       : [self.user_attributes["description"], "add_entry_to_attribute_list"],
            "we are no longer "             : [self.user_attributes["environment"], "remove_entry_from_attribute_list"],
            "we are*"                       : [self.user_attributes["environment"], "add_entry_to_attribute_list"],
            "there are no longer"           : [self.user_attributes["environment"], "add_entry_to_attribute_list"],
            "there are*"                    : [self.user_attributes["environment"], "add_entry_to_attribute_list"],
            "there is no longer"            : [self.user_attributes["environment"], "add_entry_to_attribute_list"],
            "there is*"                     : [self.user_attributes["environment"], "add_entry_to_attribute_list"],
        }
    ''' 
    Notes on remodeling this using NLP or some other possibly better method.
    Problem 1: reconstructing the sentence in the proper voice - first, second, or third person.
        Ex: User input: "I am a squirrel with a voracious appetite."
    More Simplistic Approach: have just one list of attribute phrases, which are stored when they hit trigger phrases.
        Is removing stuff mor interesting in this approach? 
    
    One thing to mention about the existing approach is that there's really two types of triggers going on here:
        1. Imperative: put on, take off. These initiate a change in state.
            a. this could be extended further into "can you", "would you"
        2. Declaratives: you are, i am, i have, there is, we are
        Each of these then has a negated counterpart.

    Single state objects: a specific user can only be in one location
    I would love to be able to handle state based stuff like this
        "I sit down on the bed". This could be a single entry string and update as things are going on. Could use NLP here 
    '''


    def __init__(self, user_name, bot_name, channel_id):
        """
        Create a new bot context for the user in the specific channel.
        """

        self.user_attributes = {
            "name": ["You are talking to ",""],
            "description": ["", []],
            "clothing": [f"user_name is wearing ", []],
            "environment":["", []],
        }

        self.bot_attributes = {
            "name": ["Your name is ", ""],
            "description":["",[]],
            "clothing":["You are wearing ", []],
            "mood":["You are feeling ", []],
        }

        self.update_trigger_phrase_maps()

        self.whisperword = True
        self.whisperword_user = user_name
        self.whisperword_channel = channel_id
        self.bot_attributes["name"][1] = bot_name
        self.user_attributes["name"][1] = user_name


async def send_message(ctx: Context, content: str):
    '''
    Send Discord message. If >2000 characters, split message.
    '''
    if len(content) > 2000:
        logging.warning("Message too long to send to discord. Splitting message")
        message = ""
        sentences = content.split(".")
        for sentence in sentences:
            if len(message) + len(sentence) < 2000:
                message += sentence
            else:
                await ctx.send(message)
                message = ""
                message += sentence
    else:
        message = content
    await ctx.send(message)



async def getAIResponse(prompt):
    api_json = openai.Completion.create(
        engine="text-davinci-001",
        prompt=prompt,
        temperature=0.8,  # big hot takes
        max_tokens=200,
        frequency_penalty=0.5,
    )
    logging.debug(api_json)

    response = api_json.choices[0].text.strip('"')
    return response



@client.event
async def on_ready():
    logging.warning("We have logged in as {0.user}".format(client))


@client.command(aliases=["ai", "generate"])
async def prompt(ctx, string: str):
    await generateSentence(ctx, prompt=string)




@client.event
async def on_message(message):
    global conversation_history
    global global_contexts
    await client.process_commands(message)
    content = message.clean_content
    ctx = await client.get_context(message)
    

    # Escape 
    if (
        message.author == client.user
        or len(content) < 2
        or content.startswith("!")
        # or content.startswith(".")  # uber bot prefix
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

    
    # Check if current user has a global context object for the chatbot in the channel they are communicating in. 
    # If not, create one for the channel/user combo. This helps maintain separation of contexts so people's 
    # fantasies don't play out in some public channel. Not that people would use this bot for anything perverse
    # they wouldnt share publicly. I totally didnt build this for that exact purpose. 
    bot_ctx: CustomAIContext
    if len(global_contexts) != 0:
        for context in global_contexts:
            if context.whisperword_user == message.author.name and context.whisperword_channel == ctx.channel.id:
                bot_ctx = context
                logging.info(f"on_message: using existing context for {message.author.name} in channel {ctx.channel.id}")             
        if bot_ctx == None:
            global_contexts.append(CustomAIContext(message.author.name, client.user.name, ctx.channel.id))
            bot_ctx = global_contexts[len(global_contexts)-1]
            logging.warning(f"on_message: created new context for {message.author.name} in channel {ctx.channel.id}")        
    else:
        global_contexts.append(CustomAIContext(message.author.name, client.user.name, ctx.channel.id))
        bot_ctx = global_contexts[len(global_contexts)-1]
        logging.warning(f"on_message: created new context for {message.author.name} in channel {ctx.channel.id}")

    if content.startswith(".context"):
        await send_message(ctx, bot_ctx.context_command(content))
        return

    if content.startswith(".history"):
        await send_message(ctx, bot_ctx.conversation_history.history_command(content))
        return
        

    bot_mention = "@" + client.user.display_name
    logging.debug("on_message: mention " + bot_mention)
    if content.startswith(bot_mention):
        content = content[len(bot_mention):].strip()

    # Start the prompt with necessary context
    # whisperword represents keywords to change the nature of the prompt. We're gating this with a special keyword.
    if bot_ctx.whisperword == True and bot_ctx.whisperword_user == message.author.name and bot_ctx.whisperword_channel == ctx.channel.id:
        bot_ctx.proces_content_for_triggers(content)
        user_prompt = bot_ctx.get_prompt(content)
        logging.info(f"on_message: user_prompt:{nl}{user_prompt}")
    else:
        name_str = message.author.name
        user_prompt = f"on_message: Your name is {client.user.name}. You are talking to {name_str}. "

    response = await generateSentence(ctx, user_prompt)

    # Save history
    bot_ctx.conversation_history.append_message(message.author.name, content)
    bot_ctx.conversation_history.append_message(client.user.name, response)

    # either reply to a user or just send a message
    if message != None:
        await message.reply(response)
    else:
        await send_message(ctx, response)



# Actual function to generate AI sentences
async def generateSentence(ctx: Context, prompt="") -> str:
    """
    Fetch response from OpenAI
    
    Arguments
        ctx: the Discord Context
        prompt: prompt data
    """
    global conversation_history
    if len(prompt) == 0:
        logging.error("generateSentence: Zero length response")
        return

    async with ctx.typing():
        #print("Querying API...")
        try:
            response = await getAIResponse(prompt)
        except Exception as err:
            return err

        if response == "":
            return "Error generating sentence. Skill issue"
    
    # TODO: Handle these better so that the first response is extracted. 
    # TODO: Reset automatically if responses are too similar.
    # Bot has a tendency to try and speak for the user... not sure why
    # Handling that here by slicing off everything at "user_name:". It's wasteful, but cant seem to ween the AI off the habit
    speak_over_user_string = f"{ctx.author.name}:"
    if speak_over_user_string in response:
        logging.error(f"generateSentence: Detected AI taking on user role.")
        logging.error(f"generateSentence: The prompt for this was: {prompt}")
        logging.error(f"generateSentence: The response was: {response}")
        response = response[:response.find(speak_over_user_string)]
    
    third_person_string = f"{ctx.me.name}: "
    if third_person_string in response:
        logging.error(f"generateSentence: Detected AI talking in third person.")
        logging.error(f"generateSentence: The prompt for this was: {prompt}")
        logging.error(f"generateSentence: The response was: {response}")
        response = response[response.find(third_person_string) + len(third_person_string): ]

    response_log_str = response.replace("/n","")
    logging.debug(f"generateSentence: response: {response_log_str}")

    return response.strip()


if __name__ == '__main__':
    # Run bot
    print("Logging in...")
    client.run(os.environ["DISCORD_TOKEN"])
