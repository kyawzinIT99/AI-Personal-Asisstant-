import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import json

# Add implementation folder to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'implementation')))

# Mock the modules before importing telegram_agent
sys.modules['google_calendar'] = MagicMock()
sys.modules['google_mail'] = MagicMock()
sys.modules['google_contacts'] = MagicMock()
sys.modules['weather_agent'] = MagicMock()
sys.modules['web_agent'] = MagicMock()
sys.modules['image_agent'] = MagicMock()
sys.modules['chat_agent'] = MagicMock()
sys.modules['search_image_agent'] = MagicMock()
sys.modules['blog_agent'] = MagicMock()
sys.modules['faceless_video_agent'] = MagicMock()
sys.modules['stripe_utils'] = MagicMock()

import telegram_agent

class TestTelegramIntegration(unittest.TestCase):
    
    def setUp(self):
        # Reset mocks
        telegram_agent.send_message = MagicMock()
        telegram_agent.chat_agent.get_openai_client.return_value = MagicMock()

    @patch('telegram_agent.parse_intent')
    def test_routing_calendar(self, mock_parse):
        mock_parse.return_value = {"intent": "calendar_list", "params": {"date": "today"}}
        telegram_agent.google_calendar.list_events.return_value = {'status': 'success', 'events': []}
        
        telegram_agent.handle_command("Show my calendar", "123")
        
        telegram_agent.google_calendar.list_events.assert_called_once()
        telegram_agent.send_message.assert_called()

    @patch('telegram_agent.parse_intent')
    def test_routing_blog(self, mock_parse):
        mock_parse.return_value = {"intent": "blog_gen", "params": {"topic": "AI", "audience": "devs"}}
        telegram_agent.blog_agent.generate_blog_workflow.return_value = {'status': 'success'}
        
        telegram_agent.handle_command("Write a blog about AI", "123")
        
        telegram_agent.blog_agent.generate_blog_workflow.assert_called_with("AI", "devs", chat_id="123")
        telegram_agent.send_message.assert_called()

    @patch('telegram_agent.parse_intent')
    def test_routing_video(self, mock_parse):
        mock_parse.return_value = {"intent": "video_gen", "params": {"subject": "Cats"}}
        telegram_agent.faceless_video_agent.generate_video_workflow.return_value = {'status': 'success', 'project_id': 'PID123'}
        
        telegram_agent.handle_command("Make a video about Cats", "123")
        
        telegram_agent.faceless_video_agent.generate_video_workflow.assert_called_with(subject="Cats")
        telegram_agent.send_message.assert_called()

    @patch('telegram_agent.parse_intent')
    def test_routing_mail_send(self, mock_parse):
        mock_parse.return_value = {"intent": "mail_send", "params": {"to": "test@example.com", "subject": "Hi"}}
        telegram_agent.google_mail.send_email.return_value = {'status': 'success'}
        
        telegram_agent.handle_command("Email test@example.com", "123")
        
        telegram_agent.google_mail.send_email.assert_called_with(telegram_agent.google_mail.get_service(), to="test@example.com", subject="Hi", body="")
        telegram_agent.send_message.assert_called()

        telegram_agent.google_mail.send_email.assert_called_with(telegram_agent.google_mail.get_service(), to="test@example.com", subject="Hi", body="")
        telegram_agent.send_message.assert_called()

    @patch('telegram_agent.parse_intent')
    def test_routing_weather(self, mock_parse):
        mock_parse.return_value = {"intent": "weather", "params": {"city": "London"}}
        telegram_agent.weather_agent.get_weather.return_value = {'name': 'London', 'main': {'temp': 20}, 'weather': [{'description': 'sunny'}]}
        
        telegram_agent.handle_command("Weather in London", "123")
        
        telegram_agent.weather_agent.get_weather.assert_called_with("London")
        telegram_agent.send_message.assert_called()

    @patch('telegram_agent.parse_intent')
    def test_routing_web_search(self, mock_parse):
        mock_parse.return_value = {"intent": "web_search", "params": {"query": "News"}}
        telegram_agent.web_agent.search_web.return_value = {'ai_summary': 'Some news'}
        
        telegram_agent.handle_command("Search for News", "123")
        
        telegram_agent.web_agent.search_web.assert_called_with("News")
        telegram_agent.send_message.assert_called()

    @patch('telegram_agent.parse_intent')
    def test_routing_image_search(self, mock_parse):
        mock_parse.return_value = {"intent": "image_search", "params": {"query": "Sunset"}}
        telegram_agent.search_image_agent.search_image.return_value = {'status': 'success', 'result_status': 'found', 'image_link': 'http://link'}
        
        telegram_agent.handle_command("Find image of Sunset", "123")
        
        telegram_agent.search_image_agent.search_image.assert_called_with("Sunset", intent='search', chat_id=None)
        telegram_agent.send_message.assert_called()

    @patch('telegram_agent.parse_intent')
    def test_routing_subscription(self, mock_parse):
        mock_parse.return_value = {"intent": "subscription_status", "params": {"email": "test@test.com"}}
        telegram_agent.stripe_utils.check_subscription.return_value = True
        
        telegram_agent.handle_command("Check sub for test@test.com", "123")
        
        telegram_agent.stripe_utils.check_subscription.assert_called_with("test@test.com")
        telegram_agent.send_message.assert_called()

        telegram_agent.stripe_utils.check_subscription.assert_called_with("test@test.com")
        telegram_agent.send_message.assert_called()

    @patch('telegram_agent.parse_intent')
    def test_routing_contact_search(self, mock_parse):
        mock_parse.return_value = {"intent": "contact_search", "params": {"query": "John"}}
        telegram_agent.google_contacts.search_contacts.return_value = {'status': 'success', 'contacts': [{'name': 'John', 'email': 'j@d.com', 'phone': '123'}]}
        
        telegram_agent.handle_command("Find John", "123")
        
        telegram_agent.google_contacts.search_contacts.assert_called()
        telegram_agent.send_message.assert_called()

    @patch('telegram_agent.parse_intent')
    def test_routing_image_gen(self, mock_parse):
        mock_parse.return_value = {"intent": "image_gen", "params": {"prompt": "A cat", "title": "Cat"}}
        telegram_agent.image_agent.generate_image_workflow.return_value = {'status': 'success'}
        
        telegram_agent.handle_command("Generate image of a cat", "123")
        
        telegram_agent.image_agent.generate_image_workflow.assert_called_with("Cat", "A cat", "123") 
        # Note: logic in handle_command calls it with (title, prompt, chat_id). 
        # Title defaults to "Telegram Image" if not in params, but mocks return what we put in params. 
        # Wait, if params has title, it uses it. My mock params has "Cat".
        telegram_agent.send_message.assert_called()

    @patch('telegram_agent.parse_intent')
    def test_routing_chat_fallback(self, mock_parse):
        # Test that generic chat falls back to chat_agent with the system prompt
        mock_parse.return_value = {"intent": "chat", "params": {"query": "Hello"}}
        telegram_agent.chat_agent.chat_openai.return_value = {'choices': [{'message': {'content': 'Hello human'}}]}
        
        telegram_agent.handle_command("Hello", "123")
        
        # Verify chat_openai was called with a system prompt in the messages
        args, _ = telegram_agent.chat_agent.chat_openai.call_args
        messages = args[0]
        self.assertEqual(messages[0]['role'], 'system')
        self.assertIn("Communication", messages[0]['content'])
        self.assertEqual(messages[1]['role'], 'user')
        telegram_agent.send_message.assert_called_with("123", "Hello human")

if __name__ == '__main__':
    unittest.main()
