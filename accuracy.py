import pandas as pd
#read in predicted results
#compare each result to the loist fo school domains and see if it macthes teh expect output

#full list of all school related domains 
schoolDomains = [
    # all whitworth domains
    "whitworth.edu", "whitworthportal.org", "pirateport.whitworth.edu", "my.whitworth.edu", "selfservice.whitworth.edu",
    "canvas.whitworth.edu", "whitgit.whitworth.edu", "git.whitworth.edu",
    # canvas domains
    "instructure.com", "canvas.instructure.com",
    # microsoft domains
    "microsoftonline.com", "login.microsoftonline.com", "login.live.com", "office.com", "outlook.com",
    "outlook.office.com", "microsoft.com", "office365.com", "graph.microsoft.com", "teams.microsoft.com", "onedrive.live.com",
    # google domains
    "google.com", "gmail.com", "mail.google.com", "docs.google.com", "drive.google.com", "slides.google.com",
    "sheets.google.com", "accounts.google.com", "googleusercontent.com", "gstatic.com",
    # math/science:
    "desmos.com", "www.desmos.com", "pearson.com", "pearsonhighered.com", "revel.pearson.com",
    "mlm.pearson.com", "etext.pearson.com",
    # gitHub
    "github.com", "api.github.com", "raw.githubusercontent.com", "githubusercontent.com",
    # vitalSource
    "vitalsource.com", "bookshelf.vitalsource.com", "api.vitalsource.com", "launch.vitalsource.com",
    # random
    "spotify.com",
]


df = pd.read_fwf("predictedResults.txt")

#make list of (domain, label) and force label to string
goodList = list(zip(df['sniDomain'], df['predictedLabel'].astype(str)))

correct = 0
incorrect = 0

for a, b in goodList:  #readingin the domain (a) and the predicted 0 or 1 value(b)   
    if pd.isna(a):
        continue

    a = str(a).strip().lower()  #
    found = False

    i = 0
    while i < len(schoolDomains):
        domain = schoolDomains[i].lower()

        #match exact or subdomain
        if a == domain or a.endswith("." + domain):
            found = True
            break

        i += 1

    #assess if its accutaully accurate or not
    if found:
        #should be 1 menaing is classified as shool related
        if b == "1":
            correct += 1
        else:
            incorrect += 1
    else:
        #shoudl be zero as in not classified as school related
        if b == "0":
            correct += 1
        else:
            incorrect += 1

print("Correct:", correct)
print("Incorrect:", incorrect)
print("Total:", correct + incorrect)
