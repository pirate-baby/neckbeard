import json
from pathlib import Path


class MasterDataset:

    def __init__(self):
        self.reviews = Path("/app/reviews")
        self.analyses = Path("/app/analyses")

    def merge_record(self, record_name: str) -> dict:
        """
        merge parts into a single record
        """
        analysis = self.analyses / f"{record_name}.json"
        review_data = self.reviews / record_name / "review.json"
        review_md = self.reviews / record_name / "review.md"

        record = {}
        record["analysis"] = json.loads(analysis.read_text())
        record["review_data"] = json.loads(review_data.read_text())

        body = []
        for line in review_md.read_text().split("\n"):
            if line.startswith("# "):
                record["review_title"] = line[2:].strip()
            else:
                body.append(line)
        record["review_body"] = "\n".join(body)
        return record

    def generate(self) -> None:
        records = []
        for file in self.analyses.glob("*"):
            if file.is_file():
                record_name = file.name.replace(".json", "")
                records.append(self.merge_record(record_name))
        master_dataset = Path("/app/master_dataset.json")
        master_dataset.write_text(json.dumps(records, indent=2))