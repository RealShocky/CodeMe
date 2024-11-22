import pytest
import asyncio
from pathlib import Path
import logging
from typing import Dict, Any, List
import json
import coverage
import ast

class TestManager:
    def __init__(self, project_manager):
        self.project_manager = project_manager
        self.logger = logging.getLogger(__name__)
        self.cov = coverage.Coverage()

    async def execute_action(self, action_plan: Dict[str, Any]):
        """Execute a test-related action plan"""
        try:
            current_project = self.project_manager.get_current_project()
            if not current_project:
                raise ValueError("No project currently loaded")

            for step in action_plan["steps"]:
                if step["type"] == "generate_tests":
                    await self.generate_tests(step["params"])
                elif step["type"] == "run_tests":
                    await self.run_tests(step["params"])
                elif step["type"] == "analyze_coverage":
                    await self.analyze_coverage()
        
        except Exception as e:
            self.logger.error(f"Error executing test action: {e}")
            raise

    def _generate_test_content(self, source_path: Path) -> str:
        """Generate test content based on source file"""
        try:
            # Read source file
            source_content = source_path.read_text()
            tree = ast.parse(source_content)
            
            # Extract classes and functions
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            
            # Generate test file content
            content = [
                "import pytest",
                f"from {source_path.stem} import *",
                "",
                "# Generated Tests"
            ]
            
            # Generate class tests
            for cls in classes:
                content.extend([
                    f"\nclass Test_{cls.name}:",
                    f"    def test_{cls.name}_initialization(self):",
                    f"        # Test {cls.name} initialization",
                    f"        instance = {cls.name}()",
                    "        assert instance is not None"
                ])
            
            # Generate function tests
            for func in functions:
                content.extend([
                    f"\ndef test_{func.name}():",
                    f"    # Test {func.name} function",
                    "    assert True  # Replace with actual test"
                ])
            
            return "\n".join(content)
            
        except Exception as e:
            self.logger.error(f"Error generating test content: {e}")
            raise

    async def generate_tests(self, params: Dict[str, Any]):
        """Generate test files for source files"""
        try:
            source_file = params.get("source_file")
            if not source_file:
                raise ValueError("No source file specified")

            current_project = self.project_manager.get_current_project()
            source_path = current_project / "src" / source_file
            test_path = current_project / "tests" / f"test_{source_file}"

            # Create test file content
            test_content = self._generate_test_content(source_path)
            
            # Write test file
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text(test_content)
            print(f"\n✅ Generated test file: {test_path}")

        except Exception as e:
            self.logger.error(f"Error generating tests: {e}")
            raise

    async def run_tests(self, params: Dict[str, Any] = None):
        """Run pytest for the project"""
        try:
            current_project = self.project_manager.get_current_project()
            if not current_project:
                raise ValueError("No project currently loaded")

            test_path = current_project / "tests"
            if not test_path.exists():
                raise ValueError("No tests directory found")

            # Start coverage
            self.cov.start()

            # Run tests
            pytest_args = [
                str(test_path),
                "-v",
                "--tb=short",
                "-p", "no:warnings"
            ]

            if params and params.get("pattern"):
                pytest_args.append("-k")
                pytest_args.append(params["pattern"])

            print("\n🧪 Running tests...")
            result = pytest.main(pytest_args)

            # Stop coverage
            self.cov.stop()
            self.cov.save()

            if result == 0:
                print("\n✅ All tests passed!")
            else:
                print("\n❌ Some tests failed")

            # Show coverage report
            await self.analyze_coverage()

        except Exception as e:
            self.logger.error(f"Error running tests: {e}")
            raise

    async def analyze_coverage(self) -> Dict[str, Any]:
        """Analyze test coverage"""
        try:
            print("\n📊 Analyzing test coverage...")
            self.cov.load()
            
            # Generate report
            total_coverage = self.cov.report()
            
            # Generate HTML report
            current_project = self.project_manager.get_current_project()
            html_dir = current_project / "htmlcov"
            self.cov.html_report(directory=str(html_dir))
            
            report = {
                "total_coverage": total_coverage,
                "report_path": str(html_dir / "index.html")
            }
            
            print(f"\n📈 Total coverage: {total_coverage:.1f}%")
            print(f"📑 Detailed report: {report['report_path']}")
            
            return report

        except Exception as e:
            self.logger.error(f"Error analyzing coverage: {e}")
            raise

    async def discover_tests(self) -> List[Path]:
        """Discover all test files in the project"""
        try:
            current_project = self.project_manager.get_current_project()
            if not current_project:
                raise ValueError("No project currently loaded")

            test_path = current_project / "tests"
            if not test_path.exists():
                return []

            test_files = list(test_path.glob("test_*.py"))
            print("\n🔍 Found test files:")
            for test_file in test_files:
                print(f"  - {test_file.relative_to(current_project)}")

            return test_files

        except Exception as e:
            self.logger.error(f"Error discovering tests: {e}")
            raise