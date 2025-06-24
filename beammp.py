import requests
def check_beammp_player(nickname):
    url = f"https://forum.beammp.com/u/{nickname}"
    response = requests.get(url)
    
    if response.status_code == 200:
        if "Oops! That page doesn’t exist or is private." in response.text:
            return False
        else:
            return True
    else:
        return False