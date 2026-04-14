import requests
import configparser
import logging

class ChatGPT:
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)

        api_key = config['CHATGPT']['API_KEY']
        base_url = config['CHATGPT']['BASE_URL']
        model = config['CHATGPT']['MODEL']
        api_ver = config['CHATGPT']['API_VER']

        self.url = f'{base_url}/deployments/{model}/chat/completions?api-version={api_ver}'

        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "api-key": api_key,
        }

        # System prompt (ALL ENGLISH)
        self.system_message = (
            "You are a helpful university assistant for students. "
            "Your answers are clear, simple, friendly, and easy to understand. "
            "Keep responses concise and natural."
        )

    def submit_with_context(self, messages):
        payload = {
            "messages": messages,
            "temperature": 1,
            "max_tokens": 150,
            "top_p": 1,
            "stream": False
        }

        try:
            response = requests.post(self.url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()

        except requests.exceptions.Timeout:
            self.logger.error("ChatGPT API request timeout")
            return "Error: Request timed out. Please try again."
        except requests.exceptions.ConnectionError:
            self.logger.error("ChatGPT API connection error")
            return "Error: Connection failed. Check your network."
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"ChatGPT API HTTP error: {e}, response: {response.text}")
            return f"Error: API call failed ({response.status_code}). Please try later."
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return "Error: An unknown error occurred."

        try:
            return response.json()['choices'][0]['message']['content']
        except KeyError as e:
            self.logger.error(f"ChatGPT API response parse error: {e}")
            return "Error: Invalid response from AI service."
        except Exception as e:
            self.logger.error(f"Response parse error: {str(e)}")
            return "Error: Failed to parse AI response."

    def submit(self, user_message: str):
        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": user_message},
        ]
        return self.submit_with_context(messages)

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    chatGPT = ChatGPT(config)

    while True:
        try:
            print('Input your query: ', end='')
            user_input = input()
            if user_input.lower() in ['exit', 'quit']:
                break
            response = chatGPT.submit(user_input)
            print(response)
        except KeyboardInterrupt:
            print("\nExit program")
            break
        except Exception as e:
            print(f"Error: {str(e)}")