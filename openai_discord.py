import os
import random
import discord
from discord.ext.commands import Bot
import openai

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

currentGame = "with AI"
generateGame = True


async def getAIResponse(prompt):
    api_json = openai.Completion.create(
        engine="text-davinci-001",
        prompt=prompt,
        temperature=0.8,  # big hot takes
        max_tokens=100,
        frequency_penalty=0.5,
    )
    print(api_json)

    response = api_json.choices[0].text.strip('"')
    return response


async def changeStatus():
    global currentGame
    currentGame = await getAIResponse("Q: name a videogame\nA:")
    currentGame = currentGame.strip('"').strip()
    await client.change_presence(activity=discord.Game(name=currentGame))


@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))
    if task_running == False and generateGame == True:
        # let's get sussy ඞ
        await generateTask()

# Asyncio used to create background task
async def generateTask():
    global task_running
    task_running = True
    while task_running:
        await changeStatus()
        await asyncio.sleep(random.randint(600, 14400))


@client.command(aliases=["ai", "generate"])
async def prompt(ctx, string: str):
    await generateSentence(ctx, prompt=string)


@client.event
async def on_message(message):
    global task_running
    await client.process_commands(message)

    content = message.clean_content

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

    bot_mention = "@" + client.user.display_name
    print("\n\n" + bot_mention + "\n\n")
    if content.startswith(bot_mention):
        content = content[len(bot_mention):]

    ctx = await client.get_context(message)

    # random chance to respond to a message, always respond if mentioned
    if random.randint(0, 100) < 25 or client.user.mentioned_in(message):

        # in order of chain: third latest reply - second latest reply - latest reply
        # this is fucking stupid
        messages = ["", "", ""]

        # who is involved in the chain
        all_mentions = message.mentions
        all_mentions.append(message.author)

        # remove our own mention from this as we don't need to duplicate information
        me = ctx.guild.get_member(client.user.id)
        if me in all_mentions:
            all_mentions.remove(me)

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
        user_prompt = f"Your name is {client.user.display_name}. You are talking to {message.author.name} and others in a Discord server called {ctx.guild.name}. "

        # tell the AI what its playing
        if len(currentGame) != 0:
            user_prompt += f"and playing {currentGame}\n"
        else:
            user_prompt += "\n"

        # Find out what other people involved in the conversation are playing

        # for every member in the chain
        for member in all_mentions:

            user_prompt += f"{member.name}'s status is {member.status}.\n"

            # try to understand these conditions I dare you
            for activity in member.activities:

                if activity is not None:
                    if activity.type != discord.ActivityType.custom:
                        msg = f"{member.name} is {activity.type.name} "
                    else:
                        msg = f"{member.name}'s status message says: "

                    if activity.type == discord.ActivityType.listening:
                        msg += f"to {activity.name} "
                    else:
                        msg += f"{activity.name} "

                    if activity.type != discord.ActivityType.custom:
                        # Add details and state for more info
                        try:
                            if activity.details is not None:
                                msg += activity.details
                        except AttributeError as e:
                            print(e)
                            pass

                        try:
                            if activity.state is not None:
                                msg += f", {activity.state}"
                        except AttributeError as e:
                            print(e)
                            pass

                    if msg.endswith(": "):
                        msg = msg[:-2]
                    print(msg)
                    user_prompt += msg + "\n"
                else:
                    print("No activity has been set.")

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
        print("Querying API...")

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
