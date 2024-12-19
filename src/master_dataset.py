import json
import datetime
from pathlib import Path
#import humanize


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

class Snarkizer:

    def __init__(self, record_name: str):
        self.record = json.loads(Path(f"/app/analyses/{record_name}.json").read_text())


    def pretty_dates(self):
        today = datetime.datetime.now()
        newest = self.record["analysis"]["newest_commit"]
        oldest = self.record["analysis"]["oldest_commit"]

        def human(datevalue):
            return humanize.naturaltime(today - datevalue)

        def more_pretty(datevalue):
            if today - datevalue < datetime.timedelta(days=1):
                return datevalue.strftime("%H:%M %p")
            else:
                return datevalue.strftime("%b %d, %Y")

        self.record["analysis"]["newest_commit"] = f"{human(newest)} ago ({more_pretty(newest)})"
        self.record["analysis"]["oldest_commit"] = f"{human(oldest)} ago ({more_pretty(oldest)})"