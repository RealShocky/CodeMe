from pathlib import Path
import logging
from typing import Dict, Any
import ast
import autopep8
from datetime import datetime

class CodeManager:
    def __init__(self, project_manager):
        """Initialize CodeManager with a ProjectManager instance"""
        self.project_manager = project_manager
        self.logger = logging.getLogger(__name__)

    async def execute_action(self, plan: Dict[str, Any]):
        """Execute a code-related action plan"""
        try:
            self.logger.info(f"Executing code action: {plan['description']}")
            
            # Ensure we have a current project
            current_project = self.project_manager.get_current_project()
            if not current_project:
                print("\n⚠️ No project loaded. Please create or load a project first.")
                return

            for step in plan["steps"]:
                if step["type"] == "create_file":
                    file_name = step["params"]["file_name"]
                    content = plan.get("code", "")
                    await self.create_file(file_name, content)
                elif step["type"] == "modify_file":
                    await self.modify_file(plan["file_path"], step["params"])
                elif step["type"] == "analyze_code":
                    await self.analyze_code(plan["file_path"])
                    
            self.logger.info(f"Code action completed: {plan['description']}")
        
        except Exception as e:
            self.logger.error(f"Error executing code action: {e}")
            raise

    async def create_file(self, file_name: str, content: str = ""):
        """Create a new file with the given content"""
        try:
            current_project = self.project_manager.get_current_project()
            if not current_project:
                raise ValueError("No project currently loaded")

            # Determine the correct subdirectory based on file type
            if file_name.endswith('.py'):
                base_dir = current_project / "src"
            elif file_name.endswith('_test.py') or file_name.startswith('test_'):
                base_dir = current_project / "tests"
            else:
                base_dir = current_project / "src"  # default to src

            # Create full path
            full_path = base_dir / file_name
            
            # Create parent directories if they don't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Add default content if file is empty
            if not content:
                content = f"""# Created by CodeMe Assistant
# Project: {current_project.name}
# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
            
            # Format the code if it's a Python file
            if full_path.suffix == '.py':
                content = autopep8.fix_code(content)
            
            # Write the file
            full_path.write_text(content)
            self.logger.info(f"Created file: {full_path}")
            
            # Track the file in the project
            self.project_manager.add_file_to_project(full_path)
            
            print(f"\n✅ Created file: {full_path}")
            return full_path
            
        except Exception as e:
            self.logger.error(f"Error creating file: {e}")
            raise

    async def modify_file(self, file_path: str, modifications: Dict[str, Any]):
        """Modify an existing file"""
        try:
            current_project = self.project_manager.get_current_project()
            if not current_project:
                raise ValueError("No project currently loaded")

            # Handle both absolute and relative paths
            if Path(file_path).is_absolute():
                full_path = Path(file_path)
            else:
                full_path = current_project / file_path
                
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Read existing content
            content = full_path.read_text()
            
            # Apply modifications
            if modifications.get("append"):
                content += f"\n{modifications['append']}"
            elif modifications.get("prepend"):
                content = f"{modifications['prepend']}\n{content}"
            elif modifications.get("replace"):
                content = modifications["replace"]
            
            # Format Python files
            if full_path.suffix == '.py':
                content = autopep8.fix_code(content)
            
            # Write back to file
            full_path.write_text(content)
            self.logger.info(f"Modified file: {full_path}")
            print(f"\n✅ Modified file: {full_path}")
            
        except Exception as e:
            self.logger.error(f"Error modifying file: {e}")
            raise

    async def analyze_code(self, file_path: str) -> Dict[str, Any]:
        """Analyze code structure and quality"""
        try:
            current_project = self.project_manager.get_current_project()
            if not current_project:
                raise ValueError("No project currently loaded")

            full_path = current_project / file_path
            content = full_path.read_text()
            
            # Parse the code
            tree = ast.parse(content)
            
            # Analyze structure
            analysis = {
                "classes": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                "functions": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                "imports": len([n for n in ast.walk(tree) if isinstance(n, ast.Import) or isinstance(n, ast.ImportFrom)]),
                "lines": len(content.splitlines()),
                "content": content
            }
            
            print(f"\n📊 Code Analysis for {file_path}:")
            print(f"  Lines of code: {analysis['lines']}")
            print(f"  Classes: {analysis['classes']}")
            print(f"  Functions: {analysis['functions']}")
            print(f"  Imports: {analysis['imports']}")
            print("\n📝 File Contents:")
            print(f"\n{content}")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing code: {e}")
            raise