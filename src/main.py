from typing import Optional
import logging
import sys
from pathlib import Path
import git
import venv
import os
import subprocess

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

class CodeBase:
    codebase: Path

    def analyze(self, github_url: str):
        logger.info(f"Starting analysis for repository: {github_url}")
        self.get_from_git(github_url)
        self.install_requirements()
        analysis_result = {
            "codebase_size": self.get_codebase_size(),
            "total_package_size": self.get_total_package_size(),
            "number_of_dependencies": self.get_number_of_dependencies(),
            "deepest_file_path": self.get_deepest_file_path(),
            "number_of_files": self.get_number_of_files()
        }
        logger.info("Analysis complete")
        return analysis_result

    def get_from_git(self, github_url: str):
        """clone the repository from github into the /codebase directory"""
        logger.info(f"Cloning repository from {github_url}")
        target = Path("/codebase")
        target.mkdir(exist_ok=True)
        git.Repo.clone_from(github_url, target)
        self.codebase = target
        logger.info("Repository cloned successfully")

    def install_requirements(self, requirements: Optional[Path] = None):
        """install requirements. attempt in this order:
        - pyproject.toml
        - setup.py

        Args:
            requirements (Path): path to the requirements file to override lookup
        """
        logger.info("Installing requirements")
        if requirements is None:
            for req_file in ["pyproject.toml", "setup.py"]:
                req_file = self.codebase / req_file
                if req_file.exists():
                    requirements = req_file
                    break
        if requirements is None:
            raise FileNotFoundError("No requirements file found")
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

    def get_number_of_dependencies(self) -> int:
        """count the number of dependencies installed in the venv directory"""
        num_dependencies = len([f for f in (self.codebase / "venv" / "lib" / "python3.8" / "site-packages").glob("*") if f.is_dir()])
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

if __name__ == "__main__":
    c = CodeBase()
    try:
        url = sys.argv[1]
    except IndexError:
        raise ValueError("Please provide a github url")
    print(c.analyze(url))