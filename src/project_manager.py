import json
from pathlib import Path
import shutil
from datetime import datetime
from typing import Dict, List, Optional
import logging
import os

class ProjectManager:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.projects_dir = self.base_dir / "projects"
        self.projects_dir.mkdir(exist_ok=True)
        self.backups_dir = self.base_dir / "backups"
        self.backups_dir.mkdir(exist_ok=True)
        self.current_project = None
        self.logger = logging.getLogger(__name__)
        self.projects_file = self.base_dir / "projects.json"
        self.projects_data = self._load_projects_data()

        # Log initialization
        self.logger.info(f"ProjectManager initialized:")
        self.logger.info(f"Base directory: {self.base_dir}")
        self.logger.info(f"Projects directory: {self.projects_dir}")
        self.logger.info(f"Backups directory: {self.backups_dir}")

    def _is_safe_path(self, path: Path) -> bool:
        """Verify that a path is within the projects directory"""
        try:
            resolved_path = path.resolve()
            projects_resolved = self.projects_dir.resolve()
            backups_resolved = self.backups_dir.resolve()
            
            # Check if path is within projects or backups directory
            is_in_projects = projects_resolved in resolved_path.parents
            is_in_backups = backups_resolved in resolved_path.parents
            
            # Log path verification
            self.logger.debug(f"Path safety check - Path: {path}")
            self.logger.debug(f"Is in projects: {is_in_projects}")
            self.logger.debug(f"Is in backups: {is_in_backups}")
            
            return is_in_projects or is_in_backups
        except (ValueError, RuntimeError) as e:
            self.logger.error(f"Path safety check failed: {e}")
            return False

    def _load_projects_data(self) -> Dict:
        """Load projects metadata"""
        if self.projects_file.exists():
            try:
                return json.loads(self.projects_file.read_text())
            except json.JSONDecodeError as e:
                self.logger.error(f"Error loading projects data: {e}")
                return {"projects": {}, "last_accessed": None}
        return {"projects": {}, "last_accessed": None}

    def _save_projects_data(self):
        """Save projects metadata"""
        try:
            with open(self.projects_file, 'w') as f:
                json.dump(self.projects_data, f, indent=2)
            self.logger.info("Projects data saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving projects data: {e}")
            raise

    def create_project(self, name: str, description: str = "") -> Path:
        """Create a new project"""
        self.logger.info(f"Creating project: {name}")
        
        # Sanitize project name
        safe_name = "".join(c if c.isalnum() else "_" for c in name)
        project_dir = self.projects_dir / safe_name
        
        # Safety check
        if not self._is_safe_path(project_dir):
            error_msg = f"Invalid project path: {project_dir}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        if project_dir.exists():
            error_msg = f"Project '{name}' already exists"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Create project structure
            project_dir.mkdir(parents=True)
            (project_dir / "src").mkdir()
            (project_dir / "tests").mkdir()
            (project_dir / "docs").mkdir()
            
            print(f"\n📁 Creating project in: {project_dir}")
            
            # Create project config
            project_config = {
                "name": name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "files": [],
                "path": str(project_dir)
            }
            
            # Save project config
            with open(project_dir / "project.json", "w") as f:
                json.dump(project_config, indent=2, fp=f)
            
            # Update projects data
            self.projects_data["projects"][safe_name] = project_config
            self.projects_data["last_accessed"] = safe_name
            self._save_projects_data()
            
            self.current_project = project_dir
            self.logger.info(f"Project created successfully: {project_dir}")
            
            # Print project structure
            self.show_project_structure(project_dir)
            
            return project_dir
            
        except Exception as e:
            self.logger.error(f"Error creating project: {e}")
            # Cleanup if needed
            if project_dir.exists():
                shutil.rmtree(project_dir)
            raise

    def load_project(self, name: str) -> Path:
        """Load an existing project"""
        self.logger.info(f"Loading project: {name}")
        
        safe_name = "".join(c if c.isalnum() else "_" for c in name)
        project_dir = self.projects_dir / safe_name
        
        if not project_dir.exists():
            error_msg = f"Project '{name}' not found"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Safety check
        if not self._is_safe_path(project_dir):
            error_msg = f"Invalid project path: {project_dir}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Update last accessed
            if safe_name in self.projects_data["projects"]:
                self.projects_data["projects"][safe_name]["last_accessed"] = datetime.now().isoformat()
                self.projects_data["last_accessed"] = safe_name
                self._save_projects_data()
            
            self.current_project = project_dir
            print(f"\n📂 Loaded project: {project_dir}")
            
            # Show project structure
            self.show_project_structure(project_dir)
            
            return project_dir
            
        except Exception as e:
            self.logger.error(f"Error loading project: {e}")
            raise

    def show_project_structure(self, project_dir: Path):
        """Display project directory structure"""
        print("\n📁 Project Structure:")
        
        def print_tree(directory: Path, prefix: str = "", is_last: bool = True):
            print(prefix + ("└── " if is_last else "├── ") + directory.name)
            
            # Get all items in directory
            items = list(directory.iterdir())
            items = [item for item in items if not item.name.startswith('.')]
            items.sort(key=lambda x: (not x.is_dir(), x.name))
            
            for i, item in enumerate(items):
                new_prefix = prefix + ("    " if is_last else "│   ")
                if item.is_dir():
                    print_tree(item, new_prefix, i == len(items) - 1)
                else:
                    print(new_prefix + ("└── " if i == len(items) - 1 else "├── ") + item.name)
        
        print_tree(project_dir)

    def list_projects(self) -> List[Dict]:
        """List all projects with their details"""
        self.logger.info("Listing all projects")
        projects = []
        for name, data in self.projects_data["projects"].items():
            project_dir = self.projects_dir / name
            if project_dir.exists():
                project_info = {
                    "name": data["name"],
                    "description": data["description"],
                    "created_at": data["created_at"],
                    "last_accessed": data["last_accessed"],
                    "path": str(project_dir)
                }
                projects.append(project_info)
                print(f"\n📂 Project: {project_info['name']}")
                print(f"   Description: {project_info['description']}")
                print(f"   Created: {project_info['created_at']}")
                print(f"   Last Accessed: {project_info['last_accessed']}")
        return projects

    def get_current_project(self) -> Optional[Path]:
        """Get current project directory"""
        if self.current_project and not self._is_safe_path(self.current_project):
            self.logger.error("Current project path is not safe, resetting...")
            self.current_project = None
        return self.current_project

    def delete_project(self, name: str):
        """Delete a project"""
        self.logger.info(f"Deleting project: {name}")
        
        safe_name = "".join(c if c.isalnum() else "_" for c in name)
        project_dir = self.projects_dir / safe_name
        
        if not project_dir.exists():
            error_msg = f"Project '{name}' not found"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Safety check
        if not self._is_safe_path(project_dir):
            error_msg = f"Invalid project path: {project_dir}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Create backup before deletion
            backup_dir = self.backup_project(name)
            print(f"\n💾 Created backup at: {backup_dir}")
            
            # Delete project
            shutil.rmtree(project_dir)
            print(f"\n🗑️ Deleted project: {project_dir}")
            
            # Update projects data
            if safe_name in self.projects_data["projects"]:
                del self.projects_data["projects"][safe_name]
                if self.projects_data["last_accessed"] == safe_name:
                    self.projects_data["last_accessed"] = None
                self._save_projects_data()
            
            if self.current_project == project_dir:
                self.current_project = None
                
        except Exception as e:
            self.logger.error(f"Error deleting project: {e}")
            raise

    def add_file_to_project(self, file_path: Path):
        """Track a file in the project"""
        if not self.current_project:
            error_msg = "No project currently loaded"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Safety check
        if not self._is_safe_path(file_path):
            error_msg = f"Invalid file path: {file_path}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Make sure file is within current project
        if self.current_project not in file_path.parents:
            error_msg = f"File must be within current project: {self.current_project}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            rel_path = file_path.relative_to(self.current_project)
            project_name = self.current_project.name
            
            if project_name in self.projects_data["projects"]:
                if "files" not in self.projects_data["projects"][project_name]:
                    self.projects_data["projects"][project_name]["files"] = []
                self.projects_data["projects"][project_name]["files"].append(str(rel_path))
                self._save_projects_data()
                print(f"\n📝 Added file to project: {rel_path}")
                
        except Exception as e:
            self.logger.error(f"Error adding file to project: {e}")
            raise

    def get_project_files(self) -> List[Path]:
        """Get all files in current project"""
        if not self.current_project:
            return []
        
        try:
            project_name = self.current_project.name
            if project_name in self.projects_data["projects"]:
                files = [self.current_project / f for f in self.projects_data["projects"][project_name].get("files", [])]
                # Verify each file
                return [f for f in files if f.exists() and self._is_safe_path(f)]
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting project files: {e}")
            return []

    def backup_project(self, name: str = None) -> Path:
        """Backup a project"""
        try:
            if name:
                project_dir = self.projects_dir / name
            elif self.current_project:
                project_dir = self.current_project
            else:
                error_msg = "No project specified or currently loaded"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            if not project_dir.exists():
                error_msg = f"Project directory not found: {project_dir}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Safety check
            if not self._is_safe_path(project_dir):
                error_msg = f"Invalid project path: {project_dir}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Create backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.backups_dir / f"{project_dir.name}_{timestamp}"
            shutil.copytree(project_dir, backup_dir)
            
            self.logger.info(f"Created backup at: {backup_dir}")
            print(f"\n💾 Created backup at: {backup_dir}")
            
            return backup_dir
            
        except Exception as e:
            self.logger.error(f"Error backing up project: {e}")
            raise

    def get_project_path(self, name: str) -> Optional[Path]:
        """Get project path if it exists and is safe"""
        safe_name = "".join(c if c.isalnum() else "_" for c in name)
        project_dir = self.projects_dir / safe_name
        
        if project_dir.exists() and self._is_safe_path(project_dir):
            return project_dir
        return None