from pathlib import Path
from typing import Dict, Any
import json

class ProjectTemplates:
    TEMPLATES = {
        "python-basic": {
            "name": "Basic Python Project",
            "description": "Simple Python project structure with basic testing",
            "files": {
                "src/__init__.py": "",
                "src/main.py": """def main():
    print("Hello from {project_name}!")

if __name__ == "__main__":
    main()
""",
                "tests/__init__.py": "",
                "tests/test_main.py": """import pytest
from src.main import main

def test_main():
    # Add your tests here
    assert True
""",
                "requirements.txt": """pytest>=7.0.0
pytest-cov>=4.0.0
""",
                "README.md": """# {project_name}

{project_description}

## Setup
1. Install requirements: `pip install -r requirements.txt`
2. Run tests: `pytest`
3. Run the project: `python src/main.py`
"""
            }
        },
        "flask-web": {
            "name": "Flask Web Application",
            "description": "Web application using Flask framework",
            "files": {
                "src/__init__.py": "",
                "src/app.py": """from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
""",
                "src/templates/index.html": """<!DOCTYPE html>
<html>
<head>
    <title>{project_name}</title>
</head>
<body>
    <h1>Welcome to {project_name}</h1>
</body>
</html>
""",
                "tests/__init__.py": "",
                "tests/test_app.py": """import pytest
from src.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    rv = client.get('/')
    assert rv.status_code == 200
""",
                "requirements.txt": """flask>=2.0.0
pytest>=7.0.0
pytest-cov>=4.0.0
""",
                "README.md": """# {project_name}

{project_description}

## Setup
1. Install requirements: `pip install -r requirements.txt`
2. Run tests: `pytest`
3. Run the app: `python src/app.py`
"""
            }
        },
        "fastapi-api": {
            "name": "FastAPI REST API",
            "description": "REST API using FastAPI framework",
            "files": {
                "src/__init__.py": "",
                "src/main.py": """from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="{project_name}")

class Item(BaseModel):
    name: str
    description: str = None

@app.get("/")
async def root():
    return {"message": "Welcome to {project_name}"}

@app.get("/items")
async def get_items():
    return {"items": []}
""",
                "tests/__init__.py": "",
                "tests/test_api.py": """from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
""",
                "requirements.txt": """fastapi>=0.68.0
uvicorn>=0.15.0
pytest>=7.0.0
httpx>=0.23.0
pytest-cov>=4.0.0
""",
                "README.md": """# {project_name}

{project_description}

## Setup
1. Install requirements: `pip install -r requirements.txt`
2. Run tests: `pytest`
3. Start the API: `uvicorn src.main:app --reload`

## API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
"""
            }
        }
    }

    @classmethod
    def list_templates(cls):
        """List available templates"""
        return {
            name: {
                "name": template["name"],
                "description": template["description"]
            }
            for name, template in cls.TEMPLATES.items()
        }

    @classmethod
    def create_from_template(cls, template_name: str, project_path: Path, project_name: str, description: str):
        """Create project from template"""
        if template_name not in cls.TEMPLATES:
            raise ValueError(f"Template '{template_name}' not found")

        template = cls.TEMPLATES[template_name]
        
        # Create project directory
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Create files from template
        for file_path, content in template["files"].items():
            full_path = project_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Format content with project details
            formatted_content = content.format(
                project_name=project_name,
                project_description=description
            )
            
            full_path.write_text(formatted_content)