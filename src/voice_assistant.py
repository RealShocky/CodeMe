import speech_recognition as sr
from anthropic import Anthropic
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union
import asyncio
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
import sys
import aioconsole
from datetime import datetime

from src.project_manager import ProjectManager
from src.code_manager import CodeManager
from src.test_manager import TestManager
from src.deployment_manager import DeploymentManager

class VoiceCodingAssistant:
    def __init__(self, anthropic_api_key: str, project_root: str, wake_word: str):
        self.client = Anthropic(api_key=anthropic_api_key)
        self.recognizer = sr.Recognizer()
        self.wake_word = wake_word.lower()
        self.is_running = False
        self.logger = logging.getLogger(__name__)
        self.command_queue = asyncio.Queue()
        self.loop = None
        self.history = []
        
        # Initialize project manager first
        self.project_manager = ProjectManager(project_root)
        
        # Initialize managers with project manager
        self.code_manager = CodeManager(self.project_manager)
        self.test_manager = TestManager(self.project_manager)
        self.deployment_manager = DeploymentManager(project_root)
        
        # Project context
        self.context = {
            "current_file": None,
            "project_root": project_root,
            "current_project": None,
            "last_action": None,
            "current_task": None,
            "session_start": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    async def start(self):
        """Start the voice assistant"""
        self.is_running = True
        self.loop = asyncio.get_running_loop()
        print("\n🚀 Starting CodeMe AI Voice Assistant...")
        self.logger.info("Starting voice recognition...")
        
        # Start voice recognition in a separate thread
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.voice_future = self.loop.run_in_executor(
            self.executor, 
            self._voice_recognition_loop
        )
        
        # Start text input loop
        asyncio.create_task(self._text_input_loop())
        
        # Start command processing loop
        try:
            await self._command_processing_loop()
        except Exception as e:
            self.logger.error(f"Error in command processing loop: {e}")
            print(f"\n❌ Error in command processing: {e}")
            await self.stop()

    async def stop(self):
        """Stop the voice assistant"""
        self.is_running = False
        print("\n👋 Shutting down assistant...")
        self.logger.info("Stopping voice assistant...")
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        
        # Save command history
        self._save_history()

    def _voice_recognition_loop(self):
        """Handle continuous voice recognition"""
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            self._print_help()
            self.logger.info("Microphone ready, listening for commands...")
            
            while self.is_running:
                try:
                    audio = self.recognizer.listen(source)
                    text = self.recognizer.recognize_google(audio).lower()
                    
                    if self.wake_word in text:
                        command = text.replace(self.wake_word, "").strip()
                        asyncio.run_coroutine_threadsafe(
                            self.command_queue.put(("voice", command)),
                            self.loop
                        )
                        print(f"\n🎯 Voice command received: '{command}'")
                        
                except sr.UnknownValueError:
                    pass
                except Exception as e:
                    self.logger.error(f"Error in voice recognition: {e}")
                    print(f"\n❌ Error understanding audio: {e}")

    async def _text_input_loop(self):
        """Handle text input commands"""
        while self.is_running:
            try:
                command = await aioconsole.ainput("\n💭 Type a command (or 'help', 'quit'): ")
                command = command.strip().lower()
                
                if not command:
                    continue
                    
                if command == 'quit':
                    print("\n👋 Shutting down...")
                    self.is_running = False
                    break
                    
                if command == 'help':
                    self._print_help()
                    continue
                    
                if command == 'history':
                    self._show_history()
                    continue
                    
                if command == 'context':
                    self._show_context()
                    continue
                    
                if command == 'projects':
                    self._show_projects()
                    continue
                
                await self.command_queue.put(("text", command))
                
            except Exception as e:
                self.logger.error(f"Error in text input: {e}")
                print(f"\n❌ Error processing text input: {e}")

    def _print_help(self):
        """Print help information"""
        print("\n🎤 Voice Commands: Say 'hey assistant' followed by your command...")
        print("\n💻 Text Commands:")
        print("   - Type your command directly")
        print("   - 'help'    : Show this help message")
        print("   - 'quit'    : Exit the program")
        print("   - 'history' : Show command history")
        print("   - 'context' : Show current context")
        print("   - 'projects': List all projects")
        print("\n📂 Project Commands:")
        print("   - create project [name] [description]")
        print("   - load project [name]")
        print("   - list projects")
        print("   - delete project [name]")
        print("   - backup project")
        print("   - show project files")
        print("\n📝 File Commands:")
        print("   - create file [name] in src/tests/docs")
        print("   - edit file [name]")
        print("   - show file [name]")
        print("   - run tests for current project")
        print("\n📚 Example Commands:")
        print("   - create project MyWebApp 'A web application project'")
        print("   - load project MyWebApp")
        print("   - create file app.py in src")
        print("   - add a hello world function to app.py")
        print("   - run tests for this project")
        print("   - backup project")

    def _show_history(self):
        """Show command history"""
        print("\n📜 Command History:")
        for entry in self.history[-10:]:  # Show last 10 commands
            print(f"  {entry['timestamp']} - [{entry['type']}] {entry['command']}")

    def _show_context(self):
        """Show current context"""
        print("\n🔍 Current Context:")
        print(f"  Project Root: {self.context['project_root']}")
        project_name = self.project_manager.get_current_project().name if self.project_manager.get_current_project() else "None"
        print(f"  Current Project: {project_name}")
        print(f"  Current File: {self.context['current_file']}")
        print(f"  Last Action: {self.context['last_action']}")
        print(f"  Session Start: {self.context['session_start']}")

    def _show_projects(self):
        """Show all projects"""
        projects = self.project_manager.list_projects()
        print("\n📁 Projects:")
        if not projects:
            print("  No projects found")
            return
        for project in projects:
            print(f"\n  📂 {project['name']}")
            print(f"     Description: {project['description']}")
            print(f"     Created: {project['created_at']}")
            print(f"     Last Accessed: {project['last_accessed']}")

    def _save_history(self):
        """Save command history to file"""
        try:
            history_file = Path(self.context['project_root']) / 'logs' / 'command_history.json'
            history_file.parent.mkdir(exist_ok=True)
            
            existing_history = []
            if history_file.exists():
                with open(history_file) as f:
                    existing_history = json.load(f)
                    
            # Combine existing history with new commands
            all_history = existing_history + self.history
            
            # Keep last 1000 commands
            all_history = all_history[-1000:]
            
            with open(history_file, 'w') as f:
                json.dump(all_history, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving history: {e}")

    async def _command_processing_loop(self):
        """Process commands from the queue"""
        while self.is_running:
            try:
                command_type, command = await self.command_queue.get()
                
                # Handle project management commands directly
                if self._handle_project_command(command):
                    continue
                
                # Add to history
                self.history.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'type': command_type,
                    'command': command
                })
                
                await self._process_command(command)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing command: {e}")
                print(f"\n❌ Error processing command: {e}")
                await asyncio.sleep(0.1)

    def _handle_project_command(self, command: str) -> bool:
        """Handle project management commands"""
        try:
            cmd_parts = command.split()
            if len(cmd_parts) >= 2:
                if cmd_parts[0] == "create" and cmd_parts[1] == "project":
                    name = cmd_parts[2]
                    description = " ".join(cmd_parts[3:]) if len(cmd_parts) > 3 else ""
                    self.project_manager.create_project(name, description)
                    print(f"\n✅ Created project: {name}")
                    return True
                
                elif cmd_parts[0] == "load" and cmd_parts[1] == "project":
                    name = cmd_parts[2]
                    self.project_manager.load_project(name)
                    print(f"\n✅ Loaded project: {name}")
                    return True
                
                elif cmd_parts[0] == "delete" and cmd_parts[1] == "project":
                    name = cmd_parts[2]
                    self.project_manager.delete_project(name)
                    print(f"\n✅ Deleted project: {name}")
                    return True
                
                elif cmd_parts[0] == "backup" and cmd_parts[1] == "project":
                    backup_path = self.project_manager.backup_project()
                    print(f"\n✅ Created backup at: {backup_path}")
                    return True
                
            elif command == "list projects":
                self._show_projects()
                return True
                
        except Exception as e:
            print(f"\n❌ Error in project command: {e}")
            return True
            
        return False

    async def _process_command(self, command: str):
        """Process voice command using Claude"""
        try:
            print("\n🤖 Processing command...")
            self.logger.info(f"Processing command: {command}")
            
            # Check if we have a current project
            if not self.project_manager.get_current_project() and not command.startswith(("create project", "load project", "list project")):
                print("\n⚠️ No project loaded. Please create or load a project first.")
                return
            
            # Prepare context for Claude
            prompt = self._create_prompt(command)
            
            print("⏳ Thinking about how to help...")
            # Get response from Claude using thread pool
            response = await self.loop.run_in_executor(
                self.executor,
                lambda: self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=4096,
                    temperature=0,
                    system="You are an AI coding assistant that helps write, test, and deploy code. Convert voice commands into specific coding actions. IMPORTANT: Respond with a single JSON object representing the action plan.",
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
            )
            
            print("🔄 Executing your request...")
            # Parse and execute the action plan
            await self._execute_action_plan(response.content)
            
        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            print(f"\n❌ Error: {e}")

    def _create_prompt(self, command: str) -> str:
        """Create a detailed prompt for Claude"""
        current_project = self.project_manager.get_current_project()
        project_name = current_project.name if current_project else "None"
        
        return f"""
You are a voice-controlled coding assistant. Parse the command and respond with a SINGLE JSON object containing the action plan.
DO NOT include any explanatory text - ONLY output valid JSON.

Command: {command}
Current Context:
- Project Root: {self.context['project_root']}
- Current Project: {project_name}
- Current File: {self.context['current_file']}
- Last Action: {self.context['last_action']}
- Current Task: {self.context['current_task']}

When handling file operations:
1. Use the current_file path if the command refers to "this file", "that file", or similar
2. For editing commands, include both the file path and the content to write
3. For modifications, include the entire new content of the file
4. For showing file contents, use the "analyze_code" type
5. Place new files in the appropriate project subdirectory (src/tests/docs)

Required JSON format:
{{
    "action_type": "code|test|deploy|navigate",
    "description": "Detailed description of what will be done",
    "steps": [
        {{
            "type": "create_file|modify_file|analyze_code",
            "params": {{
                "file_name": "path/to/file",
                "content": "complete content to write to file",
                "mode": "write|append|prepend"
            }}
        }}
    ],
    "code": "complete file content",
    "file_path": "full/path/to/file"
}}

If the command refers to the current file, use this path: {self.context['current_file']}
"""

    async def _execute_action_plan(self, response):
        """Execute the action plan from Claude"""
        try:
            # Handle TextBlock response from Claude
            if hasattr(response, 'content'):
                response = response.content
                
            if isinstance(response, list) and len(response) > 0 and hasattr(response[0], 'text'):
                json_str = response[0].text
            else:
                json_str = response if isinstance(response, str) else str(response)
            
            # Clean the response to ensure it's valid JSON
            json_str = json_str.strip()
            if json_str.startswith('```json'):
                json_str = json_str[7:]
            if json_str.endswith('```'):
                json_str = json_str[:-3]
            json_str = json_str.strip()
            
            # Log the cleaned JSON for debugging
            self.logger.debug(f"Cleaned JSON string: {json_str}")
            
            # Parse the JSON
            try:
                plan = json.loads(json_str)
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON response from Claude: {json_str}")
                print(f"\n❌ Error understanding Claude's response: {e}")
                return
            
            print(f"\n📝 Plan: {plan['description']}")
            self.logger.info(f"Executing plan: {plan['description']}")
            
            # Execute the appropriate action based on type
            if plan["action_type"] == "code":
                await self.code_manager.execute_action(plan)
                print(f"\n✅ Code action completed: {plan['description']}")
            elif plan["action_type"] == "test":
                await self.test_manager.execute_action(plan)
                print(f"\n✅ Test action completed: {plan['description']}")
            elif plan["action_type"] == "deploy":
                await self.deployment_manager.execute_action(plan)
                print(f"\n✅ Deployment action completed: {plan['description']}")
            elif plan["action_type"] == "navigate":
                self.logger.info("Navigation command received")
                print("\n❓ Could you please clarify your request?")
            else:
                self.logger.warning(f"Unknown action type: {plan['action_type']}")
                print(f"\n⚠️ Unknown action type: {plan['action_type']}")
            
            # Update context
            self.context["last_action"] = plan["description"]
            if plan.get("file_path"):
                self.context["current_file"] = plan["file_path"]
                print(f"\n📂 Current file: {self.context['current_file']}")
            
            # Update current project in context
            current_project = self.project_manager.get_current_project()
            if current_project:
                self.context["current_project"] = current_project.name
            
            print("\n🎤 Ready for next command...")
                
        except Exception as e:
            self.logger.error(f"Error executing action plan: {e}")
            self.logger.error(f"Response was: {response}")
            print(f"\n❌ Error executing action: {e}")
            raise