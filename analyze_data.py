import pandas as pd
import os
import json

# Load the cleaned data
def load_data(file_path):
    return pd.read_csv(file_path)

# 1. Transaction Summary
def transaction_summary(df):
    summary = df.groupby("Type")["Amount"].sum().to_dict()
    print("Transaction Summary:\n", summary)
    return summary

# 2. Top Senders and Recipients
def top_senders_recipients(df):
    top_senders = (
        df[df["Type"] == "Incoming Money"]
        .groupby("Sender")["Amount"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .to_dict()
    )
    top_recipients = (
        df[df["Type"] == "Transfer to Mobile Number"]
        .groupby("Recipient")["Amount"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .to_dict()
    )
    print("Top Senders:\n", top_senders)
    print("Top Recipients:\n", top_recipients)
    return top_senders, top_recipients

# 3. Monthly Trends
def monthly_trends(df):
    df["Month"] = pd.to_datetime(df["DateTime"]).dt.to_period("M")
    monthly_summary = df.groupby(["Month", "Type"])["Amount"].sum().unstack(fill_value=0)
    print("Monthly Trends:\n", monthly_summary)
    return monthly_summary

# 4. Transaction Frequency
def transaction_frequency(df):
    df["Date"] = pd.to_datetime(df["DateTime"]).dt.date
    frequency = df["Date"].value_counts().sort_index()
    print("Transaction Frequency:\n", frequency)
    return frequency

# 5. Anomaly Detection
def anomaly_detection(df):
    threshold = df["Amount"].mean() + 3 * df["Amount"].std()
    anomalies = df[df["Amount"] > threshold]
    print("Anomalies:\n", anomalies)
    return anomalies

# 6. Transaction Costs
def transaction_costs(df):
    costs = df.groupby("Type")["Fee"].sum().to_dict()
    print("Transaction Costs:\n", costs)
    return costs

# 7. Balance Trends
def balance_trends(df):
    df["Balance"] = df["Amount"].cumsum()
    balance_trend = df[["DateTime", "Balance"]]
    print("Balance Trends:\n", balance_trend)
    return balance_trend

# Export all results
def save_results_to_csv(results, output_dir):
    for key, value in results.items():
        if isinstance(value, pd.DataFrame):
            value.to_csv(f"{output_dir}/{key}.csv")
        elif isinstance(value, dict):
            pd.DataFrame(list(value.items()), columns=["Key", "Value"]).to_csv(
                f"{output_dir}/{key}.csv", index=False
            )
        else:
            value.to_csv(f"{output_dir}/{key}.csv")
def save_results_to_json(results, output_dir):
    os.makedirs(output_dir, exist_ok=True)  # Ensure the output directory exists
    
    for key, value in results.items():
        output_file = os.path.join(output_dir, f"{key}.json")
        try:
            if isinstance(value, pd.DataFrame):
                # Flatten and save DataFrame as JSON
                value.reset_index(drop=True, inplace=True)
                value.to_json(output_file, orient="records", date_format="iso")
            elif isinstance(value, pd.Series):
                # Convert Series to DataFrame and then to JSON
                value.to_frame(name="Value").reset_index().to_json(output_file, orient="records", date_format="iso")
            elif isinstance(value, dict):
                # Save dictionary as JSON
                with open(output_file, "w") as f:
                    json.dump(value, f, indent=4)
            elif isinstance(value, tuple):
                # Handle tuple for split outputs
                for idx, sub_value in enumerate(value):
                    sub_key = f"{key}_Part{idx+1}"
                    sub_output_file = os.path.join(output_dir, f"{sub_key}.json")
                    with open(sub_output_file, "w") as f:
                        json.dump(sub_value, f, indent=4)
            else:
                raise ValueError(f"Unsupported result type for key '{key}': {type(value)}")
        except Exception as e:
            print(f"Error saving {key} to JSON: {e}")
            # Save a partial version of the data for debugging
            with open(os.path.join(output_dir, f"{key}_error.json"), "w") as f:
                json.dump({"error": str(e), "data_sample": str(value)[:500]}, f, indent=4)
# Main Function
def main():
    file_path = "cleaned_data.csv"
    output_dir = "analysis_results"
    df = load_data(file_path)
    
    results = {
        "Transaction_Summary": transaction_summary(df),
        "Top_Senders_and_Recipients": top_senders_recipients(df),
        "Monthly_Trends": monthly_trends(df),
        "Transaction_Frequency": transaction_frequency(df),
        "Anomalies": anomaly_detection(df),
        "Transaction_Costs": transaction_costs(df),
        "Balance_Trends": balance_trends(df),
    }
    
    save_results_to_json(results, output_dir)
    print("Analysis complete. Results saved.")

if __name__ == "__main__":
    main()
