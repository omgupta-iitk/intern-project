import pandas as pd


class BillsAnalysis:
    def __init__(self, bill_list):
        extracted_values = {
            "Total": [data["key_values"]["TOTAL"] for data in bill_list],
            "Guests": [data["key_values"]["GUESTS"] for data in bill_list],
        }

        self.df = pd.DataFrame(extracted_values)

        # Convert columns to appropriate types
        self.df["Total"] = (
            self.df["Total"].str.replace(r"[^\d.]", "", regex=True).astype(float)
        )
        self.df["Guests"] = (
            self.df["Guests"].str.replace(r"[^\d.]", "", regex=True).astype(int)
        )

    def average_spend_per_guest(self):
        # Calculate spend per guest for each bill
        self.df["Spend per Guest"] = self.df["Total"] / self.df["Guests"]
        # Return the overall average
        return self.df["Spend per Guest"].mean()

    def total_revenue(self):
        return self.df["Total"].sum()

    def total_guests(self):
        return self.df["Guests"].sum()

    def analyze(self):
        # Get bill count
        bill_count = len(self.df)

        # Calculate average bill amount
        avg_bill = self.df["Total"].mean() if not self.df["Total"].empty else 0

        # Calculate average guests per bill
        avg_guests = self.df["Guests"].mean() if not self.df["Guests"].empty else 0

        return {
            "bill_metrics": {
                "total_bills": int(bill_count),  # Convert numpy.int64 to native int
                "total_revenue": float(
                    self.total_revenue()
                ),  # Convert numpy.float64 to native float
                "total_guests": int(self.total_guests()),
                "average_bill_amount": float(avg_bill),
            },
            "engagement_metrics": {
                "average_guests_per_bill": float(avg_guests),
                "average_spend_per_guest": float(self.average_spend_per_guest()),
            },
        }
