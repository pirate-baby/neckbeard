from pathlib import Path
import json
import subprocess

class Security:

    def __init__(self):
        pass

    def check_security_risks(self, paths: list[Path]):
        """
        Check the security of a module by running bandit on it.
        """

    def get_security_risk_codes(self, paths: list[Path]) -> dict:
        risks = []
        for filename in paths:
            result = subprocess.run(["bandit", "-r", "-lll", "-q", "-f", "json", str(filename.absolute())], cwd="/codebase", capture_output=True, text=True)
            try:
                decoded = json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                raise ValueError(f"Bandit output is not valid JSON: {result.stdout} {result.stderr}")
                continue
            risks.extend(decoded["results"])

        consolidated_risks = {}
        for risk in risks:
            text = risk["issue_text"]
            consolidated_risks[text] = consolidated_risks.get(text, 0) + 1
        return consolidated_risks