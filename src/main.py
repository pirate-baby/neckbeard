from typing import Optional
from pathlib import Path
import git
import venv
import os

class CodeBase:
    codebase: Path

    def get_from_git(self, github_url: str):
        """clone the repository from github into the /codebase directory"""
        target = Path("/codebase")
        target.mkdir(exist_ok=True)
        git.Repo.clone_from(github_url, target)
        self.codebase = target

    def install_requirements(self, requirements: Optional[Path]=None):
        """install requirements. attempt in this order:
        - pyproject.toml
        - setup.py

        Args:
            requirements (Path): path to the requirements file to override lookup
        """
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
        if (self.codebase / "poetry.lock").exists():
            venv.run(venv_dir, "poetry install")
        else:
            venv.run(venv_dir, f"pip install -r {requirements}")

    def get_codebase_size(self) -> int:
        """compute the disk size of the codebase"""
        return self.get_size(self.codebase)


    def get_total_package_size(self) -> int:
        """compute the disk size of the codebase, plus all the dependencies installed in the venv directory"""
        venv_size = self.get_size(self.codebase / "venv")
        return self.get_codebase_size + venv_size

    def get_number_of_dependencies(self) -> int:
        """count the number of dependencies installed in the venv directory"""
        # note: 3.8 at the moment to stay easy to meet
        return len([f for f in (self.codebase / "venv" / "lib" / "python3.8" / "site-packages").glob("*") if f.is_dir()])


    @classmethod
    def get_size(cls, path: Path) -> int:
        total_size = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size