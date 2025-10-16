import os
import json
import shutil
import boto3
from botocore.exceptions import ClientError
import typer
from typing_extensions import Annotated
import survey
import sys
import pyperclip 
import subprocess
from rich import print
from rich.console import Console
from rich.progress import Progress
from rich.spinner import Spinner
from rich.text import Text
from rich.live import Live
from rich.table import Table
import time

# Custom spinner frames for different operations
SPINNERS = {
    'connecting': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
    'loading': ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'],
    'dots': ['⠋', '⠙', '⠚', '⠞', '⠖', '⠦', '⠴', '⠲', '⠳', '⠓'],
    'pulse': ['█⠀', '██', '███', '████', '█████', '██████', '█████', '████', '███', '██', '█⠀'],
}
from utils.decorators import env_and_creds_layer
from typing import Any

from tenant.tenant import Tenant
from api_gateway import api_key, stages
from rds import rds
from autodeployment import deploy_lambda

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
        console.print("\n[bold cyan]🎯 Available Commands:[/bold cyan]")
        commands_list = [
            "webapp     📱",
            "db        💾",
            "datalake  📊",
            "api_gateway 🔌",
            "ec2       🖥️ ",
            "deploy    🚀",
            "fittribe  💪",
            "upgrade   ⬆️ "
        ]
        
        choice = commands_list[survey.routines.select('Select a command to execute:', options=tuple(commands_list))]
        choice = choice.split()[0]  # Extract command name without emoji
        
        console.print(f"\n[bold green]🎉 Selected Command:[/bold green] [bold cyan]{choice}[/bold cyan]\n")
        
        if choice in [cmd.split()[0] for cmd in commands_list]:
            app([choice])
        else:
            console.print("[bold yellow]ℹ️  Please use --help to see the available commands.[/bold yellow]")
    

def get_rsa_pair():
    id_rsa_pub_path = os.path.expanduser("~/.ssh/id_rsa.pub")
    
    if os.path.isfile(id_rsa_pub_path):
        with open(id_rsa_pub_path, 'r') as file:
            id_rsa_pub = file.read()
            return id_rsa_pub
        
id_rsa_public = get_rsa_pair()

@app.command()
def doctor():
    """Checks for requirements for command-line tools."""
    # The AWS CLI (aws) and Session Manager Plugin are required.
    required_tools = {
        "aws": "https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html",
        "session-manager-plugin": "https://docs.aws.amazon.com/systems-manager/latest/userguide/install-ssm-plugin.html"
    }
    
    with console.status("[bold blue]🔍 Checking dependencies...[/bold blue]", spinner="dots"):
        missing_tools = [tool for tool in required_tools if not shutil.which(tool)]

    if missing_tools:
        console.print("\n[bold red]❌ Error: Missing Required Dependencies![/bold red]")
        for tool in missing_tools:
            console.print(f"  [bold red]•[/bold red] [bold]{tool}[/bold] was not found")
            console.print(f"    📥 Install from: [blue underline]{required_tools[tool]}[/blue underline]")
        sys.exit(1)
    else:
        console.print("\n[bold green]✅ All required dependencies are installed![/bold green]")

@app.command()
@env_and_creds_layer
def redshift(
    env: Annotated[str, typer.Option(help="Environment Name")] = None,
    profile: Annotated[str, typer.Option(help="AWS Profile Name")] = None,
    data: Annotated[str, typer.Option(help="Configuration Data in JSON format")] = None):
    """
    Connect to Redshift using the CLI or Use --options flag to see more options
    """
    data = json.loads(data)
    session = boto3.Session(profile_name=profile)
    
    try:
        if len(data['db']['redshift']) == 0:
            raise Exception()
        try:
            out = subprocess.call(['kill $(lsof -t -i :5439) >/dev/null 2>&1'], shell=True)
            print("\n[yellow]Cleared the ports successfully[/yellow]")
            with console.status("Please wait - Connecting to Redshift...", spinner="earth"):
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
                        -L 5439:{0} \
                        -o "UserKnownHostsFile=/dev/null" \
                        -o "StrictHostKeyChecking=no" \
                        -o ProxyCommand="aws ssm start-session --target %h --document AWS-StartSSHSession --parameters portNumber=%p --region={1} --reason="REDSHIFT" --profile={2}" \
                        ec2-user@{3}'.format(data['db']['redshift'], data['db']['region'],
                                            profile, data['db']['bastion_instance_id'])],
                                            shell=True)

            if return_code != 0:
                raise Exception("error")

        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
            return

    except Exception as e:
        console.print(f"\n[bold yellow]Warning:[/bold yellow] Redshift is still not configured for [bold cyan]{env.strip().upper()}[/bold cyan].")
        return

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
        with console.status("[bold blue]🔍 Looking for running webapp tasks...[/bold blue]", spinner="dots"):
            response = ecs.list_tasks(
                cluster=cluster_id,
                serviceName=f'webapp-mainV2-{env.strip().lower()}',
                desiredStatus='RUNNING',
            )
            
            if not response.get('taskArns'):
                raise Exception("No running webapp tasks found")
                
            task_id = response['taskArns'][0].split('/')[-1]
            response = ecs.describe_tasks(cluster=cluster_id, tasks=[response['taskArns'][0]])
            
            task_def_response = ecs.describe_task_definition(
                taskDefinition=response['tasks'][0]['taskDefinitionArn']
            )
            
            container_found = False
            for container in task_def_response['taskDefinition']['containerDefinitions']:
                if container['name'] == 'webapp-main':
                    version = container['image'].split(':')[1]
                    container_found = True
                    break
            
            if not container_found:
                raise Exception("Webapp container not found in task definition")
        
        console.print(f"\n[bold blue]📦 Webapp Container Information[/bold blue]")
        console.print(f"[cyan]Version:[/cyan] [green]{version}[/green]")
        console.print(f"[cyan]Environment:[/cyan] [green]{env.strip().upper()}[/green]")
        console.print(f"[cyan]Profile:[/cyan] [green]{profile}[/green]\n")
        
        command = "/bin/bash"
        if tenant_creation:
            with console.status("[bold blue]🔧 Creating tenant...[/bold blue]", spinner="dots"):
                tenant.create(ecs_region, cluster_id, task_id, profile, command, env)
        
        console.print("[bold blue]🔌 Connecting to webapp container...[/bold blue]")
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
            raise Exception("Failed to execute ECS command - please check your permissions and try again")

    except Exception as e:
        error_msg = str(e)
        console.print("\n[bold red]❌ Connection Error[/bold red]")
        console.print(f"[red]└── {error_msg}[/red]")
        
        # Provide helpful troubleshooting tips based on the error
        if "No running webapp tasks found" in error_msg:
            console.print("\n[bold yellow]💡 Troubleshooting Tips:[/bold yellow]")
            console.print("1. Check if the webapp service is deployed")
            console.print("2. Verify the service name is correct")
            console.print("3. Check if the tasks are healthy")
        elif "permissions" in error_msg.lower():
            console.print("\n[bold yellow]💡 Troubleshooting Tips:[/bold yellow]")
            console.print("1. Verify your AWS credentials")
            console.print("2. Check your IAM permissions")
            console.print("3. Ensure your profile has ECS execute-command access")

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
    iswritepermission = survey.routines.inquire("Do you want write access to the database?", default=False)

    def create_progress_table() -> Table:
        table = Table(show_header=False, box=None)
        table.add_row("[bold blue]Database Connection Progress[/bold blue]")
        table.add_row("└── [yellow]Authenticating...[/yellow]")
        return table

    with Live(create_progress_table(), refresh_per_second=10) as live:
        user = str(env).strip().lower() + ('user' if iswritepermission else 'readonly')
        
        table = create_progress_table()
        table.add_row("    └── [cyan]Generating token...[/cyan]")
        live.update(table)
        
        result = subprocess.run(
            ['aws', 'rds', 'generate-db-auth-token',
             '--hostname', data['db']['rds'][:-5],
             '--port', data['db']['rds'][-4:],
             '--region', data['db']['az'][:-1],
             '--username', user,
             '--profile', profile],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True 
        )
        
        table = create_progress_table()
        if result.returncode == 0:
            db_password_token = result.stdout.strip()
            table.add_row("    └── [green]✅ Token generated successfully[/green]")
        else:
            table.add_row("    └── [red]❌ Failed to generate token[/red]")
            table.add_row(f"        └── [red]{result.stderr}[/red]")
        live.update(table)
    session = boto3.Session(profile_name=profile)
    db = rds.DB(session, data, profile, id_rsa_public, env)
    db_con_url = ""
    db_con_url = db.get_db_url()
    result = urlparse(db_con_url)
    username = result.username
    password = result.password
    database = result.path[1:]  # Removing the leading slash from the path
    hostname = "localhost"
    port = "2345"

    if superuser:
        try:
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

    # Print connection details for RDS
    console.print("\n[bold blue]------- RDS Connection Details -------[bold blue]")
    console.print(f"Username: [bold green]{username}[/bold green]")
    console.print(f"Database: [bold green]{database}[/bold green]")
    console.print(f"Host: [bold green]{hostname}[/bold green]")
    console.print(f"Port: [bold green]{port}[/bold green]")

    pyperclip.copy(db_password_token)
    print("\n[bold green]Database Password Token copied to clipboard![/bold green]")
    console.print("\n[green]Succesfully connected to RDS[/green]")

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
            cluster_id = data['ecs']['cluster_id']
            ecs = session.client('ecs', region_name=data['db']['region'])
            has_ec2 = True
            try:
                response = ecs.list_tasks(
                    cluster=cluster_id,
                    serviceName='datalake-' + str(env).strip().lower(),
                    desiredStatus='RUNNING',
                )
            except ClientError as e:
                if e.response['Error']['Code'] == 'ServiceNotFoundException':
                    console.print(f"\n[bold red]Error:[/bold red] Datalake ECS is still not configured for [bold cyan]{env.strip().upper()}[/bold cyan]. Falling back to EC2.")
                    has_ec2 = False
                else:
                    console.print(f"\n[bold red]An unexpected AWS error occurred:[/bold red] {e}")
                    return
            if has_ec2:
                taskId = response['taskArns'][0].split('/')[-1]
                response = ecs.describe_tasks(cluster=cluster_id, tasks=[response['taskArns'][0]])
                response1 = ecs.describe_task_definition(
                    taskDefinition=response['tasks'][0]['taskDefinitionArn']
                )
                container_Def = response1['taskDefinition']['containerDefinitions']
                for con_def in container_Def:
                    if con_def['name'] == 'airflow':
                        print('Connecting to airflow container running version ' +
                                con_def['image'].split(':')[1] + " ......")
                        break
                aws_command = ["aws",
                                "ecs",
                                "execute-command",
                                "--region",
                                data['db']['region'],
                                "--cluster",
                                cluster_id,
                                "--task",
                                taskId,
                                "--profile",
                                profile,
                                "--container",
                                "airflow",
                                "--command",
                                "gosu airflow /bin/bash",
                                "--interactive"
                                ]
                try:
                    subprocess.run(aws_command, check=True)
                except subprocess.CalledProcessError as e:
                    console.log("Failed to connect to ECS container. {e}")
            else:
                try:
                    return_code = subprocess.call(['aws ssm start-session --target {0} --profile={1} --region={2}'.format(data['ec2']['datalake_instance_id'], profile, data['db']['region'])], shell=True)
                except Exception as e:
                    console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        return
    try:
        subprocess.call(['open http://localhost:9154'], shell=True)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")


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
@env_and_creds_layer
def fittribe(
    env: Annotated[str, typer.Option(help="Environment Name")] = None,
    profile: Annotated[str, typer.Option(help="AWS Profile Name")] = None,
    data: Annotated[str, typer.Option(help="Configuration Data in JSON format")] = None):
    """
    Connect to Fittribe Flask using the CLI or Use --options flag to see more options
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
                serviceName=f'fittribe-flaskapp-{env.strip().lower()}',
                desiredStatus='RUNNING',
            )
        task_id = response['taskArns'][0].split('/')[-1]
        response = ecs.describe_tasks(cluster=cluster_id, tasks=[response['taskArns'][0]])
        response1 = ecs.describe_task_definition(
                        taskDefinition=response['tasks'][0]['taskDefinitionArn']
                )
        container_Def = response1['taskDefinition']['containerDefinitions']
        for con_def in container_Def:
            if con_def['name'] == 'fittribe-flaskapp':
                print('Connecting to Webapp container running version ' + con_def['image'].split(':')[1] + " ......")
                break
            
        console.print(f"[bold green]Successfully connected to {env.strip().upper()} using profile {profile}.[/bold green]")
        command = "/bin/bash"
            
        return_code = subprocess.call(
                [f'aws ecs execute-command  \
                --region {ecs_region} \
                --cluster {cluster_id} \
                --task {task_id} \
                --profile {profile.strip()} \
                --container fittribe-flaskapp \
                --command "{command}" \
                --interactive'],
                shell=True
        )
        
        if return_code != 0:
            raise Exception(f"[bold red]Error:[/bold red] Failed to execute ECS command.")

    except Exception as e:
        console.print(f"[bold red]Error while connecting to ECS:[/bold red] {str(e)}")
        
@app.command()
def upgrade():
    """
    Upgrade the CLI to the latest version
    """
    print("Please wait - Upgrading the CLI...")
    subprocess.call(['pipx install https://github.com/vinaychbol/meteor/raw/refs/heads/main/dist/lji_meteor-latest.gz --force'], shell=True)
    print("\n[green]Successfully upgraded the CLI[/green]")

@app.command()
def version():
    """
    Show the current version of the CLI
    """
    version_info = {
        'version': '1.0.0',
        'release_date': '2025-10-16'
    }
    
    console.print("\n[bold blue]📦 LJI Meteor CLI[/bold blue]")
    console.print("=" * 40)
    console.print(f"[bold cyan]Version:[/bold cyan]      [green]{version_info['version']}[/green]")
    console.print(f"[bold cyan]Released:[/bold cyan]     [green]{version_info['release_date']}[/green]")
    console.print("=" * 40)
        
if __name__ == "__main__":
    app()