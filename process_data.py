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
        # 6. Bill Purchases (Airtime and Cash Power)
        elif body.startswith("*162*"):
            match = re.search(r"TxId:(\d+)\*S\*Your payment of (\d+) RWF to (Airtime|MTN Cash Power) with token.*?at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", body)
            fee_match = re.search(r"Fee was (\d+) RWF", body)
            
            if match and fee_match:
                txn_id = match.group(1)
                amount = int(match.group(2))
                bill_type = match.group(3)
                date_time = match.group(4)
                fee = int(fee_match.group(1))
                
                data.append({
                    "Type": f"{bill_type} Bill Payment",
                    "TransactionID": txn_id,
                    "Amount": amount,
                    "BillType": bill_type,
                    "DateTime": date_time,
                    "Fee": fee
                })

        # 7. Transactions Initiated by Another Party
        elif body.startswith("*164*S*"):
            match = re.search(r"A transaction of (\d+) RWF by (.*?) on your MOMO account was successfully completed at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", body)
            txn_id_match = re.search(r"Financial Transaction Id: (\d+)", body)
            
            if match and txn_id_match:
                amount = int(match.group(1))
                initiator = match.group(2)
                date_time = match.group(3)
                txn_id = txn_id_match.group(1)
                
                data.append({
                    "Type": "Transaction Initiated by Another Party",
                    "Amount": amount,
                    "Initiator": initiator,
                    "DateTime": date_time,
                    "TransactionID": txn_id
                })

        # 8. Withdrawals from Agents
        elif body.startswith("You Wakuma Tekalign DEBELA"):
            match = re.search(r"You (.*?)\(\*+\d{3}\) have via agent: (.*?) \((\d+)\), withdrawn (\d+) RWF.*?at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", body)
            if match:
                user_name = match.group(1)
                agent_name = match.group(2)
                agent_number = match.group(3)
                amount = int(match.group(4))
                date_time = match.group(5)
                
                data.append({
                    "Type": "Withdrawal from Agent",
                    "UserName": user_name.strip(),
                    "AgentName": agent_name.strip(),
                    "AgentNumber": agent_number,
                    "Amount": amount,
                    "DateTime": date_time
                })
        
        # 9. Bank Transfers - Sending money to self or others from a bank
        elif body.startswith("You have transferred"):
            match = re.search(r"You have transferred (\d+) RWF to (.*?) from your .*? at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", body)
            if match:
                amount = int(match.group(1))
                recipient = match.group(2)
                date_time = match.group(3)
                
                data.append({
                    "Type": "Bank Transfer",
                    "Amount": amount,
                    "Recipient": recipient.strip(),
                    "DateTime": date_time
                })

        # 10. Internet or Voice Bundle Purchases
        elif body.startswith("Yello!Umaze kugura"):
            if "FRW" in body or "Rwf" in body:  # Internet bundle
                match = re.search(r"Yello!Umaze kugura ([\d,]+)(?:Rwf|FRW)\((\d+)(GB|MB)\)", body)
                if match:
                    amount = int(match.group(1).replace(",", ""))  # Remove commas and convert to integer
                    bundle_size = int(match.group(2))
                    unit = match.group(3)

                    data.append({
                        "Type": "Internet Bundle Purchase",
                        "Amount": amount,
                        "BundleSize": bundle_size,
                        "Unit": unit
                    })
            elif "Frw=" in body:  # Voice bundle
                match = re.search(r"Yello!Umaze kugura ([\d,]+)Frw=(\d+)Mins\+(\d+)SMS", body)
                if match:
                    amount = int(match.group(1).replace(",", ""))
                    minutes = int(match.group(2))
                    sms = int(match.group(3))

                    data.append({
                        "Type": "Voice Bundle Purchase",
                        "Amount": amount,
                        "Minutes": minutes,
                        "SMS": sms
                    })

    print(f"Processed {len(data)} SMS messages.")
    print(f"Failed to process {len(failed_sms)} SMS messages.")
    return data

def verify_processed_transactions(file_path):
    sms_elements = parse_xml(file_path)
    total_sms = len(sms_elements)
    
    # Track counts for all transaction types
    processed_count = {
        "Incoming Money": 0,
        "Payment to Code Holder": 0,
        "Transfer to Mobile Number": 0,
        "Bank Deposit": 0,
        "Airtime Bill Payment": 0,
        "Cash Power Bill Payment": 0,
        "Transaction Initiated by Another Party": 0,
        "Withdrawal from Agent": 0,
        "Bank Transfer": 0,
        "Internet Bundle Purchase": 0,
        "Voice Bundle Purchase": 0,
        "Ignored": 0,
    }

    for sms in sms_elements:
        body = sms.attrib.get("body", "")
        
        # Categorize and count transactions

        if body.startswith("You have received"):
            processed_count["Incoming Money"] += 1
        elif body.startswith("TxId"):
            processed_count["Payment to Code Holder"] += 1
        elif body.startswith("*165*S*"):
            processed_count["Transfer to Mobile Number"] += 1
        elif body.startswith("*113*R*"):
            processed_count["Bank Deposit"] += 1
        elif body.startswith("*162*"):  # Bill payments
            if "Airtime" in body:
                processed_count["Airtime Bill Payment"] += 1
            elif "Cash Power" in body:
                processed_count["Cash Power Bill Payment"] += 1
        elif body.startswith("*164*S*"):
            processed_count["Transaction Initiated by Another Party"] += 1
        elif body.startswith("You Wakuma Tekalign DEBELA"):  # Withdrawals from agents
            processed_count["Withdrawal from Agent"] += 1
        elif body.startswith("You have transferred"):  # Bank transfers
            processed_count["Bank Transfer"] += 1
        elif body.startswith("Yello!Umaze kugura"):  # Internet/Voice Bundle Purchases
            if "FRW" in body or "Rwf" in body:
                processed_count["Internet Bundle Purchase"] += 1
            elif "Frw" in body:
                processed_count["Voice Bundle Purchase"] += 1
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

def push_to_sqlite_by_type(df, db_path="db/transactions_by_type_debug.db"):
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
        """,
        "airtime_bill_payments": """
        CREATE TABLE IF NOT EXISTS airtime_bill_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT,
            amount REAL,
            date_time TEXT,
            fee REAL
        )
        """,
        "cash_power_bill_payments": """
        CREATE TABLE IF NOT EXISTS cash_power_bill_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT,
            amount REAL,
            date_time TEXT,
            fee REAL
        )
        """,
        "third_party_transactions": """
        CREATE TABLE IF NOT EXISTS third_party_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            initiated_by TEXT,
            date_time TEXT,
            transaction_id TEXT
        )
        """,
        "withdrawals_from_agents": """
        CREATE TABLE IF NOT EXISTS withdrawals_from_agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            agent_name TEXT,
            agent_number TEXT,
            amount REAL,
            date_time TEXT
        )
        """,
        "bank_transfers": """
        CREATE TABLE IF NOT EXISTS bank_transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            recipient TEXT,
            date_time TEXT
        )
        """,
        "internet_bundle_purchases": """
        CREATE TABLE IF NOT EXISTS internet_bundle_purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            bundle_size TEXT,
            unit TEXT,
            duration TEXT
        )
        """,
        "voice_bundle_purchases": """
        CREATE TABLE IF NOT EXISTS voice_bundle_purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            minutes TEXT,
            smses TEXT
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
        
        elif row["Type"] == "Airtime Bill Payment":
            cursor.execute("""
            INSERT INTO airtime_bill_payments (transaction_id, amount, date_time, fee)
            VALUES (?, ?, ?, ?)
            """, (row.get("TransactionID"), row["Amount"], row["DateTime"], row.get("Fee")))
        
        elif row["Type"] == "MTN Cash Power Bill Payment":
            cursor.execute("""
            INSERT INTO cash_power_bill_payments (transaction_id, amount, date_time, fee)
            VALUES (?, ?, ?, ?)
            """, (row.get("TransactionID"), row["Amount"], row["DateTime"], row.get("Fee")))
        
        elif row["Type"] == "Transaction Initiated by Another Party":
            cursor.execute("""
            INSERT INTO third_party_transactions (amount, initiated_by, date_time, transaction_id)
            VALUES (?, ?, ?, ?)
            """, (row["Amount"], row.get("Initiator"), row["DateTime"], row.get("TransactionID")))
        
        elif row["Type"] == "Withdrawal from Agent":
            cursor.execute("""
            INSERT INTO withdrawals_from_agents (user_name, agent_name, agent_number, amount, date_time)
            VALUES (?, ?, ?, ?, ?)
            """, (row.get("UserName"), row.get("AgentName"), row.get("AgentNumber"), row["Amount"], row["DateTime"]))
        
        elif row["Type"] == "Bank Transfer":
            cursor.execute("""
            INSERT INTO bank_transfers (amount, recipient, date_time)
            VALUES (?, ?, ?)
            """, (row["Amount"], row["Recipient"], row["DateTime"]))
        
        elif row["Type"] == "Internet Bundle Purchase":
            cursor.execute("""
            INSERT INTO internet_bundle_purchases (amount, bundle_size, unit, duration)
            VALUES (?, ?, ?, ?)
            """, (row["Amount"], row.get("BundleSize"), row.get("Unit"), row.get("Duration")))
        
        elif row["Type"] == "Voice Bundle Purchase":
            cursor.execute("""
            INSERT INTO voice_bundle_purchases (amount, minutes, smses)
            VALUES (?, ?, ?)
            """, (row["Amount"], row.get("Minutes"), row.get("SMS")))
    
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


def log_ignored_messages(file_path, output_log="ignored_messages.log"):
    sms_elements = parse_xml(file_path)
    ignored_messages = []

    for sms in sms_elements:
        body = sms.attrib.get("body", "")
        
        # Check for ignored messages based on their patterns
        if not (
            
            body.startswith("You have received")
            or body.startswith("TxId")
            or body.startswith("*165*S*")
            or body.startswith("*113*R*")
            or body.startswith("*162*")  # Bill payments
            or body.startswith("*164*S*")  # Transactions initiated by another party
            or body.startswith("You ")  # Withdrawals from agents
            or body.startswith("Yello!Umaze kugura")  # Internet/Voice Bundle purchases
        ):
            ignored_messages.append(body)

    # Write ignored messages to the log file
    with open(output_log, "w") as log_file:
        for message in ignored_messages:
            log_file.write(f"{message}\n")
    
    print(f"{len(ignored_messages)} ignored messages written to {output_log}")


# Convert data to DataFrame and display
def main(file_path):
    sms_elements = parse_xml(file_path)
    transactions = extract_transaction_data(sms_elements)
    df = pd.DataFrame(transactions)
    
    print(df)

    # output_file = "cleaned_data.csv"
    # output_file = "cleaned_data_v2.csv"
    # output_file = "cleaned_data.json"
    # write_to_csv(df, output_file)
    # write_to_json(df, output_file)

    verify_processed_transactions(file_path)
    # log_ignored_messages(file_path)
    push_to_sqlite_by_type(df)
    return df

# Run the script with the provided file
file_path = "sms-20250116123406.xml"
df = main(file_path)
