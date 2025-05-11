from collections import Counter
import json
import pandas as pd

class BillsAnalysis:
    def __init__(self, bills_json):
        self.df = pd.DataFrame(bills_json)

    def average_spend_per_guest(self):
        self.df["Spend per Guest"] = self.df["Total"] / self.df["Guests"]
        return self.df["Spend per Guest"].mean()

    def popular_items(self):
        counter = Counter()
        for items in self.df["Items"]:
            try:
                parsed_items = json.loads(items)
                for item, qty in parsed_items:
                    counter[item] += qty
            except Exception:
                continue
        return counter.most_common(5)
    def analyze(self):
        return {
            "engagement_metrics": {
                "average_spend_per_guest": self.average_spend_per_guest(),
                "popular_items": self.popular_items()
            }
        }
    
