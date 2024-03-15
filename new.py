# # # import requests
# # # import smtplib, ssl
# # # import pandas as pd
# # # from bs4 import BeautifulSoup
# # # d={"16":"42","13":"42","19":"42","96":"05","17":"42","34":"49","45":"49","D5":"05","E7":"05","E2":"05","64":"42","22":"42","16":"42"}
# # # # d={"88":"42"}
# # # branch_code={"01":"CIV","02":"EEE","03":"MEC","04":"ECE","05":"CSE","12":"IT","42":"CSM","47":"CC","49":"CSO","54":"AD"}
# # # header=[]
# # # final=""
# # # for i in d:
# # #     try:
# # #         header=[]
# # #         while header==[]:
# # #             URL = "https://www.vvitguntur.com/results/R20/Y20_4-1_REGULAR_DEC23/result.php?htno=20bq1a4214&group="+branch_code["42"] 
# # #             r = requests.get(URL)
# # #             head=""
# # #             x=""
# # #             soup = BeautifulSoup(r.content,'html5lib')
# # #             header = soup.find_all("td")
# # #             heading = soup.find_all("th")
# # #             print(str(header))
# # #         final+=str([header])+"\n"

# # #     except:
# # #         pass 



# # # HOST = "smtp-mail.outlook.com"
# # # PORT = 587

# # # FROM_EMAIL = "dasaribhovan@outlook.com"
# # # TO_EMAIL = "dasaribhovan@gmail.com"
# # # PASSWORD = "bhovan123#"

# # # MESSAGE = """Subject: Result

# # # """+str(final)

# # # smtp = smtplib.SMTP(HOST, PORT)

# # # status_code, response = smtp.ehlo()
# # # print(f"[*] Echoing the server: {status_code} {response}")

# # # status_code, response = smtp.starttls()
# # # print(f"[*] Starting TLS connection: {status_code} {response}")

# # # status_code, response = smtp.login(FROM_EMAIL, PASSWORD)
# # # print(f"[*] Logging in: {status_code} {response}")

# # # smtp.sendmail(FROM_EMAIL, TO_EMAIL, MESSAGE)
# # # smtp.quit()
# # print(bool("0"))

# import os
# import shutil
# def count_files_in_subdirectories(directory):
#     # Dictionary to store the count of files in each subdirectory
#     files_count = {}

#     # Iterate over each entry in the specified directory
#     for entry in os.scandir(directory):
#         if entry.is_dir():
#             # If the entry is a subdirectory, count the files in it
#             subdir_files = [f.name for f in os.scandir(entry.path) if f.is_file()]
#             files_count[entry.path+"$"+entry.name] = len(subdir_files)

#     return files_count

# if __name__ == "__main__":
#     total_5=0
#     total_6=0
#     total_7=0
#     total_4=0
#     total_8=0
#     # directory = input("Enter the directory path: ")
#     files_count = count_files_in_subdirectories(r"E:\vara\archive\data\data")
#     print("\nNumber of files in each subdirectory:")
#     for subdir, count in files_count.items():
#         x=subdir.split("$")
#         subdir=x[0]
#         name=x[1]
#         print(name,count)
        
#     # print(total_8,total_5,total_6,total_7)


