import os
import json
import boto3
import typer
import survey
import sys
import subprocess
from rich import print
from rich.console import Console
from rich.progress import Progress
from rich.spinner import Spinner
from rich.text import Text
import time
from lji_meteor.utils.decorators import env_and_creds_layer
from typing import Any
from lji_meteor.tenant.tenant import Tenant
from lji_meteor.api_gateway import stages

tenant = Tenant()

def main():
    print(r"""
⠀⢀⠀⠀⠀⠀⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠈⠻⣶⣤⣤⣴⣿⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠈⠙⠻⠿⠿⠿⠿⠂⠀⠀⢦⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⢰⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣿⣿⣶⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⢸⣿⣦⡀⠀⠀⣸⣄⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣷⣦⣄⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠈⢿⣿⣿⣿⣿⣿⣿⣷⣤⣄⣠⣴⣿⣿⣿⣿⣿⣿⣿⣿⣷⣤⡀⠀⠀⠀⠀
⠀⠀⠀⠀⠙⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣋⠉⠉⠉⠉⠉⠛⠿⣷⣄⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠈⠙⢿⣿⣿⣿⣿⡿⠛⣿⣿⣿⣷⣦⡀⠀⡄⠀⠀⠈⢻⣆⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⣿⣿⡟⠀⠀⠈⠛⠛⠿⠿⢿⡀⢻⣦⣄⡀⢈⣿⡆⠀
⠀⠀⠀⠀⠀⢲⣄⡀⠀⠀⢸⣿⠁⠀⠐⢦⣄⡀⠀⢦⣤⣄⡀⠻⣿⣿⣿⣿⣷⠀
⠀⠀⠀⠀⠀⠀⠹⣿⣷⣶⣿⣿⠀⠀⠀⠀⢻⣿⣆⠀⠹⣿⣿⡄⠘⣿⣿⣿⡿⠀
⠀⠀⠀⠀⠀⠀⠀⠈⢿⣿⣿⣿⣇⠀⠀⠀⠙⠿⠟⠀⠀⢹⣿⡷⢀⣿⣿⣿⠃⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢿⣿⣿⣦⡀⠀⠀⣆⠀⠀⠀⣸⣿⣷⣿⣿⡿⠃⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⠿⣿⣶⣤⣘⣿⣶⣶⣿⣿⣿⠿⠋⠁⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠙⠛⠛⠛⠛⠛⠉⠀⠀⠀⠀⠀⠀⠀

  _        _ ___  [red] __  __      _                  [/red]
 | |      | |_ _| [red]|  \/  | ___| |_ ___  ___  _ __ [/red]
 | |   _  | || |  [red]| |\/| |/ _ | __/ _ \/ _ \| '__|[/red]
 | |__| |_| || |  [red]| |  | |  __| ||  __| (_) | |   [/red]
 |_____\___/|___| [red]|_|  |_|\___|\__\___|\___/|_|   [/red]
                                                  
            """)

app = typer.Typer(callback=main())

try:
    aws_directory = str(sys.argv[1]) + str("/")
except:
    aws_directory = str("")

console = Console()

def get_rsa_pair():
    id_rsa_pub_path = os.path.expanduser("~/.ssh/id_rsa.pub")
    
    if os.path.isfile(id_rsa_pub_path):
        with open(id_rsa_pub_path, 'r') as file:
            id_rsa_pub = file.read()
            return id_rsa_pub
        
id_rsa_public = get_rsa_pair()

@app.command()
@env_and_creds_layer
def webapp(env: str = None, profile: str = None,tenant_creation: bool = False, data: str = None):
    data = json.loads(data)
    session = boto3.Session(profile_name=profile)

    if 'ecs' not in data:
        console.print(f"[bold yellow]Warning:[/bold yellow] Webapp is still not configured for [bold cyan]{env.strip().upper()}[/bold cyan].")
        return

    cluster_id = data['ecs']['cluster_id']
    ecs_region = data['db']['region']
    console.print(f"[bold green]Found ECS Cluster:[/bold green] {cluster_id} in region {ecs_region}")
        
    ecs = session.client('ecs', region_name=ecs_region)
        
    try:
        response = ecs.list_tasks(
                cluster=cluster_id,
                serviceName=f'webapp-mainV2-{env.strip().lower()}',
                desiredStatus='RUNNING',
            )
        task_id = response['taskArns'][0].split('/')[-1]
        taskId = response['taskArns'][0].split('/')[-1]
        response = ecs.describe_tasks(cluster=cluster_id, tasks=[response['taskArns'][0]])
        response1 = ecs.describe_task_definition(
                        taskDefinition=response['tasks'][0]['taskDefinitionArn']
                )
        container_Def = response1['taskDefinition']['containerDefinitions']
        for con_def in container_Def:
            if con_def['name'] == 'webapp-main':
                print('Connecting to Webapp container running version ' + con_def['image'].split(':')[1] + " ......")
                break
            
        console.print(f"[bold green]Successfully connected to {env.strip().upper()} using profile {profile}.[/bold green]")
        command = "/bin/bash"
        if tenant_creation:
            tenant.create(ecs_region, cluster_id, task_id, profile, command, env)
            
        return_code = subprocess.call(
                [f'aws ecs execute-command  \
                --region {ecs_region} \
                --cluster {cluster_id} \
                --task {task_id} \
                --profile {profile.strip()} \
                --container webapp-main \
                --command "{command}" \
                --interactive'],
                shell=True
        )
        
        if return_code != 0:
            raise Exception(f"[bold red]Error:[/bold red] Failed to execute ECS command.")

    except Exception as e:
        console.print(f"[bold red]Error while connecting to ECS:[/bold red] {str(e)}")

@app.command()
@env_and_creds_layer
def db(env: str = None, profile: str = None, data: str = None, get_credentials: str = None):
    data = json.loads(data)
    session = boto3.Session(profile_name=profile)
        
    with console.status("Please wait - Clearing ports...", spinner="bouncingBar"):
                        out = subprocess.call(['kill $(lsof -t -i :2345) >/dev/null 2>&1'], shell=True)
                        out = subprocess.call(['kill $(lsof -t -i :9736) >/dev/null 2>&1'], shell=True)
                        out = subprocess.call(['kill $(lsof -t -i :8843) >/dev/null 2>&1'], shell=True)
                        print("\n[yellow]Cleared the ports successfully[/yellow]")
                        
    with console.status("Please wait - Connecting to RDS...", spinner="earth"):
                        response = session.client('ec2-instance-connect', region_name=data['db']['region']).send_ssh_public_key(
                                InstanceId=data['db']['bastion_instance_id'],
                                InstanceOSUser='ec2-user',
                                SSHPublicKey=id_rsa_public,
                                AvailabilityZone=data['db']['az']
                            )
                        
                        if not response['Success']:
                            raise Exception("Something went wrong with SSH")
                            
    return_code = subprocess.call(['ssh -i ~/.ssh/id_rsa \
        -Nf -M \
        -L 2345:{0} \
        -L 9736:{2} \
        -L 8843:{6} \
        -L 5439:{0} \
        -o "UserKnownHostsFile=/dev/null" \
        -o "StrictHostKeyChecking=no" \
        -o ProxyCommand="aws ssm start-session --target %h --document AWS-StartSSHSession --parameters portNumber=%p --region={3} --profile={4}" \
        ec2-user@{5}'.format(data['db']['rds'], data['db']['redshift'], data['db']['redis'],
                            data['db']['region'], profile.strip(), data['db']['bastion_instance_id'],
                            data['db']['engine_url'])],
                    shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print("\n[green]Succesfully connected to DB[/green]")
    if get_credentials:
        with console.status("Please wait - Featching RDS Credentials...", spinner="earth"):
            pass

@app.command()
@env_and_creds_layer
def datalake(env: str = None, profile: str = None, data: str = None, get_credentials: str = None):
    data = json.loads(data)
    session = boto3.Session(profile_name=profile)
    
    # Start the loading spinner
    with console.status("Please wait - Loading Congurations...", spinner="pong"):
        try:
            credentials = profile.strip()
            session = boto3.Session(profile_name=credentials)
            client = session.client('s3', region_name='us-west-2')
            response = client.get_object(Bucket='gravty-comet', Key='comet-details.json')
            data = json.loads(response['Body'].read())
            data = data[env.strip().lower()]
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
            return
        
    with console.status("Please wait - Clearing ports...", spinner="monkey"):
                        out = subprocess.call(['kill $(lsof -t -i :9154) >/dev/null 2>&1'], shell=True)
                        print("\n[yellow]Cleared the ports successfully[/yellow]")
                        
    with console.status("Please wait - Connecting to Datalake...", spinner="earth"):
                        response = session.client('ec2-instance-connect', region_name=data['db']['region']).send_ssh_public_key(
                                InstanceId=data['db']['bastion_instance_id'],
                                InstanceOSUser='ec2-user',
                                SSHPublicKey=id_rsa_public,
                                AvailabilityZone=data['db']['az']
                            )
                        
                        if not response['Success']:
                            raise Exception("Something went wrong with SSH")
                            
    return_code = subprocess.call(['ssh -i ~/.ssh/id_rsa \
                -Nf -M \
                -L 9154:{0} \
                -o "UserKnownHostsFile=/dev/null" \
                -o "StrictHostKeyChecking=no" \
                -o ProxyCommand="aws ssm start-session --target %h --document AWS-StartSSHSession --parameters portNumber=%p --region={1} --profile={2}" \
                ec2-user@{3}'.format(data['ec2']['airflow_dns'], data['db']['region'],
                                    profile, data['db']['bastion_instance_id'])],shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("\n[green]Succesfully connected to Datalake[/green]")


@app.command()
@env_and_creds_layer
def api_gateway(env: str = None, profile: str = None,data: str = None, disable_logging: bool = False):
    data = json.loads(data)
    
    if disable_logging:
        region = data['db']['region']
        stage = stages.Stage(profile, env, region)
        stage.turn_off_logging()
    


if __name__ == "__main__":
    app()