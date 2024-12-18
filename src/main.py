from typing import Union
import json
from typing import Optional
import toml
import logging
import sys
from pathlib import Path
import git
import venv
import os
import subprocess

from cst_frame_depth import analyze_package
from test_counter import count_tests_in_package
from package_complexity import get_package_complexity
from pyflake_it import flake_package
from readme_parser import parse_readme
from github_parser import GithubParser
from reviewer import Reviewer

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

class CodeBase:
    codebase: Path

    def analyze(self, github_page_url: str):
        naked = github_page_url.split("?")[0]
        github_url = f"{naked}.git"
        logger.info(f"Starting analysis for repository: {github_url}")
        self.get_from_git(github_url)
        self.find_setup_file()
        self.install_requirements()
        analysis_result = {
            "package_name": self.get_package_name(),
            "github_url": github_url,
            "github_stats": GithubParser().analyze_repo(github_url),
            "summary": parse_readme(github_url, self.codebase),
            "codebase_size": self.format_bytes(self.get_codebase_size()),
            "total_package_size": self.format_bytes(self.get_total_package_size()),
            "immediate_dependencies": len(self.get_dependencies()),
            "total_number_of_dependencies_in_deps_chain": self.get_number_of_dependencies(),
            "deepest_file_path": self.get_deepest_file_path(),
            "number_of_files": self.get_number_of_files(),
            "number_of_tests": count_tests_in_package(self.codebase)["total_tests"],
            "package_tree_analysis_excluding_test_files": analyze_package(self.codebase),
            "package_complexity": get_package_complexity(self.codebase),
            "error_analysis": flake_package(self.codebase)

        }
        logger.info("Analysis complete")
        return json.dumps(analysis_result, indent=2)

    def get_from_git(self, github_url: str):
        """clone the repository from github into the /codebase directory"""
        logger.info(f"Cloning repository from {github_url}")
        target = Path("/codebase")
        target.mkdir(exist_ok=True)
        git.Repo.clone_from(github_url, target)
        self.codebase = target
        logger.info("Repository cloned successfully")

    def find_setup_file(self) -> Optional[Path]:
        """find the toml/setup.py file in the codebase"""
        for req_file in ["pyproject.toml", "setup.py"]:
            req_file = self.codebase / req_file
            if req_file.exists():
                self.setup_file = req_file
                break
        if self.setup_file is None:
            raise FileNotFoundError("No requirements file found")

    def get_package_name(self) -> str:
        """get the package name from the setup file"""
        package_name = None
        if self.setup_file.name == "pyproject.toml":
            data = toml.load(self.setup_file)
            section = data.get("project", data.get("tool", {}).get("poetry", {"name": "name_not_found"}))
            package_name = section.get("name").lower()
        else:
            for line in self.setup_file.read_text().splitlines():
                if "name=" in line:
                    package_name = line.split("=")[1].strip().replace(",","").replace("'","").replace('"','')
                    break
        if not package_name:
            raise ValueError("unable to find package name")
        logger.info(f"Package name: {package_name}")
        return package_name

    def get_dependencies(self) -> list:
        """get the dependencies from the setup file"""
        if self.setup_file.name == "pyproject.toml":
            section = self._get_pyproject_section()
            dependencies = section.get("dependencies", None)
        else:
            for line in self.setup_file.read_text().splitlines():
                if line.startswith("install_requires"):
                    dependencies = line.split("=")[1].strip().strip("[]").split(",")
                    break
        logger.info(f"Dependencies: {dependencies}")
        return dependencies

    def _get_pyproject_section(self) -> dict:
        """find the project or poetry tool section in the pyproject.toml file"""
        data = toml.load(self.setup_file)
        return data.get("project", data.get("tool", {}).get("poetry", {}))

    def install_requirements(self, requirements: Optional[Path] = None):
        """install requirements. attempt in this order:
        - pyproject.toml
        - setup.py

        Args:
            requirements (Path): path to the requirements file to override lookup
        """
        logger.info("Installing requirements")
        requirements = requirements or self.setup_file

        venv_dir = self.codebase / "venv"
        venv.create(venv_dir, with_pip=True)
        activate_script = venv_dir / "bin" / "activate"
        if (self.codebase / "poetry.lock").exists():
            logger.info("Using Poetry to install dependencies")
            try:
                subprocess.run(f". {activate_script} && poetry install", shell=True, check=True, cwd=self.codebase)
            except subprocess.CalledProcessError as e:
                logger.error(f"Error installing requirements with Poetry: {e.stderr}")
                raise e
        else:
            logger.info(f"Using pip to install dependencies from {requirements}")
            try:
                subprocess.run(f". {activate_script} && pip install .", shell=True, check=True, cwd=self.codebase)
            except subprocess.CalledProcessError as e:
                logger.error(f"Error installing requirements with pip: {e.stderr}")
                raise e
        logger.info("Requirements installed successfully")

    def get_codebase_size(self) -> int:
        """compute the disk size of the codebase"""
        size = self.get_size(self.codebase)
        logger.info(f"Codebase size: {size} bytes")
        return size

    def get_total_package_size(self) -> int:
        """compute the disk size of the codebase, plus all the dependencies installed in the venv directory"""
        venv_size = self.get_size(self.codebase / "venv")
        total_size = self.get_codebase_size() + venv_size
        logger.info(f"Total package size: {total_size} bytes")
        return total_size

    def get_number_of_dependencies(self) -> Union[int,str]:
        """count the number of dependencies installed in the venv directory"""
        site_packages = None
        for maybe_dir in (self.codebase / "venv" / "lib").glob("*"):
            if maybe_dir.is_dir() and maybe_dir.name.startswith("python"):
                site_packages = maybe_dir / "site-packages"
        if not site_packages:
            logger.error("cannot find site-packages directory")
            return "n/a"
        num_dependencies = len([f for f in site_packages.glob("*") if f.is_dir()])
        logger.info(f"Number of dependencies: {num_dependencies}")
        return num_dependencies

    def get_deepest_file_path(self) -> int:
        """returns the number of directories in the deepest file path in the codebase"""
        deepest_path = max([len(p.parts) for p in self.codebase.rglob("*") if p.is_file()])
        logger.info(f"Deepest file path depth: {deepest_path}")
        return deepest_path

    def get_number_of_files(self) -> int:
        """returns the number of files in the codebase"""
        num_files = len([p for p in self.codebase.rglob("*") if p.is_file()])
        logger.info(f"Number of files: {num_files}")
        return num_files

    @classmethod
    def get_size(cls, path: Path) -> int:
        total_size = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size


    @classmethod
    def format_bytes(cls, num) -> str:
        step = 1024.0
        for x in ['b', 'K', 'M', 'G', 'T']:
            if num < step:
                return "%3.1f %s" % (num, x)
            num /= step

if __name__ == "__main__":
    c = CodeBase()
    try:
        url = sys.argv[1]
    except IndexError:
        raise ValueError("Please provide a github url")
    save_path = Path("analyses")
    save_path.mkdir(exist_ok=True)
    analysis = c.analyze(url)
    safe_name = c.get_package_name().replace("/","_").replace(":","_").replace(".","_")
    file_path = save_path / f"{safe_name}.json"
    file_path.write_text(analysis)
    print("Analysis complete. Results saved to", save_path)
    print("writing reviews...")
    Reviewer().review(safe_name)