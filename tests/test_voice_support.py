import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import io

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

class TestVoiceSupport(unittest.TestCase):
    
    @patch('telegram_agent.requests.get')
    @patch('telegram_agent.download_telegram_file')
    @patch('telegram_agent.transcribe_voice')
    @patch('telegram_agent.handle_command')
    @patch('telegram_agent.send_message')
    @patch('telegram_agent.get_updates')
    def test_voice_message_flow(self, mock_get_updates, mock_send_message, mock_handle_command, mock_transcribe, mock_download, mock_req_get):
        # Patch telegram_agent.ALLOWED_CHAT_ID to None to bypass security check
        telegram_agent.ALLOWED_CHAT_ID = None
        
        # Setup mock update with voice message
        mock_get_updates.side_effect = [
            {
                "ok": True,
                "result": [{
                    "update_id": 123,
                    "message": {
                        "chat": {"id": 456},
                        "voice": {"file_id": "voice_123"}
                    }
                }]
            },
            None # Stop loop on second iteration
        ]
        
        mock_download.return_value = b"fake_voice_data"
        mock_transcribe.return_value = "Hello world"
        
        # We need to break the main loop or handle Exception to exit
        with patch('time.sleep', side_effect=KeyboardInterrupt):
            try:
                telegram_agent.main()
            except KeyboardInterrupt:
                pass
        
        # Verify flow
        mock_download.assert_called_with("voice_123")
        mock_transcribe.assert_called_with(b"fake_voice_data")
        mock_handle_command.assert_called_with("Hello world", "456")
        
        # Verify user notifications
        expected_calls = [
            unittest.mock.call("456", "🎙️ _Transcribing your voice message..._"),
            unittest.mock.call("456", '📝 _Transcribed_: "Hello world"')
        ]
        mock_send_message.assert_has_calls(expected_calls)

if __name__ == '__main__':
    unittest.main()
