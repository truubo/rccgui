from tkinter import *
import tkinter.ttk as ttk
from tkinter import messagebox, filedialog
import xml.etree.ElementTree as ET
import requests, time, random, base64

def sendSoap(ip, port, action, xml, *args, **kwargs):
  try:
    attempt_time = time.time()
    soap_req = requests.post(f"http://{ip}:{str(port)}/", headers={"SOAPAction": f"http://roblox.com/{action}", "Content-Type": "application/xml", "User-Agent": "rccGUI/1.0"}, data=f"""<?xml version='1.0' encoding='utf-8'?><soap-env:Envelope xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><soap-env:Body>{xml}</soap-env:Body></soap-env:Envelope>""", timeout=kwargs.get("timeout") if kwargs.get("timeout") != None else 5)
    connect_time = time.time()
    ping = int((connect_time - attempt_time) * 1000)
  except:
    return False, "Timeout", 5000
  if soap_req.status_code == 200 and b"RCCServiceSoap" in soap_req.content:
    return True, soap_req.content, ping
  else:
    return False, soap_req.content, ping

def ping():
  success, content, ping = sendSoap(ip.get(), port.get(), "HelloWorld", """<ns0:HelloWorld xmlns:ns0="http://roblox.com/"/>""")
  if success:
    messagebox.showinfo("Pong!", f"Pong! Ping: {str(ping)}ms")
  else:
    messagebox.showerror("Failed", f"Failed to ping RCCService. Error: {content}")

def getAllJobs():
  joblist.delete(*joblist.get_children())
  success, content, ping = sendSoap(ip.get(), port.get(), "GetAllJobs", """<ns0:GetAllJobs xmlns:ns0="http://roblox.com/"/>""")
  if success:
    root = ET.fromstring(content.decode())
    jobs = root.findall(".//{http://roblox.com/}GetAllJobsResult")
    if len(jobs) == 0:
      messagebox.showinfo("All jobs", "There are no jobs running on this instance")
    else:
      global all_jobs
      jobs_list = []
      for i in jobs:
        job_id = i.find("{http://roblox.com/}id").text
        expiration = i.find("{http://roblox.com/}expirationInSeconds").text
        category = i.find("{http://roblox.com/}category").text
        cores = i.find("{http://roblox.com/}cores").text
        jobs_list.append([job_id, expiration, category, cores])
        joblist.insert(parent="", index="end", text="", values=[job_id, expiration, category, cores])
  else:
    messagebox.showerror("Failed", f"Failed to get jobs. Error: {content}")

def selectJob():
  messagebox.showinfo("Test", joblist.item(joblist.focus()))

def createJob(jobID, expiration, *args, **kwargs):
  if jobID == "":
    messagebox.showerror("Error", "You must enter a job ID")
    return
  success, content, ping = sendSoap(ip.get(), port.get(), "OpenJob", f"""<ns0:OpenJob xmlns:ns0="http://roblox.com/"><ns0:job><ns0:id>{jobID}</ns0:id><ns0:expirationInSeconds>{expiration}</ns0:expirationInSeconds><ns0:category>0</ns0:category><ns0:cores>1</ns0:cores></ns0:job><ns0:script><ns0:name>test</ns0:name><ns0:script>print('Hello world')</ns0:script></ns0:script></ns0:OpenJob>""")
  if success:
    getAllJobs()
    messagebox.showinfo("Job created", "Created job successfully!")
    if kwargs.get("window") != None:
      kwargs.get("window").destroy()
    
  else:
    messagebox.showerror("Failed", "Failed to create job. Is the Job ID already in use?")


def showCreateJobWindow():
  createJobWindow = Toplevel()
  createJobWindow.geometry("330x100")
  createJobWindow.title("Create new job")
  Label(createJobWindow, text="Job ID").grid(row=0, column=0, padx=5, pady=5, sticky=E)
  jobID = Entry(createJobWindow)
  jobID.grid(row=0, column=1, padx=5, pady=5, columnspan=3)
  Label(createJobWindow, text="Expiration (in seconds)").grid(row=1, column=0, padx=5, pady=5, sticky=E)
  exp = Entry(createJobWindow)
  exp.delete(0, END)
  exp.insert(0, "999999")
  exp.grid(row=1, column=1, padx=5, pady=5, columnspan=3)
  createjob = Button(createJobWindow, text="Create job", command=lambda: createJob(jobID.get(), exp.get(), window=createJobWindow)) # there's probably a better way to do this...
  createjob.grid(row=2, column=1, padx=5, pady=5, columnspan=2)

def getRCCInfo():
  success, content, ping = sendSoap(ip.get(), port.get(), "GetStatus", """<ns0:GetStatus xmlns:ns0="http://roblox.com/"/>""")
  if success:
    root = ET.fromstring(content.decode())
    results = root.find(".//{http://roblox.com/}GetStatusResult")
    version = results.find("{http://roblox.com/}version").text
    jobCount = results.find("{http://roblox.com/}environmentCount").text
    messagebox.showinfo("RCC information", f"""Version: {version}
Jobs running: {jobCount}""")

def executeScript(jobID, script, *args, **kwargs):
  success, content, ping = sendSoap(ip.get(), port.get(), "Execute", f"""<ns0:Execute xmlns:ns0="http://roblox.com/"><ns0:jobID>{jobID}</ns0:jobID><ns0:script><ns0:name>{random.randint(0, 999999)}</ns0:name><ns0:script>{script}</ns0:script></ns0:script></ns0:Execute>""", timeout=20)
  if success:
    root = ET.fromstring(content.decode())
    output = kwargs.get("textbox")
    if output != None:
      output.config(state=NORMAL)
      output.delete(1.0, END)
      executeResult = root.find(".//{http://roblox.com/}ExecuteResult")
      if executeResult != None:
        returned = executeResult.find("{http://roblox.com/}value").text
        global consoleOutput
        consoleOutput = returned
        if len(returned) >= 10000:
          output.insert("end", "<output too large, please save>")
        else:
          output.insert("end", returned)
      output.config(state=DISABLED)
  else:
    if content == "Timeout":
      messagebox.showerror("Error", "Failed to send script to RCC")
    else:
      root = ET.fromstring(content.decode())
      output = kwargs.get("textbox")
      if output != None:
        output.config(state=NORMAL)
        output.delete(1.0, END)
        output.insert("end", root.find(".//SOAP-ENV:Fault/faultstring", {"SOAP-ENV": "http://schemas.xmlsoap.org/soap/envelope/"}).text)
        output.config(state=DISABLED)
      else:
        messagebox.showerror("Error", root.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Fault/{http://schemas.xmlsoap.org/soap/envelope/}faultstring"))

def executeFile(jobID, *args, **kwargs):
  filename = filedialog.askopenfilename(filetypes=(("Lua script", "*.lua"), ("Text file", "*.txt"), ("All files", "*.*")))
  if filename != "":
    try:
      file = open(filename, 'r').read()
      executeScript(jobID, file, textbox=kwargs.get("textbox"))
    except Exception as e:
      messagebox.showerror("Error", f"Error opening file. Error: {e}")

def saveOutput():
  types = [("Text file", "*.txt"), ("JPG image", "*.jpg"), ("PNG image", "*.png"), ("All files", "*.*")]
  file = filedialog.asksaveasfile(filetypes=types, defaultextension=types)
  filename = file.name
  if filename.split(".")[-1] in ["jpg", "png"]:
    file.close()
    bytes_file = open(filename, "wb")
    bytes_file.write(base64.b64decode(consoleOutput))
    bytes_file.close()
  else:
    file.write(consoleOutput or None)
    file.close()
  messagebox.showinfo("Success", "Console output saved successfully")

def showExecuteWindow():
  if joblist.item(joblist.focus()).get("values") == "":
    messagebox.showerror("Error", "Please select a job to execute a script in")
    return
  jobID = joblist.item(joblist.focus()).get("values")[0]
  executeWindow = Toplevel()
  executeWindow.title(f"Executing script in {jobID}")
  scriptBox = Text(executeWindow, height=20, width=80, undo=True, autoseparators=True, maxundo=-1)
  scriptBox.grid(row=0, column=0, padx=5, pady=5, columnspan=80)
  output = Text(executeWindow, height=20, width=80)
  output.config(state=DISABLED)
  output.grid(row=3, column=0, padx=5, pady=5, columnspan=80)
  executeButton = Button(executeWindow, width=10, text="Execute", command=lambda: executeScript(jobID, scriptBox.get(1.0, END), textbox=output))
  executeButton.grid(row=1, column=0, padx=5, pady=5, sticky=W)
  clearButton = Button(executeWindow, width=10, text="Clear", command=lambda: scriptBox.delete(1.0, END))
  clearButton.grid(row=1, column=1, padx=5, pady=5, sticky=W)
  executeFileButton = Button(executeWindow, width=10, text="Execute file", command=lambda: executeFile(jobID, textbox=output))
  executeFileButton.grid(row=1, column=2, padx=5, pady=5, sticky=W)
  saveOutputButton = Button(executeWindow, width=10, text="Save output", command=lambda: saveOutput())
  saveOutputButton.grid(row=4, column=0, padx=5, pady=5, sticky=W)

def closeJob():
  if joblist.item(joblist.focus()).get("values") == "":
    messagebox.showerror("Error", "Please select a job to close")
    return
  success, content, ping = sendSoap(ip.get(), port.get(), "CloseJob", f"""<ns0:CloseJob xmlns:ns0="http://roblox.com/"><ns0:jobID>{joblist.item(joblist.focus()).get("values")[0]}</ns0:jobID></ns0:CloseJob>""")
  if success:
    messagebox.showinfo("Success", "Closed job successfully!")
  else:
    messagebox.showerror("Error", f"Failed to close job. Error: {content}")
  

root = Tk()
root.title("rccGUI 1.0")
root.geometry('485x310')
root.maxsize(485, 310)

ip_label = Label(root, text="IP")
ip_label.grid(row=1, column=0, sticky=E, padx=5)
ip = Entry(root)
ip.delete(0, END)
ip.insert(0, "127.0.0.1")
ip.grid(row=1, column=1, columnspan=2, padx=5, pady=5)

port_label = Label(root, text="Port")
port_label.grid(row=2, column=0, sticky=E, padx=5)
port = Entry()
port.delete(0, END)
port.insert(0, "64989")
port.grid(row=2, column=1, columnspan=2, padx=5, pady=5)

ping = Button(root, width=10, text="Ping", command=ping)
ping.grid(row=1, column=3, sticky=N, pady=5, padx=5)

ping = Button(root, width=10, text="RCC info", command=getRCCInfo)
ping.grid(row=1, column=4, sticky=N, pady=5, padx=5)

alljobs = Button(root, width=10, text="Get all jobs", command=getAllJobs)
alljobs.grid(row=2, column=3, sticky=N, pady=5, padx=5)

createjob = Button(root, width=10, text="Create job", command=showCreateJobWindow)
createjob.grid(row=2, column=4, sticky=N, pady=5, padx=5)

closejob = Button(root, width=10, text="Close job", command=closeJob)
closejob.grid(row=2, column=5, sticky=N, pady=5, padx=5)

execute = Button(root, width=10, text="Execute", command=showExecuteWindow)
execute.grid(row=3, column=3, pady=5, padx=5)

joblist = ttk.Treeview(root, height=10)
joblist['columns'] = ('jobID')
joblist.column("#0", width=0, stretch=NO)
joblist.column("jobID", width=50, anchor=W)
joblist.heading("#0", text="", anchor=CENTER)
joblist.heading("jobID", text="Job ID", anchor=W)
joblist.grid(row=3, column=0, columnspan=3, rowspan=100, padx=5, pady=5, sticky='nsew')

root.mainloop()