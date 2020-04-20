import psutil
import flask
from flask import request,jsonify


app = flask.Flask(__name__)
app.config["DEBUG"] = True

@app.route('/api/v1/sortedProcesses', methods=['GET'])
def api_get_sorted_processes():
    lowToHigh=1
    sortOrder = request.args.get("lowToHigh")
    numShow = request.args.get("numShow")
    numProcessesToShow = -1
    if numShow:
        try:
            numProcessesToShow= int(numShow)
        except ValueError:
            return {"error": "invalid parameters"}, 400
        
    if sortOrder:
        try:
            lowToHigh = int(sortOrder)
        except ValueError:
            return {"error": "invalid parameters"}, 400
    processInfo = []
    for proc in psutil.process_iter():
       try:
           pinfo = proc.as_dict(attrs=['pid', 'name', 'username'])
           pinfo['vms'] = proc.memory_info().vms
           processInfo.append(pinfo)
       except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
           pass
 
    result = []
    if lowToHigh > 0:
        result = sorted(processInfo, key=lambda procObj: procObj['vms'])
    else:
        result = sorted(processInfo, key=lambda procObj: procObj['vms'], reverse=True)
    
    if numProcessesToShow > -1:
        result = [result[index] for index in range(0, numProcessesToShow)]

 
    return jsonify(result),200
    



app.run()
