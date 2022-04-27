from cmath import e
import logging
import os
from click import FileError
import discord
from discord.ext.commands import Bot
from discord.ext.commands import Context
import openai
from prompt_handler import PromptHandler
from log import logging
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
task_running = False

# Use Bot instead of Discord Client for commands
# Give it ALL THE POWER
intents = discord.Intents.all()
client = Bot("!", intents=intents)

global_contexts = []
MAX_CONVERSATION_HISTORY = 3
nl = "\n"

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
    bot_name  = client.user.name
    user_name = message.author.name

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
    prompt_handler: PromptHandler
    if len(global_contexts) != 0:
        for context in global_contexts:
            if context.whisperword_user == user_name and context.whisperword_channel == ctx.channel.id:
                prompt_handler = context
                logging.info(f"on_message: using existing context for {user_name} in channel {ctx.channel.id}")             
        if prompt_handler == None:
            global_contexts.append(PromptHandler(user_name, bot_name, ctx.channel.id, MAX_CONVERSATION_HISTORY))
            prompt_handler = global_contexts[len(global_contexts)-1]
            logging.warning(f"on_message: created new context for {user_name} in channel {ctx.channel.id}")        
    else:
        global_contexts.append(PromptHandler(user_name, bot_name, ctx.channel.id, MAX_CONVERSATION_HISTORY))
        prompt_handler = global_contexts[len(global_contexts)-1]
        logging.warning(f"on_message: created new context for {user_name} in channel {ctx.channel.id}")

    # Handle .commands
    if content.startswith(".context"):
        await send_message(ctx, prompt_handler.context_command(content))
        return

    if content.startswith(".history"):
        await send_message(ctx, prompt_handler.conversation_history.history_command(content))
        return
        

    bot_mention = "@" + client.user.display_name
    logging.debug("on_message: mention " + bot_mention)
    if content.startswith(bot_mention):
        content = content[len(bot_mention):].strip()

    # Start the prompt with necessary context
    # whisperword represents keywords to change the nature of the prompt. We're gating this with a special keyword.
    if prompt_handler.whisperword == True and prompt_handler.whisperword_user == user_name and prompt_handler.whisperword_channel == ctx.channel.id:
        prompt_handler.proces_content_for_triggers(content)
        user_prompt = prompt_handler.get_prompt(content)
        logging.info(f"on_message: user_prompt:{nl}{user_prompt}")
    else:
        user_prompt = f"on_message: Your name is {bot_name}. You are talking to {user_name}. "

    response = await generateSentence(ctx, user_prompt)

    # Save history
    prompt_handler.conversation_history.append_message(bot_name, content)
    prompt_handler.conversation_history.append_message(user_name, response)

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

def split_multiple_dialogs(content, bot_name, user_name):
    """
    Find bot name
    """
    pass
    

if __name__ == '__main__':
    # Run bot
    print("Logging in...")
    client.run(os.environ["DISCORD_TOKEN"])
