import subprocess   #this is used to run tshark live and get live input from tshark
import csv          #helps to parse tsharks csv files (theyre being def in as csv files)
import pandas as pd     #converts packet dicts into a table which is then fed to model
from sklearn.ensemble import RandomForestClassifier     #contains all the objs of the model behidn the scenes
from joblib import dump     #saves the trained model
import ipaddress    #used to conver ip to num

#need to capture live packets from tshark
INTERFACE ="en0"        #the interface tshark is listening for traffic on, based WiFi interface

#full list of all school related domains 
schoolDomains = [
    #all whitworth domains
    "whitworth.edu", "whitworthportal.org", "pirateport.whitworth.edu", "my.whitworth.edu", "selfservice.whitworth.edu",
    "canvas.whitworth.edu","whitgit.whitworth.edu","git.whitworth.edu",
    #canvas domains
    "instructure.com", "canvas.instructure.com",
    #microsoft domains
    "microsoftonline.com","login.microsoftonline.com", "login.live.com", "office.com", "outlook.com",
    "outlook.office.com", "microsoft.com", "office365.com", "graph.microsoft.com", "teams.microsoft.com","onedrive.live.com",
    #google domains
    "google.com", "gmail.com", "mail.google.com", "docs.google.com", "drive.google.com", "slides.google.com",
    "sheets.google.com", "accounts.google.com", "googleusercontent.com", "gstatic.com",
    #math/science:
    "desmos.com","www.desmos.com", "pearson.com", "pearsonhighered.com", "revel.pearson.com",
    "mlm.pearson.com", "etext.pearson.com",
    #gitHub
    "github.com", "api.github.com", "raw.githubusercontent.com",  "githubusercontent.com",
    #vitalSource
    "vitalsource.com", "bookshelf.vitalsource.com", "api.vitalsource.com", "launch.vitalsource.com",
    #random
    "spotify.com",
]

def captureLivePackets():
    #these are the output coloums of the "exported" CSV from tshark
    fields = [
        "frame.number",
        "frame.time_relative",
        "ip.src",
        "ip.dst",
        "tls.handshake.extensions_server_name", #same as "info" coloumn in wireshark GUI
        "frame.len",
    ]
    #building the command to run tshark as if it were running from terminal
    cmd = [
        "tshark",
        "-i", INTERFACE,    #telling it what interface we want tshark to listen for tarffic on
        "-l",   #buffer the line
        "-T", "fields", #fields we previously defined
        "-E", "separator=,",    #delimeter for CSV, -E for CSV formatting
        "-E", "quote=d", #for double wuotes
        "-E", "header=y",   #include header so we know coloumn name
    ]
    #-e for extracting fields
    for f in fields:
        cmd.extend(["-e", f])       #telling it to give results for each field value
    
    print("running:", " ".join(cmd))    #prints when the cmd is being run

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1,) #running command in terminal w./process

    filteredRows = []   #row i wanted to keep after knowing "info" isnt empty

    try:
        assert proc.stdout is not None  # if its empty, prog terminates
        readcsv = csv.DictReader(proc.stdout)   #storigng in readcsv

        #####TEMP FOR TESTING######
        count = 0
        with open("outputFile.txt", "w") as file:
            for row in readcsv:
                if row["tls.handshake.extensions_server_name"] != "":   #if its NOT empty, we keep!
                    file.write(str(row) + "\n")
                    filteredRows.append(row)
                    count +=1
                if count >= 500: #quit after 10 packets
                    break
        ###########################

    finally:
        proc.terminate()    #polietrly try to end process
        try:
            proc.wait(timeout=3)    #give her three secs to shut down properly
        except subprocess.TimeoutExpired:     #if she don't listen!!!
            proc.kill() #kill her


    print("\nDone. Read:", count, "packets.")

    #if somehow no good packest are captured, end prog cleanly
    if not filteredRows:
        print("No packets with non-empty SNI captured. Exiting.")
        return


    #need to convert csv into a table form that can be read in by the model
    df = pd.DataFrame(filteredRows) #convert dict to pando data frame
    print(df.head())    #xxx
    
    #convert that data into numerical values so ml can understand it
    df["frame.number"] = pd.to_numeric(df["frame.number"], errors="coerce")
    df["frame.time_relative"] = pd.to_numeric(df["frame.time_relative"], errors="coerce")
    df["frame.len"] = pd.to_numeric(df["frame.len"], errors="coerce")
    df["ip.src"] = df["ip.src"].apply(ipToNum)
    df["ip.dst"] = df["ip.dst"].apply(ipToNum)

    #now we have converted the data into numbers, now its time to label it
    #bc ml cannot take string, only numbers, this assigns arbitrary numerical value to website name
    df["label"] = df["tls.handshake.extensions_server_name"].apply(schoolRelated)

    #now encode data farme after being labeled:
    df["tls.handshake.extensions_server_name"] = (df["tls.handshake.extensions_server_name"].astype("category").cat.codes)

    df = df.dropna()    #incase any of the converted numerica values contain NaN(not a number indicator)- GET RID OF PACKET

    with open("dataframeOutput.txt", "w") as f:
        f.write(df.to_string())

    #need to send the tshark info and the corresponding answer flags to the model to train

    #makign a variable to hold a singular frame to send to our lovley ml robot, only the fields we want as input values
    X = df[["frame.number", "frame.time_relative", "ip.src", "ip.dst",  "tls.handshake.extensions_server_name", "frame.len"]]
    #a seperate labled df to send to the ml; this is teh corresponding label to that row we send in X
    y = df["label"] 
    #n_estimators: tells it how mnay trees to make 200 is good for pratice, 500 is best for most accurate, over 1000 is unneccesary
    # random_state: this controls the level of randomness, so it causes how reproduceable the results are 
    #xxx -=> look more into this about how it works for report
    model = RandomForestClassifier(n_estimators=300, random_state=69)   #creatign the random forest
    model.fit(X, y)
    dump(model, "networkingLM7Classifier.joblib") #saves the traine dmodel 

    

#function to match domian name against list of school related domains
def schoolRelated(sni):
    if not isinstance(sni, str):
        return 0
    sni = sni.lower()
    for domain in schoolDomains:
        if domain in sni:
            return 1
    return 0


#quick function to convert ip to num
def ipToNum(ip):
    if ip == "":    
        return 0
    try:
        return int(ipaddress.ip_address(ip))    #return converted ip num
    except:
        return 0


if __name__ == "__main__":
    captureLivePackets()