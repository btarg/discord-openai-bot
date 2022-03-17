import unittest 
from openai_discord import PromptHandler
import json

nl = "\n"

def build_tc_mock():
    tc = PromptHandler("knight","shrubbery","nih", 3)
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
        tc.proces_content_for_triggers(case)

    return tc
    
class TestCustomAIContext(unittest.TestCase):
    def setUp(self) -> None:
        self.tc = build_tc_mock()

    def test_set_user_attribute(self):
        self.assertEqual(self.tc.user_attributes["name"][1], "jamin")
        self.assertEqual(self.tc.user_attributes["description"][1][0], "jamin is a tall man")
        self.assertEqual(self.tc.user_attributes["clothing"][1][0], "a hat")
        self.assertEqual(self.tc.user_attributes["clothing"][1][1], "a cape")

    def test_set_bot_attribute(self):
        self.assertEqual(self.tc.bot_attributes["name"][1], "shrubbery")
        self.assertEqual(self.tc.bot_attributes["description"][1][0], "you are a short woman")
        self.assertEqual(self.tc.bot_attributes["clothing"][1][0], "a robe")
        self.assertEqual(self.tc.bot_attributes["clothing"][1][1], "a jacket")
    
    def test_delete_attrbibutes(self):
        pass

    def test_save_context(self):
        json_string = self.tc.save_context("test_context")
        obj = json.loads(json_string)
        
        self.assertEqual(obj["user_attributes"]["name"][1], "jamin")
        self.assertEqual(obj["user_attributes"]["description"][1][0], "jamin is a tall man")
        self.assertEqual(obj["user_attributes"]["clothing"][1][0], "a hat")
        self.assertEqual(obj["user_attributes"]["clothing"][1][1], "a cape")


    def test_load_context(self):
        fresh_tc = PromptHandler("knight","spam","eggs and spam", 3)
        self.tc.save_context("test_context")
        fresh_tc.load_context("test_context")
        
        self.assertEqual(fresh_tc.user_attributes["name"][1], "jamin")
        self.assertEqual(fresh_tc.user_attributes["description"][1][0], "jamin is a tall man")
        self.assertEqual(fresh_tc.user_attributes["clothing"][1][0], "a hat")
        self.assertEqual(fresh_tc.user_attributes["clothing"][1][1], "a cape")
        
    def test_list_context(self):
        self.assertTrue("test_context" in self.tc.list_context())

    def test_remove_entry_from_attribute_list(self):
        self.tc.proces_content_for_triggers("I put on a tshirt")
        self.tc.proces_content_for_triggers("Put on a bracelet")

        self.assertTrue(len([item for item in self.tc.user_attributes["clothing"][1] if "tshirt" in item]) != 0)
        self.assertTrue(len([item for item in self.tc.bot_attributes["clothing"][1] if "bracelet" in item]) != 0)

        self.tc.proces_content_for_triggers("I take off my tshirt")
        self.tc.proces_content_for_triggers("Take off your bracelet")

        self.assertEqual([item for item in self.tc.user_attributes["clothing"][1] if "tshirt" in item], [])
        self.assertEqual([item for item in self.tc.bot_attributes["clothing"][1] if "bracelet" in item], [])
        

if __name__ == '__main__':
    unittest.main()