import os
import subprocess
import string 
import random
import boto3 
import json

class Tenant():
    
    
    def create(self, ecs_region, cluster_id, task_id, profile, command, env):
        print("[bold green]Initiated Tenant Creation[/bold green]")
        session = boto3.Session(profile_name=profile)
        client = session.client('cloudfront', region_name=ecs_region)
        response = client.list_distributions()
        api_url = None
        for item in response['DistributionList']['Items']:
            if api_url:
                break
            for item in item['Origins']['Items']:
                if env in item['DomainName'] and 'api' in item['DomainName']:
                    print(item['DomainName'])
                    api_url = item['DomainName']
                    break
            
        print(f"[bold green]API Gateway URL:[/bold green] {api_url}")
        url_split = api_url.split('.')
        domain = f"{url_split[1]}.{url_split[2]}.{url_split[3]}"
        print(f"[bold green]Domain:[/bold green] {domain}")
        tenant_url = input("Enter Tenant URL |ex: abc.env.gravty.xyz|: ")
        tenant_name = tenant_url.split('.')[0]
        tenant_email = input("Enter Tenant Email: ")
        tenant_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        command = f"""
        export APIGatewayURL=https://{api_url}/ && export PRIVATE_PEM_FILE=s3://gravty-{env}/cert/keys/private.pem && python3 manage.py setup_tenant {tenant_url} {tenant_email} {tenant_password} --test_tenant=False
        """
        
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
        
        print("Assuming Tenat creation was successful")
        print("Clearing Cache for the tenant...")
        
        command = f"""
        python3 manage.py tenant_command shell -s {tenant_name} << EOF
        from offers.tasks import setup_offer_expiration_process
        setup_offer_expiration_process() 
        from core.listener import cache_loyalty_tenants
        cache_loyalty_tenants() 
        exit() 
        EOF
        """
        
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
        
        print("Tenant cache cleared successfully")
        print("Tenant Name: ", tenant_name)
        print("Tenant Email: ", tenant_email)
        print("Tenant Password: ", tenant_password)
        print("Tenat URL :", f"https://{tenant_name}.{env.strip().lower()}.gravtee.com")
        
        if return_code != 0:
                raise Exception(f"[bold red]Error:[/bold red] Failed to execute ECS command.")


# tenant = Tenant()
# tenant.create("us-west-2", "x", "x", "ie", "ls", "cstraining")