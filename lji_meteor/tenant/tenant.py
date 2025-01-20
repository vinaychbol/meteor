import os
import subprocess
import string 
import random

class Tenant():
    
    
    def create(self, ecs_region, cluster_id, task_id, profile, command, env):
        print("[bold green]Initiated Tenant Creation[/bold green]")
        tenant_name = input("Enter Tenant Name: ")
        tenant_email = input("Enter Tenant Email: ")
        tenant_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        command = f"""
        python3 manage.py setup_tenant {tenant_name} {tenant_email} {tenant_password} --test_tenant=False
        """
        
        return_code = subprocess.call(
                [f'export APIGatewayURL=https://api.{env}.gravtee.com/ \
                export PRIVATE_PEM_FILE=s3://gravty-{env}/cert/keys/private.pem \
                aws ecs execute-command  \
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
