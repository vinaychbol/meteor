import os
import json
import boto3
import typer
from typing_extensions import Annotated
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
from lji_meteor.api_gateway import api_key, stages
from lji_meteor.rds import rds
from lji_meteor.autodeployment import deploy_lambda

from urllib.parse import urlparse
import psycopg2

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
    

app = typer.Typer(callback=main(), pretty_exceptions_show_locals=False)

try:
    aws_directory = str(sys.argv[1]) + str("/")
except:
    aws_directory = str("")

console = Console()

@app.callback(invoke_without_command=True)
def default(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        # Ask user to select a default command if none is provided
        commands_list = [
            "webapp",
            "db",
            "datalake",
            "api_gateway",
            "ec2",
            "deploy",
            "upgrade"
        ]
        choice = commands_list[survey.routines.select('Select a command to execute : ', options = tuple(commands_list))]
        print(f"\n[bold yellow]Selected Command :[/bold yellow] {choice}\n")
        if choice in commands_list:
            app([choice])
        else:
            print("Please use --help to see the available commands.")
    

def get_rsa_pair():
    id_rsa_pub_path = os.path.expanduser("~/.ssh/id_rsa.pub")
    
    if os.path.isfile(id_rsa_pub_path):
        with open(id_rsa_pub_path, 'r') as file:
            id_rsa_pub = file.read()
            return id_rsa_pub
        
id_rsa_public = get_rsa_pair()

@app.command()
@env_and_creds_layer
def webapp(
    env: Annotated[str, typer.Option(help="Environment Name")] = None,
    profile: Annotated[str, typer.Option(help="AWS Profile Name")] = None,
    tenant_creation: Annotated[bool, typer.Option(help="Flag to initiate tenant creation")] = False,
    data: Annotated[str, typer.Option(help="Configuration Data in JSON format")] = None):
    """
    Connect to Webapp using the CLI or Use --options flag to see more options
    """
    
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
def db(
    env: Annotated[str, typer.Option(help="Environment Name")] = None,
    profile: Annotated[str, typer.Option(help="AWS Profile Name")] = None,
    data: Annotated[str, typer.Option(help="Configuration Data in JSON format")] = None,
    get_credentials: Annotated[bool, typer.Option(help="Flag to get database credentials")] = None,
    superuser: Annotated[str, typer.Option(help="Email of the superuser to be updated")] = None,
    tenant_schema: Annotated[str, typer.Option(help="Tenant schema name")] = None,
    email: Annotated[str, typer.Option(help="Email address for authentication")] = None):
    """
    Connect to RDS using the CLI or Use --options flag to see more options
    """
    data = json.loads(data)
    session = boto3.Session(profile_name=profile)
    db = rds.DB(session, data, profile, id_rsa_public, env)
    db_con_url = ""
    if get_credentials or superuser:
        db_con_url = db.get_db_url()   
        
    if superuser:
        result = urlparse(db_con_url)
        username = result.username
        password = result.password
        database = result.path[1:]  # Removing the leading slash from the path
        hostname = "localhost"
        port = "2345"

        try:
            # Establish connection to the database
            connection = psycopg2.connect(
                database=database,
                user=username,
                password=password,
                host=hostname,
                port=port
            )
            
            with connection.cursor() as curs:
                if not tenant_schema:
                    tenant_schema = input("Enter the tenant schema: ")
                    
                update_query = f"""
                UPDATE {tenant_schema}.auth_user
                SET is_superuser = TRUE, is_staff = TRUE
                WHERE email = %s;
                """
                curs.execute(update_query, (superuser,))
                connection.commit()

                print(f"Updated user {superuser} in schema {tenant_schema}.")

        except Exception as e:
            print(f"Error connecting to the database: {e}")
        finally:
            # Make sure to close the connection
            if connection:
                connection.close()

        
        
    

@app.command()
@env_and_creds_layer
def datalake(
    env: Annotated[str, typer.Option(help="Environment Name")] = None,
    profile: Annotated[str, typer.Option(help="AWS Profile Name")] = None,
    data: Annotated[str, typer.Option(help="Configuration Data in JSON format")] = None,
    connect: Annotated[bool, typer.Option(help="Connect to Datalake Shell")] = False,
    get_credentials: Annotated[str, typer.Option(help="Get Credentials")] = None):
    """
    Connect to Datalake using the CLI
    """
    data = json.loads(data)
    session = boto3.Session(profile_name=profile)
    

        
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

    if connect is False:
        connect = survey.routines.inquire("Do you want to connect to Datalake Shell?", default=True)
        if connect:
            return_code = subprocess.call(['aws ssm start-session --target {0} --profile={1} --region={2}'.format(data['ec2']['datalake_instance_id'], profile, data['db']['region'])], shell=True)

            if return_code != 0:
                raise Exception("error")
        
    


@app.command()
@env_and_creds_layer
def api_gateway(
    env: Annotated[str, typer.Option(help="Environment Name")] = None,
    profile: Annotated[str, typer.Option(help="AWS Profile Name")] = None,
    data: Annotated[str, typer.Option(help="Configuration Data in JSON format")] = None,
    disable_logging: Annotated[bool, typer.Option(help="Disable API Gateway Logging")] = False,
    generate_api_key: Annotated[bool, typer.Option(help="Generate API Key")] = False,
    schema: Annotated[str, typer.Option(help="Schema Name for API Key Generation")] = None
):
    """
    LJI API Gateway CLI to automate common tasks on API Gateway Service 
    """
    data = json.loads(data)
    session = boto3.Session(profile_name=profile)
    
    if disable_logging:
        region = data['db']['region']
        stage = stages.Stage(profile, env, region)
        stage.turn_off_logging()
        return
    elif generate_api_key:
        apikey = api_key.ApiKey(session, profile, data, id_rsa_public, env)
        if not schema:
            schema = input("Enter the schema name for which you want to generate the API Key: ")
            
        apikey.add_x_api_key(schema)
        return
    
@app.command()
@env_and_creds_layer
def ec2(
    env: Annotated[str, typer.Option(help="Environment Name")] = None,
    profile: Annotated[str, typer.Option(help="AWS Profile Name")] = None,
    data: Annotated[str, typer.Option(help="Configuration Data in JSON format")] = None
):
    """
    Connect to EC2 instance using the CLI
    """
    data = json.loads(data)
    return_code = subprocess.call(['aws ssm start-session --target {0} --profile={1} --region={2}'.format(
                            data['ec2']['ecs_ec2_instance_id'], profile, data['db']['region'])], shell=True)
    if return_code != 0:
        raise Exception("Failed to connect to EC2 instance.")
    


@app.command()
def deploy(env: str = None, service: str = None, tag: str = None):
    """
    Trigger auto deployment lambda from CLI
    """
    if not env:
        env = input("Enter the environment: ")
    if not service:
        service = input("Enter the service name: ")
    if not tag:
        tag = input("Enter the tag: ")
    
    with console.status("Please wait - Triggering auto deployment lambda...", spinner="earth"):
        response = deploy_lambda.deploy(env, service, tag)
        
    if "error" in response:
        console.print("\n[bold red]Error Triggering Deployment[/bold red]")
        print(json.dumps(json.loads(response), indent=4))
    else:
        console.print("\n[bold blue]Deployment Triggered Successfully[/bold blue]")
        print(json.dumps(json.loads(response), indent=4))
        
@app.command()
def upgrade():
    """
    Upgrade the CLI to the latest version
    """
    print("Please wait - Upgrading the CLI...")
    subprocess.call(['pipx install https://github.com/vinaychbol/meteor/raw/refs/heads/main/dist/lji_meteor-latest.gz --force'], shell=True)
    print("\n[green]Successfully upgraded the CLI[/green]")
        
if __name__ == "__main__":
    app()