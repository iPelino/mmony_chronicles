import xml.etree.ElementTree as ET
import re
from datetime import datetime
from ..models import (
    IncomingMoney, PaymentToCodeHolder, TransferToMobile, BankDeposit,
    AirtimeBillPayment, CashPowerBillPayment, ThirdPartyTransaction,
    WithdrawalFromAgent, BankTransfer, InternetBundlePurchase, VoiceBundlePurchase,
    FailedSMSLog
)

# Parse the XML file
def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    return root.findall("sms")

# Extract and categorize SMS messages
def extract_transaction_data(sms_elements, user=None):
    processed_count = 0
    failed_count = 0
    data = []
    failed_sms = []

    for sms in sms_elements:
        body = sms.attrib.get("body", "")
        processed_successfully = False
        reason = None
        reason = None

        # 1. System Notifications
        if body.startswith("*143*R*"):
            if "successfully registered" in body:
                processed_successfully = True
                continue  # Skip registration messages
            if "failed" in body:
                processed_successfully = True # Consider system failures as processed (skipped)
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

                # Create IncomingMoney object
                IncomingMoney.objects.create(
                    amount=amount,
                    sender=sender,
                    date_time=date_time,
                    transaction_id=txn_id,
                    user=user
                )
                processed_successfully = True
            else:
                reason = "Missing data for Incoming Money (amount, sender, date, or transaction ID)"

        # 3. Payments to Code Holders
        elif body.startswith("TxId"):
            # Generalized matching
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
                # Create PaymentToCodeHolder object
                PaymentToCodeHolder.objects.create(
                    transaction_id=txn_id,
                    amount=amount,
                    recipient=recipient,
                    date_time=date_time,
                    user=user
                )
                processed_successfully = True
                processed_count += 1
            else:
                reason = "Missing data for Payment to Code Holder (TxId, amount, recipient, or date)"
                failed_count += 1
                FailedSMSLog.objects.create(sms_body=body, reason=reason, user=user)

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

                # Create TransferToMobile object
                TransferToMobile.objects.create(
                    amount=amount,
                    recipient=recipient,
                    recipient_number=recipient_number,
                    date_time=date_time,
                    fee=fee,
                    user=user
                )
                processed_successfully = True
                processed_count += 1
            else:
                reason = "Missing data for Transfer to Mobile (amount, recipient, number, date, or fee)"

        # 5. Bank Deposits
        elif body.startswith("*113*R*"):
            match = re.search(r"deposit of (\d+) RWF", body)
            date_time_match = re.search(r"at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", body)

            if match and date_time_match:
                amount = int(match.group(1))
                date_time = date_time_match.group(1)

                # Create BankDeposit object
                BankDeposit.objects.create(
                    amount=amount,
                    date_time=date_time,
                    user=user
                )
                processed_successfully = True
                processed_count += 1
            else:
                reason = "Missing data for Bank Deposit (amount or date)"

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

                if bill_type == "Airtime":
                    # Create AirtimeBillPayment object
                    AirtimeBillPayment.objects.create(
                        transaction_id=txn_id,
                        amount=amount,
                        date_time=date_time,
                        fee=fee,
                        user=user
                    )
                    processed_successfully = True
                    processed_count += 1
                elif bill_type == "MTN Cash Power":
                    # Create CashPowerBillPayment object
                    CashPowerBillPayment.objects.create(
                        transaction_id=txn_id,
                        amount=amount,
                        date_time=date_time,
                        fee=fee,
                        user=user
                    )
                    processed_successfully = True
                    processed_count += 1
            else:
                reason = "Missing data for Bill Purchase (TxId, amount, bill type, date, or fee)"
                failed_count += 1
                FailedSMSLog.objects.create(sms_body=body, reason=reason, user=user)

        # 7. Transactions Initiated by Another Party
        elif body.startswith("*164*S*"):
            match = re.search(r"A transaction of (\d+) RWF by (.*?) on your MOMO account was successfully completed at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", body)
            txn_id_match = re.search(r"Financial Transaction Id: (\d+)", body)

            if match and txn_id_match:
                amount = int(match.group(1))
                initiator = match.group(2)
                date_time = match.group(3)
                txn_id = txn_id_match.group(1)

                # Create ThirdPartyTransaction object
                ThirdPartyTransaction.objects.create(
                    amount=amount,
                    initiated_by=initiator,
                    date_time=date_time,
                    transaction_id=txn_id,
                    user=user
                )
                processed_successfully = True
                processed_count += 1
            else:
                reason = "Missing data for Third Party Transaction (amount, initiator, date, or transaction ID)"

        # 8. Withdrawals from Agents
        elif body.startswith("You "): # More generic start
            match = re.search(r"You (.*?)\(\*+\d{3}\) have via agent: (.*?) \((\d+)\), withdrawn (\d+) RWF.*?at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", body)
            if match:
                user_name = match.group(1) # This captures the name dynamically
                agent_name = match.group(2)
                agent_number = match.group(3)
                amount = int(match.group(4))
                date_time = match.group(5)

                # Create WithdrawalFromAgent object
                WithdrawalFromAgent.objects.create(
                    user_name=user_name.strip(),
                    agent_name=agent_name.strip(),
                    agent_number=agent_number,
                    amount=amount,
                    date_time=date_time,
                    user=user
                )
                processed_successfully = True
                processed_count += 1
            else:
                reason = "Missing data for Withdrawal from Agent (user name, agent name/number, amount, or date)"

        # 9. Bank Transfers - Sending money to self or others from a bank
        elif body.startswith("You have transferred"):
            match = re.search(r"You have transferred (\d+) RWF to (.*?) from your .*? at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", body)
            if match:
                amount = int(match.group(1))
                recipient = match.group(2)
                date_time = match.group(3)

                # Create BankTransfer object
                BankTransfer.objects.create(
                    amount=amount,
                    recipient=recipient.strip(),
                    date_time=date_time,
                    user=user
                )
                processed_successfully = True
                processed_count += 1
            else:
                reason = "Missing data for Bank Transfer (amount, recipient, or date)"

        # 10. Internet or Voice Bundle Purchases
        elif body.startswith("Yello!Umaze kugura"):
            if "FRW" in body or "Rwf" in body:  # Internet bundle
                match = re.search(r"Yello!Umaze kugura ([\d,]+)(?:Rwf|FRW)\((\d+)(GB|MB)\)", body)
                if match:
                    amount = int(match.group(1).replace(",", ""))  # Remove commas and convert to integer
                    bundle_size = match.group(2)
                    unit = match.group(3)

                    # Create InternetBundlePurchase object
                    InternetBundlePurchase.objects.create(
                        amount=amount,
                        bundle_size=bundle_size,
                        unit=unit,
                        user=user
                    )
            elif "Frw=" in body:  # Voice bundle
                match = re.search(r"Yello!Umaze kugura ([\d,]+)Frw=(\d+)Mins\+(\d+)SMS", body)
                if match:
                    amount = int(match.group(1).replace(",", ""))
                    minutes = match.group(2)
                    sms = match.group(3)

                    # Create VoiceBundlePurchase object
                    VoiceBundlePurchase.objects.create(
                        amount=amount,
                        minutes=minutes,
                        smses=sms,
                        user=user
                    )

    print(f"Processed {len(data)} SMS messages.")
    print(f"Failed to process {len(failed_sms)} SMS messages.")
    return data

# Main function to process XML file
def process_xml_file(xml_file, user=None):
    # If xml_file is a FileField from a model, open it
    if hasattr(xml_file, 'path'):
        with open(xml_file.path, 'rb') as f:
            sms_elements = parse_xml(f)
    else:
        # For backward compatibility, handle direct file objects
        sms_elements = parse_xml(xml_file)

    extract_transaction_data(sms_elements, user)
    print(f"XML file processed successfully with {len(sms_elements)} SMS messages.")
