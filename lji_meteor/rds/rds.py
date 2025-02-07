from rich.console import Console
from rich.progress import Progress
from rich.prompt import Prompt
from rich.spinner import Spinner
from rich import print
import subprocess



console = Console()

class DB:
    
    def __init__(self, session, data, profile, id_rsa_public, env):
        self.session = session
        self.data = data
        self.profile = profile
        self.id_rsa_public = id_rsa_public
        self.conn = None
        self.cursor = None
        self.region = data['db']['region']
        self.env = env
        self.connect()
    
    def get_db_url(self):
        with console.status("Please wait - Featching RDS Credentials...", spinner="earth"):
                client = self.session.client('ssm', region_name=self.region)
                paramenter_name = f"/db/{self.env}/rds/db-con-url"
                print(f"\n[yellow]Fetching RDS Connection URL...{paramenter_name}[/yellow]")
                response = client.get_parameter(Name=paramenter_name,WithDecryption=True)
                db_con_url = response['Parameter']['Value']
                print("\n[yellow]RDS Connection URL:[/yellow] " + db_con_url)
                return db_con_url
    
    def connect(self):
        with console.status("Please wait - Clearing ports...", spinner="bouncingBar"):
            out = subprocess.call(['kill $(lsof -t -i :2345) >/dev/null 2>&1'], shell=True)
            out = subprocess.call(['kill $(lsof -t -i :9736) >/dev/null 2>&1'], shell=True)
            out = subprocess.call(['kill $(lsof -t -i :8843) >/dev/null 2>&1'], shell=True)
            print("\n[yellow]Cleared the ports successfully[/yellow]")
                            
        with console.status("Please wait - Connecting to RDS...", spinner="earth"):
            response = self.session.client('ec2-instance-connect', region_name=self.region).send_ssh_public_key(
                    InstanceId=self.data['db']['bastion_instance_id'],
                    InstanceOSUser='ec2-user',
                    SSHPublicKey=self.id_rsa_public,
                    AvailabilityZone=self.data['db']['az']
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
            ec2-user@{5}'.format(self.data['db']['rds'], self.data['db']['redshift'], self.data['db']['redis'],
                                self.region, self.profile.strip(), self.data['db']['bastion_instance_id'],
                                self.data['db']['engine_url'])],
                        shell=True)
        
        print("[green]Succesfully connected to DB[/green]")