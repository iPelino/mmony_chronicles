import xml.etree.ElementTree as ET
import re
import pandas as pd
import sqlite3

# Load and parse the XML file
def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    return root.findall("sms")

# Extract and categorize SMS messages
def extract_transaction_data(sms_elements):
    data = []
    failed_sms = []
    
    for sms in sms_elements:
        body = sms.attrib.get("body", "")
        
        # 1. System Notifications
        if body.startswith("*143*R*"):
            if "successfully registered" in body:
                continue  # Skip registration messages
            if "failed" in body:
                continue  # Skip failure messages for now
        
        # 2. Incoming Money
        elif body.startswith("You have received"):
            match = re.search(r"received (\d+) RWF from (.+?) \(", body)
            date_time_match = re.search(r"at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", body)
            txn_id_match = re.search(r"Financial Transaction Id: (\d+)", body)
            
            if match and date_time_match and txn_id_match:
                amount = int(match.group(1))
                sender = match.group(2)
                date_time = date_time_match.group(1)
                txn_id = txn_id_match.group(1)
                
                data.append({
                    "Type": "Incoming Money",
                    "Amount": amount,
                    "Sender": sender,
                    "DateTime": date_time,
                    "TransactionID": txn_id
                })
        
        # 3. Payments to Code Holders
        elif body.startswith("TxId"):

           # Generalized matching logic for flexibility
            txn_id_match = re.search(r"TxId: (\d+)", body)
            amount_match = re.search(r"payment\s+of\s+([\d,]+)\s+RWF", body)  # Adjusted regex
            recipient_match = re.search(r"to (.+?) (\d+)", body)
            date_time_match = re.search(r"at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", body)

            # Extract matched components
            txn_id = txn_id_match.group(1) if txn_id_match else None
            amount = int(amount_match.group(1).replace(",", "")) if amount_match else None  # Remove commas from amount
            recipient = recipient_match.group(1).strip() if recipient_match else None
            recipient_code = recipient_match.group(2) if recipient_match else None
            date_time = date_time_match.group(1) if date_time_match else None

            if txn_id and amount and recipient and date_time:
                data.append({
                    "Type": "Payment to Code Holder",
                    "TransactionID": txn_id,
                    "Amount": amount,
                    "Recipient": recipient,
                    "RecipientCode": recipient_code,
                    "DateTime": date_time
                })
            else:
                failed_sms.append(body)
                
        # 4. Transfers to Mobile Numbers
        elif body.startswith("*165*S*"):
            match = re.search(r"(\d+) RWF transferred to (.+?) \((250\d+)\)", body)
            date_time_match = re.search(r"at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", body)
            fee_match = re.search(r"Fee was: (\d+) RWF", body)
            
            if match and date_time_match and fee_match:
                amount = int(match.group(1))
                recipient = match.group(2)
                recipient_number = match.group(3)
                date_time = date_time_match.group(1)
                fee = int(fee_match.group(1))
                
                data.append({
                    "Type": "Transfer to Mobile Number",
                    "Amount": amount,
                    "Recipient": recipient,
                    "RecipientNumber": recipient_number,
                    "DateTime": date_time,
                    "Fee": fee
                })
        
        # 5. Bank Deposits
        elif body.startswith("*113*R*"):
            match = re.search(r"deposit of (\d+) RWF", body)
            date_time_match = re.search(r"at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", body)
            
            if match and date_time_match:
                amount = int(match.group(1))
                date_time = date_time_match.group(1)
                
                data.append({
                    "Type": "Bank Deposit",
                    "Amount": amount,
                    "DateTime": date_time
                })
    print(f"Processed {len(data)} SMS messages.")
    print(f"Failed to process {len(failed_sms)} SMS messages.")
    return data

def verify_processed_transactions(file_path):
    sms_elements = parse_xml(file_path)
    total_sms = len(sms_elements)
    
    # Track counts
    processed_count = {
        "Incoming Money": 0,
        "Payment to Code Holder": 0,
        "Transfer to Mobile Number": 0,
        "Bank Deposit": 0,
        "Ignored": 0,
    }

    for sms in sms_elements:
        body = sms.attrib.get("body", "")
        
        # Categorize and count transactions
        if body.startswith("*143*R*"):
            processed_count["Ignored"] += 1
        elif body.startswith("You have received"):
            processed_count["Incoming Money"] += 1
        elif body.startswith("TxId"):
            processed_count["Payment to Code Holder"] += 1
        elif body.startswith("*165*S*"):
            processed_count["Transfer to Mobile Number"] += 1
        elif body.startswith("*113*R*"):
            processed_count["Bank Deposit"] += 1
        else:
            processed_count["Ignored"] += 1  # Messages not fitting known patterns

    processed_total = sum(v for k, v in processed_count.items() if k != "Ignored")
    print(f"Total SMS: {total_sms}")
    print(f"Processed Transactions: {processed_total}")
    print(f"Processed Breakdown: {processed_count}")
    print(f"Discrepancy: {total_sms - processed_total - processed_count['Ignored']} (unprocessed messages)")

    return processed_count, total_sms, processed_total


def write_to_csv(df, output_file):
    df.to_csv(output_file, index=False)

# def write_to_json(df, output_file):
#     df.to_json(output_file, orient="records")

def push_to_sqlite_by_type(df, db_path="db/transactions_by_type.db"):
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Define table creation queries for each transaction type
    table_definitions = {
        "incoming_money": """
        CREATE TABLE IF NOT EXISTS incoming_money (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            sender TEXT,
            date_time TEXT,
            transaction_id TEXT
        )
        """,
        "payment_to_code_holder": """
        CREATE TABLE IF NOT EXISTS payment_to_code_holder (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT,
            amount REAL,
            recipient TEXT,
            date_time TEXT
        )
        """,
        "transfer_to_mobile": """
        CREATE TABLE IF NOT EXISTS transfer_to_mobile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            recipient TEXT,
            recipient_number TEXT,
            date_time TEXT,
            fee REAL
        )
        """,
        "bank_deposits": """
        CREATE TABLE IF NOT EXISTS bank_deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            date_time TEXT
        )
        """
    }

    # Create tables
    for table, query in table_definitions.items():
        cursor.execute(query)
    
    # Insert data into respective tables based on `Type`
    for _, row in df.iterrows():
        if row["Type"] == "Incoming Money":
            cursor.execute("""
            INSERT INTO incoming_money (amount, sender, date_time, transaction_id)
            VALUES (?, ?, ?, ?)
            """, (row["Amount"], row.get("Sender"), row["DateTime"], row.get("TransactionID")))
        
        elif row["Type"] == "Payment to Code Holder":
            cursor.execute("""
            INSERT INTO payment_to_code_holder (transaction_id, amount, recipient, date_time)
            VALUES (?, ?, ?, ?)
            """, (row.get("TransactionID"), row["Amount"], row.get("Recipient"), row["DateTime"]))
        
        elif row["Type"] == "Transfer to Mobile Number":
            cursor.execute("""
            INSERT INTO transfer_to_mobile (amount, recipient, recipient_number, date_time, fee)
            VALUES (?, ?, ?, ?, ?)
            """, (row["Amount"], row["Recipient"], row["RecipientNumber"], row["DateTime"], row.get("Fee")))
        
        elif row["Type"] == "Bank Deposit":
            cursor.execute("""
            INSERT INTO bank_deposits (amount, date_time)
            VALUES (?, ?)
            """, (row["Amount"], row["DateTime"]))
    
    # Commit and close connection
    conn.commit()
    conn.close()
    print(f"Data successfully pushed to {db_path}")

# def extract_payment_to_code_holder_sms(file_path, output_file="payment_to_code_holder_sms.log"):
#     sms_elements = parse_xml(file_path)
#     txid_sms = []

#     for sms in sms_elements:
#         body = sms.attrib.get("body", "")
#         if body.startswith("TxId"):
#             txid_sms.append(body)

#     with open(output_file, "w") as f:
#         for message in txid_sms:
#             f.write(f"{message}\n")

#     print(f"Extracted {len(txid_sms)} 'Payment to Code Holder' SMS messages.")


def log_unprocessed_messages(file_path, output_file="unprocessed_sms.log"):
    sms_elements = parse_xml(file_path)
    unprocessed = []

    for sms in sms_elements:
        body = sms.attrib.get("body", "")
        if not (
            body.startswith("*143*R*")
            or body.startswith("You have received")
            or body.startswith("TxId")
            or body.startswith("*165*S*")
            or body.startswith("*113*R*")
        ):
            unprocessed.append(body)

    with open(output_file, "w") as f:
        for message in unprocessed:
            f.write(f"{message}\n")

    print(f" {len(unprocessed)} Unprocessed messages logged to {output_file}")


# Convert data to DataFrame and display
def main(file_path):
    sms_elements = parse_xml(file_path)
    transactions = extract_transaction_data(sms_elements)
    df = pd.DataFrame(transactions)
    
    print(df)

    # output_file = "cleaned_data.csv"
    # output_file = "cleaned_data.json"
    # write_to_csv(df, output_file)
    # write_to_json(df, output_file)

    verify_processed_transactions(file_path)
    log_unprocessed_messages(file_path)
    # push_to_sqlite_by_type(df)
    return df

# Run the script with the provided file
file_path = "sms-20250116123406.xml"
df = main(file_path)
