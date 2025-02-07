import boto3
import subprocess
from rich.console import Console
from rich.prompt import Prompt

def list_sso_profiles():
    console = Console()
    session = boto3.Session()
    sso_client = session.client('sso-admin')
    
    response = sso_client.list_accounts()
    accounts = response['accountList']
    
    console.print("Available SSO Profiles:", style="bold green")
    for idx, account in enumerate(accounts):
        console.print(f"[{idx}] {account['accountName']} ({account['accountId']})")
    
    return accounts

def set_aws_profile(account_id):
    console = Console()
    profile_name = f"sso-{account_id}"
    
    # Assuming AWS CLI is configured with SSO
    subprocess.run(["aws", "configure", "sso", "--profile", profile_name])
    
    console.print(f"Profile {profile_name} is now set for your AWS account keys.", style="bold blue")

def main():
    accounts = list_sso_profiles()
    selected_index = Prompt.ask("Select a profile by index", choices=[str(i) for i in range(len(accounts))], default="0")
    selected_account = accounts[int(selected_index)]
    
    set_aws_profile(selected_account['accountId'])

if __name__ == "__main__":
    main()