import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add implementation folder to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'implementation')))

import telegram_agent

# Mock send_message to print instead of network call
def mock_send_message(chat_id, text, parse_mode=None):
    print(f"\n--- BOT RESPONSE ({chat_id}) ---\n{text}\n-----------------------------")

telegram_agent.send_message = mock_send_message

# Mock methods that might hit APIs expensive or side-effect
# We want to test logic flow, not external APIs fully, but 'digest' hits Gmail. 
# Let's let it hit Gmail read-only if credentials exist, otherwise mock.
# Assuming credentials handling is done inside the agent.

def verify_commands():
    print("Verifying Followup logic...")
    # Test Followup Add
    telegram_agent.handle_command("track this: Verify Antigravity Code", "12345")
    
    # Test Followup List
    telegram_agent.handle_command("show followups", "12345")
    
    print("\nVerifying Digest/Urgent (Mocking Gmail/LLM)...")
    
    # Mock Gmail service for digest
    mock_service = MagicMock()
    mock_messages = {
        'messages': [
            {'id': '1', 'from': 'boss@example.com', 'subject': 'Urgent Task', 'snippet': 'Do this now'},
            {'id': '2', 'from': 'newsletter@example.com', 'subject': 'Weekly News', 'snippet': 'Here is the news'}
        ]
    }
    
    with patch('implementation.google_mail.get_service', return_value=mock_service):
        with patch('implementation.google_mail.list_emails', return_value={'status': 'success', 'messages': mock_messages['messages']}):
             with patch('implementation.chat_agent.chat_openai', return_value={'choices': [{'message': {'content': 'Summary: Boss wants task done. Newsletter arrived.'}}]}):
                 
                 print("Testing /digest...")
                 telegram_agent.handle_command("digest", "12345")
                 
                 print("Testing /urgent...")
                 telegram_agent.handle_command("urgent emails", "12345")

    print("\nVerifying Drafts (Mocking Gmail)...")
    with patch('implementation.google_mail.get_service', return_value=mock_service):
        with patch('implementation.google_mail.list_drafts', return_value={'status': 'success', 'drafts': [{'id': 'd1', 'to': 'me@test.com', 'subject': 'test draft'}]}):
            telegram_agent.handle_command("list drafts", "12345")

if __name__ == "__main__":
    verify_commands()
