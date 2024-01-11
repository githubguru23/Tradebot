import os
import requests
import git
import logging
import time
from requests.exceptions import HTTPError, RequestException
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables for configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO_URL = os.environ.get("GITHUB_REPO_URL")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 150))

# Validate input prompt
def validate_prompt(prompt):
    if not prompt or len(prompt) > 1000:
        raise ValueError("Invalid prompt")

# Function to get code from ChatGPT
def get_code_from_chatgpt(prompt):
    validate_prompt(prompt)
    api_url = "https://api.openai.com/v1/engines/davinci-codex/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "prompt": prompt,
        "max_tokens": MAX_TOKENS
    }
    try:
        response = api_request_with_retry(api_url, headers, data)
        response.raise_for_status()
        return response.json()["choices"][0]["text"]
    except HTTPError as http_err:
        logging.error(f'HTTP error occurred: {http_err}')
    except RequestException as req_err:
        logging.error(f'Request error: {req_err}')
    except Exception as err:
        logging.error(f'An error occurred: {err}')

# Function to handle API requests with retries
def api_request_with_retry(url, headers, json, max_retries=3, delay=5):
    for i in range(max_retries):
        response = requests.post(url, headers=headers, json=json)
        if response.status_code == 200:
            return response
        else:
            logging.warning(f"API request failed, retrying in {delay} seconds...")
            time.sleep(delay)
    raise Exception("Maximum retries reached for API request")

# Function to commit code to GitHub
def commit_code_to_github(code, filename="output.py", message="Auto commit from ChatGPT"):
    repo_dir = 'C:\\GitHub_Project'
    if not os.path.exists(repo_dir):
        git.Repo.clone_from(GITHUB_REPO_URL, repo_dir, branch='main', env={'GIT_COMMITTER_TOKEN': GITHUB_TOKEN})
    repo = git.Repo(repo_dir)

    file_path = os.path.join(repo_dir, filename)
    with open(file_path, "w") as file:
        file.write(code)

    repo.git.add(file_path)
    repo.index.commit(message)
    repo.remote('origin').push('main')

# Main Execution
if __name__ == '__main__':
    try:
        prompt = input("Enter your prompt for ChatGPT: ")
        generated_code = get_code_from_chatgpt(prompt)
        if generated_code:
            commit_code_to_github(generated_code)
        else:
            logging.error("No code was generated.")
    except Exception as e:
        logging.error(f'Error: {e}')
