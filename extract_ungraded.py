import json

# Load the JSON file
with open('github_submissions.json', 'r') as f:
    submissions = json.load(f)

# Extract ungraded submissions
ungraded = []
for student, data in submissions.items():
    if data.get('graded') == False and data.get('submission') != "No submission" and data.get('submission') != "File upload submission":
        ungraded.append({
            "name": student,
            "submission": data['submission']
        })

# Print the results
print(f"Total ungraded submissions: {len(ungraded)}")
print("\nUngraded students:")
for i, student in enumerate(ungraded, 1):
    print(f"{i}. {student['name']} - {student['submission']}")
