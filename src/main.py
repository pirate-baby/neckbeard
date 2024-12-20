from typing import Union, Generator
from datetime import datetime
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
from master_dataset import MasterDataset
from moisture_meter import check_dryness
from security import Security

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

class CodeBase:
    codebase: Path
    setup_file: Path
    is_a_package: bool
    is_installed: bool

    def analyze(self, github_page_url: str):
        naked = github_page_url.split("?")[0]
        self.github_url = f"{naked}.git"
        self.setup_file = None
        logger.info(f"Starting analysis for repository: {self.github_url}")
        self.get_from_git()
        self.find_setup_file()
        self.install_requirements()
        package_tree_analysis = analyze_package(self.codebase)
        test_count = count_tests_in_package(self.codebase)["total_tests"]
        analysis_result = {
            "project_name": self.get_package_name(),
            "analyzed_at": datetime.now().isoformat(),
            "is_a_package": self.is_a_package,
            "self.github_url": self.github_url,
            "github_stats": GithubParser().analyze_repo(self.github_url),
            "summary": parse_readme(self.github_url, self.codebase),
            "raw_codebase_size": self.get_codebase_size(),
            "raw_total_package_size": self.get_total_package_size(),
            "codebase_size": self.format_bytes(self.get_codebase_size()),
            "total_package_size": self.format_bytes(self.get_total_package_size()),
            "immediate_dependencies": len(self.get_dependencies()),
            "total_number_of_dependencies_in_deps_chain": self.get_number_of_dependencies(),
            "deepest_file_path": self.get_deepest_file_path(),
            "number_of_modules": self.get_number_of_files(filter_by=".py"),
            "number_of_files": self.get_number_of_files(),
            "number_of_tests": test_count,
            "naive_test_coverage_ratio": round(test_count / package_tree_analysis["count_of_functions"], 2),
            "dryness": check_dryness(self.filtered_codebase),
            "package_tree_analysis": package_tree_analysis,
            "package_complexity": get_package_complexity(self.codebase),
            "error_analysis": flake_package(self.codebase),
            "security_risks": [f"{v} instances of {k}" for k, v in Security().get_security_risk_codes(self.filtered_codebase).items()]

        }
        logger.info("Analysis complete")
        return json.dumps(analysis_result, indent=2)

    def get_from_git(self):
        """clone the repository from github into the /codebase directory"""
        logger.info(f"Cloning repository from {self.github_url}")
        target = Path("/codebase")
        target.mkdir(exist_ok=True)
        git.Repo.clone_from(self.github_url, target)
        self.codebase = target
        logger.info("Repository cloned successfully")

    def find_setup_file(self) -> None:
        """find the toml/setup.py file in the codebase"""
        self.is_a_package = False
        for req_file in ["pyproject.toml", "setup.py"]:
            req_file = self.codebase / req_file
            if req_file.exists():
                self.setup_file = req_file
                self.is_a_package = True
                return
        if (self.codebase / "requirements.txt").exists():
            self.is_a_package = False


    def get_package_name(self) -> str:
        """get the package name from the setup file"""
        if not self.is_a_package:
            return self.github_url.split("/")[-1].strip(".git")
        if self.setup_file.name == "pyproject.toml":
            data = toml.load(self.setup_file)
            section = data.get("project", data.get("tool", {}).get("poetry", {"name": "name_not_found"}))
            return section.get("name").lower()
        elif self.setup_file.name == "setup.py":
            for line in self.setup_file.read_text().splitlines():
                if "name=" in line:
                    return line.split("=")[1].strip().replace(",","").replace("'","").replace('"','')
        else:
            raise ValueError("Unsupported package manager")

    def get_dependencies(self) -> list:
        """get the dependencies from the setup file"""
        if not self.is_a_package:
            requirements = self.codebase / "requirements.txt"
            if requirements.exists():
                return requirements.read_text().split("\n")
            return []
        if self.setup_file.name == "pyproject.toml":
            section = self._get_pyproject_section()
            return section.get("dependencies", None)
        else:
            install_requires = []
            in_install_requires = False
            for line in self.setup_file.read_text().splitlines():
                if "install_requires" in line:
                    in_install_requires = True
                    install_requires.extend(line.split("=")[1].strip().strip("[]").split(","))
                elif in_install_requires:
                    if "]" in line:
                        install_requires.extend(line.strip().strip("[]").split(","))
                        break
                    install_requires.append(line.strip().strip(","))
            return install_requires

    def _get_pyproject_section(self) -> dict:
        """find the project or poetry tool section in the pyproject.toml file"""
        data = toml.load(self.setup_file)
        return data.get("project", data.get("tool", {}).get("poetry", {}))

    def install_requirements(self, requirements: Optional[str] = None):
        """install requirements. attempt in this order:
        - pyproject.toml
        - setup.py

        Args:
            requirements (Path): path to the requirements file to override lookup
        """
        logger.info("Installing requirements")
        requirements = requirements or self.setup_file or "requirements.txt"

        venv_dir = self.codebase / "venv"
        venv.create(venv_dir, with_pip=True)
        activate_script = venv_dir / "bin" / "activate"
        if (self.codebase / "poetry.lock").exists():
            logger.info("Using Poetry to install dependencies")
            try:
                subprocess.run(f". {activate_script} && poetry install", shell=True, check=True, cwd=self.codebase)
                logger.info("Requirements installed successfully")
                self.installed = True
                return
            except subprocess.CalledProcessError as e:
                logger.error(f"Error installing requirements with Poetry: {e.stderr}")
                self.installed = False
        elif self.is_a_package:
            logger.info(f"Using pip to install dependencies from {requirements}")
            try:
                subprocess.run(f". {activate_script} && pip install .", shell=True, check=True, cwd=self.codebase)
                logger.info("Requirements installed successfully")
                self.installed = True
                return
            except subprocess.CalledProcessError as e:
                logger.error(f"Error installing requirements with pip: {e.stderr}")
                self.installed = False
        else:
            logger.info(f"not a package, attempting to install dependencies from {requirements}")
            try:
                subprocess.run(f". {activate_script} && pip install -r {requirements}", shell=True, check=True, cwd=self.codebase)
                logger.info("Requirements installed successfully")
                self.installed = True
                return
            except subprocess.CalledProcessError as e:
                logger.error(f"Error installing requirements: {e.stderr}")
                self.installed = False

    def get_codebase_size(self) -> int:
        """compute the disk size of the codebase"""
        size = 0
        for dir in self.filtered_codebase:
            size += self.get_size(dir)
        logger.info(f"Codebase size: {size} bytes")
        return size

    def get_total_package_size(self) -> Union[int,str]:
        """compute the disk size of the codebase, plus all the dependencies installed in the venv directory"""
        if not self.installed:
            return "n/a unable to install"
        venv_size = self.get_size(self.codebase / "venv")
        total_size = self.get_codebase_size() + venv_size
        logger.info(f"Total package size: {total_size} bytes")
        return total_size

    def get_number_of_dependencies(self) -> Union[int,str]:
        """count the number of dependencies installed in the venv directory"""
        if not self.installed:
            return "n/a unable to install"
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
        """returns the number of directories in the deepest file path to .py code in the codebase"""
        deepest_path = max([len(p.parts) for p in self.filtered_codebase if p.is_file() and p.suffix == ".py"])
        logger.info(f"Deepest file path depth: {deepest_path}")
        return deepest_path

    def get_number_of_files(self, filter_by:Optional[str]=None) -> int:
        """returns the number of files in the codebase"""
        files = [p for p in self.filtered_codebase if p.is_file()]
        if filter_by:
            files = [f for f in files if f.suffix == filter_by]
        num_files = len(files)
        logger.info(f"Number of files: {num_files}")
        return num_files

    @property
    def filtered_codebase(self) -> Generator:
        """remove venv files from codebase counts"""
        for p in self.codebase.rglob("*"):
            if "venv" not in p.parts:
                yield p

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
        num = int(num)
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
    #print("writing reviews...")
    #Reviewer().review(safe_name)

    #print("re-building master dataset...")
    #MasterDataset().generate()