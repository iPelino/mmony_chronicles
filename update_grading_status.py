import json
import os

# Load the JSON file
with open('github_submissions.json', 'r') as f:
    submissions = json.load(f)

# Get all directories in the current folder
directories = [d for d in os.listdir('.') if os.path.isdir(d)]

# Count of updates made
updates = 0

# Update graded status
for student, data in submissions.items():
    if data.get('graded') == False:  # Only check ungraded submissions
        if student in directories:
            # If there's a folder with the student's name, mark as graded
            submissions[student]['graded'] = True
            updates += 1
            print(f"Marked {student} as graded")

# Save the updated JSON file
with open('github_submissions.json', 'w') as f:
    json.dump(submissions, f, indent=4)

print(f"\nUpdated {updates} student records in github_submissions.json")
