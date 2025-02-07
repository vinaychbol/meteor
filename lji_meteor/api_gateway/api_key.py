import boto3
import psycopg2
from urllib.parse import urlparse
from rich import print
import json

from lji_meteor.rds import rds

class ApiKey():
    
    def __init__(self, session, profile, data, id_rsa_public, env):
        self.data = data
        self.id_rsa_public = id_rsa_public
        self.profile = profile
        self.session = session
        self.env = env
        self.region = data['db']['region']
        
    def add_to_usage_plan(self, api_key):
        print("adding usage plan to the api key")
        client = self.session.client('apigateway', region_name=self.region)
        usage_plan_name = f"Router-new-plan-{self.env.lower()}"
        usage_plan_id = None
        response = client.get_usage_plans()
        for item in response['items']:
            if item['name'] == usage_plan_name:
                usage_plan_id = item['id']
                break
        
        try:
            response = client.create_usage_plan_key(
                usagePlanId=usage_plan_id,
                keyId=api_key,
                keyType='API_KEY',
            )
        except Exception as e:
            print(f"Error adding usage plan to the api key: {e}")
            return
        
    def add_x_api_key(self, schema):
        
        print("[bold green]Initiated API Key Creation[/bold green]")
        try:
            client = self.session.client('apigateway', region_name=self.region)
            stage_name = f"Router-new-plan-{self.env.lower()}"
            response = client.create_api_key(name=schema, enabled=True)
            api_key = response['value']
            api_key_id = response['id']
            # print(json.dumps(response, indent=4, sort_keys=True, default=str))
        except Exception as e:
            print(f"Error creating API Key: {e}")
            return
        
        print(f"[bold green]API Key:[/bold green] {api_key}")
        
        self.add_to_usage_plan(api_key_id)
        
        print("adding x-api-key to the tenant db")
        
        # db = rds.DB(self.session, self.data, self.profile, self.id_rsa_public)
        # db_con_url = db.get_db_url(self.env)
        
        # result = urlparse(db_con_url)
        # username = result.username
        # password = result.password
        # database = result.path[1:]  # Removing the leading slash from the path
        # hostname = "localhost"
        # port = "2345"

        # try:
        #     # Establish connection to the database
        #     connection = psycopg2.connect(
        #         database=database,
        #         user=username,
        #         password=password,
        #         host=hostname,
        #         port=port
        #     )
            
        #     with connection.cursor() as curs:
                    
        #         update_query = f"""
        #         UPDATE public.core_loyaltytenant
        #         SET x_api_key = {api_key}
        #         WHERE name = {schema};
        #         """
        #         curs.execute(update_query)
        #         connection.commit()

        #         print(f"Updated api key {api_key} in core_loyaltytenant table.")
                
        # except Exception as e:
        #     print(f"Error connecting to the database and adding x-api-key into core_loyaltytenant table: {e}")
        # finally:
        #     # Make sure to close the connection
        #     if connection:
        #         connection.close()
        
        