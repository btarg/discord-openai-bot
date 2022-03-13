import unittest 
import openai_discord

class TestCustomAIContext(unittest.TestCase):
    CustomAIContext = openai_discord.CustomAIContext
    tc = CustomAIContext("knight","shrubbery","nih")

    content = [
        "My name is jamin",
        "I am a tall man",
        "You are a short woman",
        "I put on a hat",
        "I put on a cape",
        "Put on a robe",
        "Put on a jacket",
    ]
    
    for case in content:
        tc.proces_triggers(case)

    def test_set_user_attribute(self):
        self.assertEqual(self.tc.user_attributes["name"][1], "jamin")
        self.assertEqual(self.tc.user_attributes["description"][1], "a tall man")
        self.assertEqual(self.tc.user_attributes["clothing"][1][0], "a hat")
        self.assertEqual(self.tc.user_attributes["clothing"][1][1], "a cape")

    def test_set_bot_attribute(self):
        self.assertEqual(self.tc.bot_attributes["name"][1], "shrubbery")
        self.assertEqual(self.tc.bot_attributes["description"][1], "a short woman")
        self.assertEqual(self.tc.bot_attributes["clothing"][1][0], "a robe")
        self.assertEqual(self.tc.bot_attributes["clothing"][1][1], "a jacket")
    
    def test_delete_attrbibutes(self):
        pass

    def test_toJSON(self):
        json_str = self.tc.toJSON()
        self.assertTrue("shrubbery" in json_str)


    def test_fromJSON(self):
        pass

if __name__ == '__main__':
    unittest.main()