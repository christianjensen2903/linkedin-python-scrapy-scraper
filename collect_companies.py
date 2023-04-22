import json
import os

# Import all json files in jobs folder
# And create a list of all the jobs

jobs = []
for filename in os.listdir("jobs"):
    if filename.endswith(".json"):
        with open("jobs/" + filename) as f:
            job = json.load(f)
            jobs.append(job)

# Convert from list of lists to a list
jobs = [job for sublist in jobs for job in sublist]


# Convert from a list of dicts to a list of strings (the dict only contain one string)
jobs = [job["company_link"] for job in jobs]

# Remove parameters from the url
jobs = [job.split("?")[0] for job in jobs]

print(len(jobs))
# Remove duplicates
jobs = list(set(jobs))

print(len(jobs))

# Save to json file
with open("jobs.json", "w") as f:
    json.dump(jobs, f)
