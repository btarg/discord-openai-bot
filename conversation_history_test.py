import unittest 
import conversation_history

nl = "\n"

def build_mock_conversation_history() -> conversation_history.ConversationHistory:
        ch = conversation_history.ConversationHistory(5)
        ch.append_message("HEAD KNIGHT", "Ni!")
        ch.append_message("KNIGHTS", "Ni! Ni! Ni!")
        ch.append_message("ARTHUR", "Who are you?")
        ch.append_message("HEAD KNIGHT", "We are the Knights Who Say... Ni!")
        ch.append_message("ARTHUR", "No! Not the Knights Who Say Ni!")
        return ch

class TestConversationHistory(unittest.TestCase):
    def test_append_message(self):
        ch = build_mock_conversation_history()
        ch.reset_history()
        ch.append_message("HEAD KNIGHT", "Ni!")
        ch.append_message("KNIGHTS", "Ni! Ni! Ni!")
        ch.append_message("ARTHUR", "Who are you?")
        ch.append_message("HEAD KNIGHT", "We are the Knights Who Say... Ni!")
        ch.append_message("ARTHUR", "No! Not the Knights Who Say Ni!")
        ch.append_message("HEAD KNIGHT", "The same!")
        ch.append_message("BEDEVERE", "Who are they?")

        self.assertEqual(ch.messages[0], "ARTHUR: Who are you? \n")

    def test_history_to_str(self):
        ch = build_mock_conversation_history()
        output = ch.history_to_str()
        match_str = "HEAD KNIGHT: Ni! \nKNIGHTS: Ni! Ni! Ni! \nARTHUR: Who are you? \nHEAD KNIGHT: We are the Knights Who Say... Ni! \nARTHUR: No! Not the Knights Who Say Ni! \n"
        self.assertEqual(output, match_str)
        

if __name__ == '__main__':
    unittest.main()