import os
import logging
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import boto3

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Default port for the sidecar
PORT = 8080

# Environment variable to specify secrets source (e.g., "dotenv", "ssm")
SECRETS_SOURCE = os.environ.get("SECRETS_SOURCE", "dotenv")

# Dictionary to store secrets
secrets = {}

app = FastAPI()

def load_dotenv_secrets(filepath=".env"):
    """Loads secrets from a .env file."""
    load_dotenv(filepath)
    return dict(os.environ)

def load_ssm_parameters():
    """Loads parameters from AWS Systems Manager Parameter Store."""
    try:
        region_name = os.environ.get("AWS_REGION_NAME")
        parameter_names = os.environ.get("SSM_PARAMETER_NAMES")

        if not region_name or not parameter_names:
            logging.error("AWS_REGION_NAME or SSM_PARAMETER_NAMES not set.")
            return {}

        ssm_client = boto3.client('ssm', region_name=region_name)
        parameter_names_list = parameter_names.split(',')
        results = {}
        for name in parameter_names_list:
            try:
                response = ssm_client.get_parameter(Name=name.strip(), WithDecryption=True)
                results[name.split('/')[-1]] = response['Parameter']['Value']
            except Exception as e:
                logging.error(f"Error fetching parameter {name}: {e}")
        return results

    except ImportError:
        logging.error("boto3 not installed. AWS SSM Parameter loading disabled.")
        return {}
    except Exception as e:
        logging.error(f"Error loading SSM parameters: {e}")
        return {}

def load_secrets():
    """Loads secrets based on the SECRETS_SOURCE environment variable."""
    global secrets
    if SECRETS_SOURCE == "ssm":
        secrets = load_ssm_parameters()
    elif SECRETS_SOURCE == "dotenv":
        secrets = load_dotenv_secrets()
    else:
        logging.error("SECRETS_SOURCE not set correctly. using .env as default")
        secrets = load_dotenv_secrets()

    logging.info(f"Secrets loaded from {SECRETS_SOURCE}: {list(secrets.keys())}")

@app.get("/{key}")
async def get_secret(key: str):
    """Handles GET requests for secrets."""
    if key in secrets:
        return {key: secrets[key]}
    else:
        raise HTTPException(status_code=404, detail="Secret not found")

if __name__ == "__main__":
    load_secrets()
    uvicorn.run(app, host="0.0.0.0", port=PORT)
    