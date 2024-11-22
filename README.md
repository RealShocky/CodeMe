# CodeMe AI Voice Assistant 🎙️

A powerful voice-controlled coding assistant that helps you write, manage, and deploy code through natural language commands. Built with Python and powered by state-of-the-art AI.

## 🌟 Features

- **Voice Control**: Interact with your development environment using natural voice commands
- **Project Management**: Create, load, and manage multiple coding projects
- **Code Generation**: Generate code based on natural language descriptions
- **Code Analysis**: Analyze and improve code quality
- **Testing Support**: Generate and run tests for your code
- **Deployment**: Handle deployment tasks through voice commands
- **Multi-Modal**: Works with both voice and text commands
- **Project Backups**: Automatic project backup functionality
- **Extensible**: Modular design for easy feature additions

## 🛠️ Components

- `voice_assistant.py`: Core assistant functionality and command processing
- `project_manager.py`: Project creation and management
- `code_manager.py`: Code generation and modification
- `test_manager.py`: Test creation and execution
- `deployment_manager.py`: Deployment and environment management
- `utils/`: Helper functions and utilities

## 🚀 Getting Started

1. **Prerequisites**
   - Python 3.12+
   - Required packages (install via `pip install -r requirements.txt`)
   - OpenAI API key (for AI features)
   - Anthropic API key (for Claude integration)

2. **Installation**
   ```bash
   git clone <repository-url>
   cd codeme
   pip install -r requirements.txt

3. **Configuration**
Copy .env.example to .env
Add your API keys to .env
Configure config.json for custom settings

4. **Run**
python src/main.py

💬 Commands
Project Commands
create project [name] [description]: Create a new coding project
load project [name]: Switch to an existing project
list projects: Show all available projects
delete project [name]: Remove a project (creates backup first)
backup project: Create a backup of the current project
show project files: List all files in the current project

File Commands
create file [name] in src/tests/docs: Create a new file in specified directory
edit file [name]: Modify an existing file
show file [name]: Display file contents
run tests for current project: Execute project tests

Voice Commands
Start with "hey assistant" followed by your command

Examples:
"hey assistant, create a new web app project"
"hey assistant, add a login function to app.py"
"hey assistant, run all tests"

🔧 Project Structure

codeme/
├── src/                  # Source code
│   ├── main.py          # Entry point
│   ├── voice_assistant.py# Core assistant
│   ├── project_manager.py# Project management
│   ├── code_manager.py  # Code operations
│   ├── test_manager.py  # Testing functionality
│   └── utils/           # Utilities
├── tests/               # Test files
├── projects/            # User projects
├── backups/            # Project backups
├── templates/          # Code templates
└── config.json         # Configuration

🔍 Troubleshooting
Voice Recognition Issues
Ensure your microphone is properly connected
Check microphone permissions
Try speaking clearly and at a moderate pace

API Connection Problems
Verify API keys in .env
Check internet connection
Ensure API services are available

Project Loading Issues
Confirm project exists in projects directory
Check file permissions
Verify project structure is intact

🛠️ Development Setup
Environment Setup

python -m venv venv

source venv/bin/activate  # or venv\Scripts\activate on Windows

pip install -r requirements.txt

IDE Configuration
Recommended: VSCode with Python extension
Enable linting (pylint)
Configure test discovery

Testing
python -m pytest tests/

🤝 Contributing
Fork the repository
Create a feature branch
Commit your changes
Push to the branch
Create a Pull Request

📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

🙏 Acknowledgments
OpenAI for GPT integration
Anthropic for Claude integration
Speech recognition libraries
All contributors and users
Made with ❤️ by the Vibration Robotics team