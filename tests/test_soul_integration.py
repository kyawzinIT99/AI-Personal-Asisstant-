
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import json
import traceback
from datetime import datetime

# Add implementation folder to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'implementation')))

# Mock modules
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
sys.modules['scrape_apify'] = MagicMock()
sys.modules['clickup_agent'] = MagicMock()

import telegram_agent

class TestSoulIntegration(unittest.TestCase):
    
    def setUp(self):
        telegram_agent.send_message = MagicMock()
        telegram_agent.chat_agent.get_openai_client.return_value = MagicMock()
        # Mock global memory usage to avoid file writes during tests if not careful, 
        # but handle_command mostly calls helpers.
        
    @patch('telegram_agent.parse_intent')
    def test_digest(self, mock_parse):
        mock_parse.return_value = {"intent": "digest", "params": {"limit": 10}}
        
        telegram_agent.google_calendar.list_events.return_value = {
            'status': 'success', 
            'events': [{'start': '2023-01-01T10:00:00', 'summary': 'Meeting'}]
        }
        telegram_agent.google_mail.list_emails.return_value = {
            'status': 'success', 
            'messages': [{'from': 'boss@work.com', 'subject': 'Work', 'id': '1'}]
        }
        telegram_agent.chat_agent.chat_openai.return_value = {
            'choices': [{'message': {'content': 'Summary of work emails'}}]
        }
        
        telegram_agent.handle_command("/digest", "123")
        
        # Verify message contains digest info
        args, _ = telegram_agent.send_message.call_args
        self.assertIn("Daily Digest", args[1])
        self.assertIn("Meeting", args[1])
        self.assertIn("Summary of work emails", args[1])


    @patch('telegram_agent.parse_intent')
    def test_urgent(self, mock_parse):
        mock_parse.return_value = {"intent": "urgent", "params": {"limit": 5}}
        
        telegram_agent.google_mail.list_emails.return_value = {
            'status': 'success', 
            'messages': [{'from': 'alert@bank.com', 'subject': 'URGENT', 'id': '2'}]
        }
        
        telegram_agent.handle_command("/urgent", "123")
        
        # Check query uses label:important or similar
        call_args = telegram_agent.google_mail.list_emails.call_args
        self.assertTrue("important" in call_args[1].get('query') or "urgent" in call_args[1].get('query'))
        
        args, _ = telegram_agent.send_message.call_args
        self.assertIn("Urgent Items", args[1])

    @patch('telegram_agent.parse_intent')
    def test_draft_enforcement_send(self, mock_parse):
        """Test that mail_send creates a draft instead of sending."""
        mock_parse.return_value = {"intent": "mail_send", "params": {"to": "bob@example.com", "subject": "Hi"}}
        
        telegram_agent.google_mail.create_draft.return_value = {'status': 'success', 'draft_id': 'D123'}
        
        telegram_agent.handle_command("Send email to bob@example.com", "123")
        
        # Should call create_draft, NOT send_email
        telegram_agent.google_mail.create_draft.assert_called()
        telegram_agent.google_mail.send_email.assert_not_called()
        
        args, _ = telegram_agent.send_message.call_args
        self.assertIn("Draft created", args[1])

    @patch('telegram_agent.parse_intent')
    def test_draft_enforcement_reply(self, mock_parse):
        """Test that mail_reply creates a draft."""
        mock_parse.return_value = {"intent": "mail_reply", "params": {"body": "Yes", "message_id": "M1"}}
        
        telegram_agent.google_mail.create_reply_draft.return_value = {'status': 'success', 'draft_id': 'D124'}
        
        telegram_agent.handle_command("Reply Yes", "123")
        
        telegram_agent.google_mail.reply_email.assert_not_called()
        telegram_agent.google_mail.create_reply_draft.assert_called()
        
        args, _ = telegram_agent.send_message.call_args
        self.assertIn("Reply Draft created", args[1])

    @patch('telegram_agent.parse_intent')
    def test_draft_approve(self, mock_parse):
        mock_parse.return_value = {"intent": "draft_approve", "params": {"draft_id": "D123"}}
        telegram_agent.google_mail.send_draft.return_value = {'status': 'success'}
        
        telegram_agent.handle_command("approve draft D123", "123")
        
        telegram_agent.google_mail.send_draft.assert_called_with(telegram_agent.google_mail.get_service(), "D123")
        
        args, _ = telegram_agent.send_message.call_args
        self.assertIn("sent successfully", args[1])

    @patch('telegram_agent.parse_intent')
    def test_daily_log(self, mock_parse):
        mock_parse.return_value = {"intent": "daily_log", "params": {}}
        
        # Mock memory directory and log file
        with patch('os.path.exists', return_value=True):
            # Special case: side_effect to return valid JSON for followups and log text for actions
            file_contents = {
                telegram_agent.FOLLOWUP_FILE: '[]',
                os.path.join(telegram_agent.MEM_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.md"): 'User: Hello\nBot: World'
            }
            
            def mocked_open(path, *args, **kwargs):
                content = file_contents.get(path, '')
                return unittest.mock.mock_open(read_data=content)(path, *args, **kwargs)

            with patch('builtins.open', side_effect=mocked_open):
                telegram_agent.chat_agent.chat_openai.return_value = {
                    'choices': [{'message': {'content': 'Summary of the day'}}]
                }
                
                telegram_agent.handle_command("What did I do today?", "123")
                
                args, _ = telegram_agent.send_message.call_args
                self.assertIn("Evening Summary", args[1])
                self.assertIn("Summary of the day", args[1])

if __name__ == '__main__':
    unittest.main()
