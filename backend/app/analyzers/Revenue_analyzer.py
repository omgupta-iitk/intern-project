import uuid
from io import BytesIO

import matplotlib.pyplot as plt
import pandas as pd
from app.util import upload_to_supabase_storage


class RevenueAnalysis:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        df["Total Revenue"] = df["Total Revenue"].str.replace(r"[^\d.]", "", regex=True)
        df["Total Revenue"] = pd.to_numeric(df["Total Revenue"], errors="coerce")

    def daily_revenue_trend(self):
        plt.figure()
        plt.plot(self.df["Date"], self.df["Total Revenue"])
        plt.title("Revenue Trend")
        plt.xlabel("Date")
        plt.ylabel("Revenue ($)")
        # Rotate x-axis labels to 90 degrees (vertical)
        plt.xticks(rotation=90)
        plt.tight_layout()
        plt.grid(True)
        image_bytes = BytesIO()
        plt.savefig(image_bytes, format="png")
        plt.close()
        image_bytes.seek(0)
        image_url = upload_to_supabase_storage(
            image_bytes.read(), f"daily_trend_{uuid.uuid4()}.png"
        )
        return image_url

    def weekly_avg_revenue(self):
        weekly_avg = self.df.groupby("Day of Week")["Total Revenue"].mean().to_dict()
        return weekly_avg

    def top_days(self):
        top = self.df.sort_values("Total Revenue", ascending=False).head(3)
        return top[["Date", "Total Revenue"]].to_dict(orient="records")

    def average_spend_per_transaction(self):
        self.df["Avg Spend per Transaction"] = (
            self.df["Total Revenue"] / self.df["Transaction Count"]
        )
        return self.df["Avg Spend per Transaction"].mean()

    def analyze(self):
        return {
            "trends": {
                "daily_revenue_trend_image": self.daily_revenue_trend(),
                "weekly_average_revenue": self.weekly_avg_revenue(),
                "top_revenue_days": self.top_days(),
            },
            "engagement_metrics": {
                "average_spend_per_transaction": self.average_spend_per_transaction()
            },
        }

    def generate_recommendations(self, analyzed_data):
        recs = []
        top_days = analyzed_data["trends"]["top_revenue_days"]
        weak_days = analyzed_data["trends"]["weekly_average_revenue"]
        if weak_days:
            weak_day = min(weak_days, key=weak_days.get)
            recs.append(
                f"Consider offering discounts or promotions on {weak_day}s to increase traffic."
            )
        if top_days:
            recs.append(
                f"Optimize staffing on peak days like {top_days[0]['Date']} due to high revenue."
            )
        return recs
