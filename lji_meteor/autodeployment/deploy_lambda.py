import requests
import json

def deploy(env, service, tag):
    url = "https://autodeploy.basea.gravty.info/v1/deploy"

    payload = {
        "env":env,
        service: tag
    }

    headers = {}

    response = requests.request("POST", url, headers=headers, json=payload)
    return response.text