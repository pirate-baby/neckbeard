from typing import Literal
from pathlib import Path
from openai import OpenAI

class Reviewer:
    """uses the analysis to generate a huan-readable review"""
    reviews: Path
    analyses: Path


    def __init__(self):
        self.client = OpenAI()
        self.reviews = Path("/app/reviews")
        self.analyses = Path("/app/analyses")


    def generate_review_part(self, subject: str, output: Literal["json", "md"] = "md"):
        """generate a review based on the analysis"""
        analysis = self.analyses / f"{subject}.json"
        if not analysis.exists():
            raise FileNotFoundError("Analysis not found")
        analysis = analysis.read_text()

        example_reviews = ("django", "langchain-monorepo", "promptic",)
        example_prompt = ""
        for example in example_reviews:
            review = self.reviews / example / "review.md" if output == "md" else self.reviews / example / "review.json"
            example_prompt += f"\nReview of {example}:\n"
            example_prompt += f"ANALYSIS:\n```json\n{(self.analyses / (example + '.json')).read_text()}\n```\n"
            example_prompt += f"REVIEW:\n```{output}\n{review.read_text()}\n```\n"

        prompts = [
            {"role": "system",
             "content": ("You are a professional software critic. Using analysis data and your knowledge of software design, write a review of the software package.\n"
                         f"{'respond only with valid JSON' if output=='json' else ''}\n"
                         "Here are examples of your past reviews:")  + "\n" + example_prompt},
            {"role": "user",
             "content": f"Review of {subject}:\nANALYSIS:\n```json\n{analysis}\n```\n"}
        ]
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=prompts
        )
        response_raw = response.choices[0].message.content
        if output == "md":
            return response_raw.split("```")[1].strip("md\n")
        return response_raw

    def review(self, subject: str)->None:
        """generate a review and save it"""
        save_path = self.reviews / subject
        save_path.mkdir(exist_ok=True)
        for type in ("json", "md"):
            review = self.generate_review_part(subject, type)
            review_path = save_path / f"review.{type}"
            review_path.write_text(review)