import requests
import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_TOKEN")
SERVER_ID = os.getenv("SERVER_ID")


PLAYERS_JSON_PATH = "players.json"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}


def download_file_from_server():
    """Download players.json file from the server using Pterodactyl API"""
    try:
        endpoint = f"{API_URL}api/client/servers/{SERVER_ID}/files/contents"
        file_headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Accept": "text/plain"
        }
        params = {"file": PLAYERS_JSON_PATH}
        response = requests.get(endpoint, headers=file_headers, params=params)
        if response.status_code == 200:
            if not response.text or response.text.isspace():
                print("Warning: Downloaded file is empty")
                return None  
            fixed_filename = f"{OUTPUT_DIR}/latest_players.json"
            with open(fixed_filename, "w", encoding="utf-8") as f:
                f.write(response.text)
            return response.text
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return None
def parse_player_data(json_data):
    """Parse the player data from JSON"""
    try:
        data = json.loads(json_data)
        return data
    
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON data - {str(e)}")
        print(f"JSON data length: {len(json_data)} characters")
        if len(json_data) > 0:
            error_pos = e.pos if hasattr(e, 'pos') else 0
            start = max(0, error_pos - 20)
            end = min(len(json_data), error_pos + 20)
            print(f"JSON near error (position {error_pos}): ...{json_data[start:end]}...")
        return None
    except Exception as e:
        print(f"Error parsing data: {str(e)}")
        return None

def add_player_to_whitelist(player_name):
    """Send command to add player to whitelist via Pterodactyl API"""
    try:
        endpoint = f"{API_URL}api/client/servers/{SERVER_ID}/command"
        command_data = {
            "command": f";whitelist add {player_name}"
        }
        response = requests.post(endpoint, headers=headers, json=command_data)
        
        if response.status_code == 204:
            return True
        else:
            print(f"Failed to add player to whitelist. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error adding player to whitelist: {str(e)}")
        return False


def main():
    """Main function to run the script"""
    json_data = download_file_from_server()
    if json_data:
        player_data = parse_player_data(json_data)

if __name__ == "__main__":
    main()