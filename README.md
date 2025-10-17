# Meteor CLI

🚀 A powerful CLI tool for managing AWS resources and services with a focus on user-friendly interactions.

## Features

- 📱 Web Application Management (ECS)
- 💾 Database Operations (RDS)
- 📊 Data Lake Access
- 🔌 API Gateway Management
- 🖥️ EC2 Instance Access
- 🚀 Deployment Automation
- 💪 FitTribe Application Management

## Installation

## Prerequisites

Before installing Meteor CLI, ensure you have the following tools installed:

### 1. Homebrew (for macOS)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Python and pipx
#### Install Python 3.12 or later
```bash
brew install python@3.12
```
#### Install pipx
``` bash
brew install pipx
pipx ensurepath
```

### 3. AWS CLI

####Install AWS CLI
```bash
brew install awscli
```
#### Configure AWS CLI with your credentials
``` bash
aws configure
```

### 4. Session Manager Plugin
#### Install the Session Manager Plugin for AWS CLI
```bash
brew install --cask session-manager-plugin
```
#### Verify installation
``` bash
session-manager-plugin --version
```

### 5. AWS Credentials Setup
Make sure to set up your AWS credentials properly:
1. Create `~/.aws/credentials` with your profiles:
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY

[dev]
aws_access_key_id = YOUR_DEV_ACCESS_KEY
aws_secret_access_key = YOUR_DEV_SECRET_KEY
```

2. Create `~/.aws/config` with your regions:
```ini
[default]
region = us-west-2
output = json

[profile dev]
region = us-west-2
output = json
```

## Installation

After installing all prerequisites:

### Install using pipx (recommended)
```bash
pipx install https://github.com/vinaychbol/meteor/raw/refs/heads/main/dist/lji_meteor-latest.tar.gz
```

### Verify Installation
#### Check if meteor CLI is installed correctly
``` bash
meteor --version
```
#### Run the doctor command to verify all dependencies
``` bash
meteor doctor
```

## Quick Start

#### Run meteor without any commands to see the interactive menu
```bash
meteor
```
#### Or use specific commands directly
```
meteor webapp --env dev --profile myprofile
```

## Available Commands

### 1. Webapp Management

#### Connect to webapp container
```bash
meteor webapp --env <environment> --profile <aws-profile>
```

### 2. Database Operations
```bash
# Connect to database
meteor db --env <environment> --profile <aws-profile>

# Get database root credentials
meteor db --env <environment> --profile <aws-profile> --get-credentials

# Update superuser permissions
meteor db --env <environment> --profile <aws-profile> --superuser <email> --tenant-schema <schema>
```

### 3. Data Lake Access
```bash
# Connect to datalake
meteor datalake --env <environment> --profile <aws-profile>

# Connect to datalake shell
meteor datalake --env <environment> --profile <aws-profile> --connect
```
### 4. Deployment
```bash
# Deploy a service
meteor deploy --env <environment> --service <service-name> --tag <version-tag>
```

### 5. Connect to FitTribe Shell
```bash
# Connect to FitTribe container
meteor fittribe --env <environment> --profile <aws-profile>
```

## Development Guide

### Prerequisites

1. Python 3.12 or higher
2. AWS CLI configured with appropriate profiles
3. Session Manager Plugin for AWS CLI
4. Poetry (for development)

### Project Structure
```
lji_meteor/
├── __init__.py
├── main.py                  # Main CLI implementation
├── api_gateway/            # API Gateway management
├── autodeployment/        # Deployment automation
├── rds/                   # Database operations
├── tenant/               # Tenant management
└── utils/                # Shared utilities
```

### Setting Up Development Environment

1. Clone the repository:
```bash
git clone https://github.com/vinaychbol/meteor.git
cd meteor
```

2. Install dependencies:
```bash
poetry install
```

3. Activate virtual environment:
```bash
poetry shell
```

### Adding New Commands

1. Create a new function in `main.py`:
```python
@app.command()
@env_and_creds_layer
def your_command(
    env: Annotated[str, typer.Option(help="Environment Name")] = None,
    profile: Annotated[str, typer.Option(help="AWS Profile Name")] = None,
    data: Annotated[str, typer.Option(help="Configuration Data")] = None
):
    """Your command description"""
    # Your implementation here
```

2. Add any supporting modules in appropriate directories:
```python
# lji_meteor/your_module/your_file.py
class YourClass:
    def __init__(self, session, data, profile):
        self.session = session
        self.data = data
        self.profile = profile

    def your_method(self):
        # Implementation
        pass
```

### Best Practices

1. **Error Handling**: Always use try-except blocks with proper error messages
```python
try:
    # Your code
except Exception as e:
    console.print(f"[bold red]❌ Error:[/bold red] {str(e)}")
```

2. **Progress Indicators**: Use rich console for better UX
```python
with console.status("[bold blue]🔄 Processing...[/bold blue]", spinner="dots"):
    # Your long-running operation
```

3. **Documentation**: Always include docstrings and help text
```python
@app.command()
def your_command():
    """
    Detailed description of what your command does.
    """
    pass
```

### Building and Testing

1. Build the package:
```bash
poetry build
```

2. Install locally for testing:
```bash
pipx install dist/*.whl --force
```

3. Run tests:
```bash
poetry run pytest
```

## Environment Variables

The CLI respects the following environment variables:
- `AWS_PROFILE`: Default AWS profile
- `AWS_DEFAULT_REGION`: Default AWS region

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed list of changes in each version.

Current Version: v0.0.2 (October 2025)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
