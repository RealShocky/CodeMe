import asyncio
from pathlib import Path
import logging
from typing import Dict, Any
import json
import shutil
import subprocess
import docker
from datetime import datetime

class DeploymentManager:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
        self.config_path = self.project_root / "deployments" / "deployment_config.json"
        self.docker_client = None
        try:
            self.docker_client = docker.from_env()
        except:
            self.logger.warning("Docker not available. Container deployments disabled.")

    async def execute_action(self, action_plan: Dict[str, Any]):
        """Execute a deployment-related action plan"""
        try:
            for step in action_plan["steps"]:
                if step["type"] == "build":
                    await self.build_project(step["params"])
                elif step["type"] == "deploy":
                    await self.deploy(step["params"])
                elif step["type"] == "rollback":
                    await self.rollback(step["params"])
                elif step["type"] == "status":
                    await self.get_deployment_status()
                    
        except Exception as e:
            self.logger.error(f"Error executing deployment action: {e}")
            raise

    async def build_project(self, params: Dict[str, Any]):
        """Build the project for deployment"""
        try:
            # Create build directory
            build_dir = self.project_root / "build"
            build_dir.mkdir(exist_ok=True)
            
            # Copy project files
            deploy_files = params.get("files", ["src", "requirements.txt"])
            for file in deploy_files:
                source = self.project_root / file
                dest = build_dir / file
                if source.is_dir():
                    shutil.copytree(source, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(source, dest)

            # Run build commands
            build_commands = params.get("commands", [])
            for cmd in build_commands:
                process = await asyncio.create_subprocess_exec(
                    *cmd.split(),
                    cwd=str(build_dir),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"Build command failed: {stderr.decode()}")
                
            # Create Docker image if specified
            if params.get("create_docker_image") and self.docker_client:
                await self._create_docker_image(build_dir, params.get("docker_tag", "latest"))
                
            self.logger.info("Build completed successfully")
            
        except Exception as e:
            self.logger.error(f"Build failed: {e}")
            raise

    async def deploy(self, params: Dict[str, Any]):
        """Deploy the project to the specified environment"""
        try:
            environment = params.get("environment", "development")
            deployment_config = self._load_deployment_config()
            
            if environment not in deployment_config:
                raise ValueError(f"Environment '{environment}' not found in deployment config")
            
            env_config = deployment_config[environment]
            
            # Create deployment directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            deploy_dir = self.project_root / "deployments" / environment / timestamp
            deploy_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy build artifacts
            build_dir = self.project_root / "build"
            if build_dir.exists():
                shutil.copytree(build_dir, deploy_dir, dirs_exist_ok=True)
            
            # Run deployment steps
            if env_config.get("type") == "docker":
                await self._deploy_docker(env_config, params)
            else:
                await self._deploy_standard(deploy_dir, env_config, params)
            
            # Update deployment status
            self._update_deployment_status(environment, {
                "timestamp": timestamp,
                "version": params.get("version", "latest"),
                "status": "active",
                "path": str(deploy_dir)
            })
            
            self.logger.info(f"Deployment to {environment} completed successfully")
            
        except Exception as e:
            self.logger.error(f"Deployment failed: {e}")
            raise

    async def rollback(self, params: Dict[str, Any]):
        """Rollback to a previous deployment"""
        try:
            environment = params["environment"]
            version = params.get("version")
            
            # Get deployment history
            status_file = self.project_root / "deployments" / "status.json"
            if not status_file.exists():
                raise FileNotFoundError("No deployment history found")
                
            status = json.loads(status_file.read_text())
            
            if environment not in status:
                raise ValueError(f"No deployments found for environment: {environment}")
                
            # Find deployment to rollback to
            deployments = status[environment]["history"]
            target_deployment = None
            
            if version:
                target_deployment = next(
                    (d for d in deployments if d["version"] == version),
                    None
                )
            else:
                # Rollback to previous deployment
                if len(deployments) < 2:
                    raise ValueError("No previous deployment found")
                target_deployment = deployments[-2]
            
            if not target_deployment:
                raise ValueError(f"Deployment version {version} not found")
            
            # Perform rollback
            deploy_dir = Path(target_deployment["path"])
            deployment_config = self._load_deployment_config()
            env_config = deployment_config[environment]
            
            if env_config.get("type") == "docker":
                await self._deploy_docker(env_config, {"version": target_deployment["version"]})
            else:
                await self._deploy_standard(deploy_dir, env_config, {})
            
            # Update status
            self._update_deployment_status(environment, {
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "version": target_deployment["version"],
                "status": "active",
                "path": str(deploy_dir),
                "rollback": True
            })
            
            self.logger.info(f"Rollback completed successfully")
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            raise

    async def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status"""
        try:
            status_file = self.project_root / "deployments" / "status.json"
            if status_file.exists():
                return json.loads(status_file.read_text())
            return {}
        except Exception as e:
            self.logger.error(f"Error getting deployment status: {e}")
            raise

    async def _create_docker_image(self, build_dir: Path, tag: str):
        """Create Docker image from build directory"""
        try:
            if not self.docker_client:
                raise Exception("Docker not available")
                
            dockerfile = build_dir / "Dockerfile"
            if not dockerfile.exists():
                raise FileNotFoundError("Dockerfile not found in build directory")
                
            self.docker_client.images.build(
                path=str(build_dir),
                tag=tag,
                rm=True
            )
            
            self.logger.info(f"Docker image created: {tag}")
            
        except Exception as e:
            self.logger.error(f"Error creating Docker image: {e}")
            raise

    async def _deploy_docker(self, env_config: Dict[str, Any], params: Dict[str, Any]):
        """Deploy using Docker"""
        try:
            if not self.docker_client:
                raise Exception("Docker not available")
                
            # Pull image if specified
            image = env_config.get("image", params.get("version", "latest"))
            self.docker_client.images.pull(image)
            
            # Stop existing container
            container_name = env_config.get("container_name")
            try:
                container = self.docker_client.containers.get(container_name)
                container.stop()
                container.remove()
            except:
                pass
            
            # Start new container
            self.docker_client.containers.run(
                image,
                name=container_name,
                detach=True,
                ports=env_config.get("ports", {}),
                environment=env_config.get("environment", {})
            )
            
            self.logger.info(f"Docker deployment completed: {image}")
            
        except Exception as e:
            self.logger.error(f"Docker deployment failed: {e}")
            raise

    async def _deploy_standard(self, deploy_dir: Path, env_config: Dict[str, Any], params: Dict[str, Any]):
        """Deploy using standard file copy and commands"""
        try:
            # Run pre-deploy commands
            for cmd in env_config.get("pre_deploy_commands", []):
                process = await asyncio.create_subprocess_exec(
                    *cmd.split(),
                    cwd=str(deploy_dir),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"Pre-deploy command failed: {stderr.decode()}")
            
            # Copy to deployment location
            deploy_location = env_config.get("location")
            if deploy_location:
                deploy_path = Path(deploy_location)
                deploy_path.mkdir(parents=True, exist_ok=True)
                shutil.copytree(deploy_dir, deploy_path, dirs_exist_ok=True)
            
            # Run post-deploy commands
            for cmd in env_config.get("post_deploy_commands", []):
                process = await asyncio.create_subprocess_exec(
                    *cmd.split(),
                    cwd=str(deploy_location if deploy_location else deploy_dir),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"Post-deploy command failed: {stderr.decode()}")
            
            self.logger.info("Standard deployment completed successfully")
            
        except Exception as e:
            self.logger.error(f"Standard deployment failed: {e}")
            raise

    def _load_deployment_config(self) -> Dict[str, Any]:
        """Load deployment configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError("Deployment configuration not found")
        return json.loads(self.config_path.read_text())

    def _update_deployment_status(self, environment: str, deployment_info: Dict[str, Any]):
        """Update deployment status file"""
        try:
            status_file = self.project_root / "deployments" / "status.json"
            status = {}
            
            if status_file.exists():
                status = json.loads(status_file.read_text())
            
            if environment not in status:
                status[environment] = {"current": None, "history": []}
            
            # Update current deployment
            status[environment]["current"] = deployment_info
            
            # Add to history
            status[environment]["history"].append(deployment_info)
            
            # Keep only last 5 deployments in history
            status[environment]["history"] = status[environment]["history"][-5:]
            
            # Save status file
            status_file.write_text(json.dumps(status, indent=2))
            
        except Exception as e:
            self.logger.error(f"Error updating deployment status: {e}")
            raise