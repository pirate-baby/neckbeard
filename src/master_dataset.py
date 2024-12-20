import json
import datetime
from pathlib import Path
import humanize


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
        self.presentation = {}

    def stars(self):
        stars = dict(
        bloat = 0,
        dependency_chain = 0,
        dryness = 0,
        depth = 0,
        complexity = 0
        )
        match (self.record["raw_total_package_size"] * 1024 * 1024):
            case x if x <= 50:
                stars["bloat"] = 5
            case x if x <= 250:
                stars["bloat"] = 4
            case x if x <= 500:
                stars["bloat"] = 3
            case x if x <= 1024:
                stars["bloat"] = 2
            case x if x <= 2048:
                stars["bloat"] = 1
            case _:
                stars["bloat"] = 0

        match (self.record["total_number_of_dependencies_in_deps_chain"]):
            case x if x <= 25:
                stars["dependency_chain"] = 5
            case x if x <= 30:
                stars["dependency_chain"] = 4
            case x if x <= 40:
                stars["dependency_chain"] = 3
            case x if x <= 100:
                stars["dependency_chain"] = 2
            case x if x <= 200:
                stars["dependency_chain"] = 1
            case _:
                stars["dependency_chain"] = 0

        match self.record["dryness"]["dryness_score"]:
            case x if x >= 3:
                stars["dryness"] = 5
            case x if x >= 2.5:
                stars["dryness"] = 4
            case x if x >= 2:
                stars["dryness"] = 3
            case x if x >= 1.5:
                stars["dryness"] = 2
            case x if x >= 1:
                stars["dryness"] = 1
            case _:
                stars["dryness"] = 0
        match self.record["package_tree_analysis"]["nested_score"]:
            case x if x <= 15:
                stars["depth"] = 5
            case x if x <= 17:
                stars["depth"] = 4
            case x if x <= 18:
                stars["depth"] = 3
            case x if x <= 19:
                stars["depth"] = 2
            case x if x <= 20:
                stars["depth"] = 1
            case _:
                stars["depth"] = 0
        match self.record["package_complexity"]["complexity_score"]:
            case x if x <= 15:
                stars["complexity"] = 5
            case x if x <= 17:
                stars["complexity"] = 4
            case x if x <= 18:
                stars["complexity"] = 3
            case x if x <= 19:
                stars["complexity"] = 2
            case x if x <= 20:
                stars["complexity"] = 1
            case _:
                stars["complexity"] = 0

        self.presentation["stars"] = stars

    def pretty_dates(self):
        today = datetime.datetime.now()
        self.presentation["reviewed_on"] = today.strftime("%b %d, %Y")
        newest = self.record["analysis"]["github_stats"]["newest_commit"]
        oldest = self.record["analysis"]["github_stats"]["oldest_commit"]

        def human(datevalue):
            return humanize.naturaltime(today - datevalue)

        def more_pretty(datevalue):
            if today - datevalue < datetime.timedelta(days=1):
                return datevalue.strftime("%H:%M %p")
            else:
                return datevalue.strftime("%b %d, %Y")

        self.presentation["newest_commit"] = f"{human(newest)} ago ({more_pretty(newest)})"
        self.presentation["oldest_commit"] = f"{human(oldest)} ago ({more_pretty(oldest)})"