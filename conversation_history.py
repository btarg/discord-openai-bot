nl = "\n"
class ConversationHistory:
    """
    Stores history format str: f"{actor}: message "
    """
    messages = []
    max_messages = 5

    def append_message(self, actor: str, message: str) -> None:
        """
        Add a message to conversation history. Abide max_messages by dropping oldest

        Arguments:
            message: the message
            actor: who wrote the message
        """
        self.messages.append(f"{actor}: {message} {nl}")

        # Remove the last two from conversation history when it gets too long.
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def history_to_str(self) -> str:
        """
        Returns a string of each actor's
        Returns "" if no history
        """
        history_str = ""
        if len(self.messages) == 0:
            return ""
        
        for message in self.messages:
            history_str += message
        return history_str

    def reset_history(self):
        """
        Sets history to empty array
        """
        self.messages = []

    def set_max_messages(self, number: int):
        """
        Set total messages in history. If there's less space, drop the oldest.
        """
        self.max_messages = number

        # max_messages changed from 10 to 5. Had 10 already, added one above to make 11 total. 
        # Pop 0-5, leaving 6-10, which are now at index 0-5. range(11 - 5) = 0,1,2,3,4,
        if len(self.messages) - self.max_messages > 0:
            for x in range(len(self.messages) - self.max_messages):
                self.messages.pop(x)
    
    def history_command(self, content) -> str:
        helpstring = "Available commands:\n.history.reset"
        if ".history.reset" == content:
            self.reset_history()
            return "History was reset"
        else: 
            return f"Command wasnt recognized.\n{helpstring}"

    def __init__(self, max_messages) -> None:
        """
        Create conversation history object with max_messages
        """
        self.max_messages = max_messages