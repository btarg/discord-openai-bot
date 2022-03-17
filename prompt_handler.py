import os
from conversation_history import ConversationHistory
import json
from log import logging
import spacy
nlp = spacy.load("en_core_web_sm")


nl = "\n"

class PromptHandler:
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

    trigger_phrases_maps = {}

    whisperword = False
    whisperword_user = ""
    whisperword_channel = ""

    my_funcs = locals()

    CONTEXT_FOLDER =".\\contexts\\"

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
    Context Commands: read, write, update, delete(not yet implemented)
    '''

    def save_context(self, bot_context_save_name) -> str:
        with open(f"{self.CONTEXT_FOLDER}{self.whisperword_user}_{bot_context_save_name}.botctx", "w") as file:
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
            with open(f"{self.CONTEXT_FOLDER}{self.whisperword_user}_{bot_context_save_name}.botctx", "r") as file:
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
        file_list = os.listdir(f"{self.CONTEXT_FOLDER}")
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
        target_prompts = f"{user_name}: {content}{nl}{bot_name}: "

        # Bring everything together
        context_str = f"{bot_discussion_context_str}{user_discussion_context_str}{history_context_str}{target_prompts}"

        return context_str
    
    def update_trigger_phrase_maps(self):
        # attribute phrase appended with a * indicates the attribute phrase is persisted with the rest of the data. This generally requires
        # TODO: COMPLICATED: allow for multiple prepositional phrases.
        # TODO: Create environment attributes separate of user
        # TODO: Think about handling multi-value attributes that have a rolling nature like history for more ephemeral context
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


    def __init__(self, user_name, bot_name, channel_id, max_conversation_history: int):
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
        self.conversation_history = ConversationHistory(max_conversation_history)

