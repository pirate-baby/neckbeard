from openai import OpenAI
from pathlib import Path

class Readme:
    """digest a package's readme file"""


    def read_readme(self, package_path: Path) -> str:
        readme_content = ""
        for file_path in package_path.rglob("README*"):
            readme_content += file_path.read_text()
        if not readme_content:
            raise FileNotFoundError("No README file found")
        return readme_content

    def generate_summary(self,
                         github_url: str,
                         readme_content: str):
        prompts = [
            {"role": "system", "content": ("Your job is to describe Python software projects in a few sentences. Users will supply you with the Github URL and the project's README file. Respond to the user with a consise summary of the project, no more than three sentences."),
            },
            {
            "role": "user",
            "content": f"this is the project readme for {github_url}:\n\n  {readme_content}"
            }
        ]
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=prompts
        )
        return response.choices[0].message.content

def parse_readme(github_url:str, project_path:Path) -> str:
    readme = Readme()
    readme_content = readme.read_readme(project_path)
    return readme.generate_summary(github_url, readme_content)
