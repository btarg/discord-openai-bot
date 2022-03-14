import unittest 
import openai_discord
import json

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

    def test_save_context(self):
        json_string = self.tc.save_context("test_context")
        obj = json.loads(json_string)
        
        self.assertEqual(obj["user_attributes"]["name"][1], "jamin")
        self.assertEqual(obj["user_attributes"]["description"][1], "a tall man")
        self.assertEqual(obj["user_attributes"]["clothing"][1][0], "a hat")
        self.assertEqual(obj["user_attributes"]["clothing"][1][1], "a cape")


    def test_load_context(self):
        fresh_tc = openai_discord.CustomAIContext("knight","spam","eggs and spam")
        self.tc.save_context("test_context")
        fresh_tc.load_context("test_context")
        
        self.assertEqual(fresh_tc.user_attributes["name"][1], "jamin")
        self.assertEqual(fresh_tc.user_attributes["description"][1], "a tall man")
        self.assertEqual(fresh_tc.user_attributes["clothing"][1][0], "a hat")
        self.assertEqual(fresh_tc.user_attributes["clothing"][1][1], "a cape")
        
    def test_list_context(self):
        self.assertTrue("test_context" in self.tc.list_context())


if __name__ == '__main__':
    unittest.main()