import pymongo
from pymongo import MongoClient
import flask
from flask import request,jsonify
from datetime import datetime
from pymongo import errors

app = flask.Flask(__name__)
app.config["DEBUG"] = True


cluster = MongoClient("mongodb+srv://yourAccount.mongodb.net/test?retryWrites=true&w=majority")
db = cluster["test"]
collection = db["test"]
collection2 = db["test2"]


@app.route('/', methods=['GET'])
def home():
    return "ok", 200

@app.route('/api/v1/projects', methods=['GET'])
def api_get():
    query_parameters = request.args
    result_message, code = validate_parameters(query_parameters)
    if code == 400:
        return result_message, code
    
    
    ##objects = query_parameters.get('objects')
    ##checkObj()
    response = collection.find(result_message)
    result = [project for project in response]
    
    return jsonify(result), code

def validate_parameters(query_parameters, validateObject=False):
    search_parameters = {}
    project_id = query_parameters.get('projectId')
    if project_id:
        try:
            project_id = int(project_id)
            
        except ValueError:
            return {"error": "invalid project id"}, 400
        print(project_id)
        search_parameters["_id"] = project_id

    user_id = query_parameters.get('userId')
    if user_id:
        try:
            user_id = int(user_id)
        except:
            return {"error": "invalid user id"}, 400
        search_parameters["userId"] = user_id
    
    project_name = query_parameters.get('projectName')
    if project_name:
        search_parameters["projectName"] = project_name
    
    timestamp = query_parameters.get('timestamp')
    if timestamp:
        search_parameters["timestamp"] = timestamp
    
    objects = query_parameters.get('objects')
    objArray = []
    
    if objects:
        try:
            objArray = [int(obj) for obj in objects]
            search_parameters["objects"] = objArray
        except:
            return {"error": "invalid object Id"}, 400

    return search_parameters, 200

def validate_params_create(query_data):
    project_data = {}
    project_id = query_data.get('projectId')
    if not project_id:
        return {"error": "invalid project id"}, 400
    try:
        project_id = int(project_id)
    except ValueError:
        return {"error": "invalid project id"}, 400
    project_data["_id"] = project_id

    user_id = query_data.get('userId')
    if not user_id:
        return {"error": "invalid user id"}, 400
    try:
        user_id = int(user_id)
    except:
        return {"error": "invalid user id"}, 400
    project_data["userId"] = user_id
    
    project_name = query_data.get('projectName')
    if not project_name:
        return {"error": "invalid project name"}, 400
    project_data["projectName"] = project_name
    
    objects = query_data.get('objects')
    if not objects:
        return {"error": "objects not found in data"}, 400
    obj_desc, code = validate_objects(objects)
    if code == 400 and obj_desc.get("error"):
        obj_desc["error"] =  " ".join([obj_desc["error"], "in ProjectId:", str(project_id)])
        return obj_desc, code
    else:
        project_data["objects"] = obj_desc["insertedIds"]
    
    return project_data, 200



def validate_objects(objects):
    to_create = []
    id_set = []
    for obj in objects:
        obj_desc, code = validate_obj(obj)
        if code == 400:
            return obj_desc, code
        id_set.append(obj_desc["_id"])
        to_create.append(obj_desc)

    response = None
    result = {}
    try :
        response = collection2.insert_many(to_create, False)
    except errors.BulkWriteError as bwe:
        result["writeErrors"] = bwe.details['writeErrors']
        #return result, 400
        
    result["insertedIds"] = id_set
    return result, 200

def validate_obj(obj):
    result = {}
    obj_id = obj.get("id")
    if not obj_id:
        return {"error": "invalid object id"}, 400
    try:
        obj_id = int(obj_id)
    except ValueError:
        return {"error": "invalid object id"}, 400
    result["_id"] = obj_id

    obj_name = obj.get("name")
    if not obj_name:
        return {"error": "invalid object name "}, 400
    result["objectName"] = obj_name
    
    obj_length = obj.get("length")
    if not obj_length:
        return {"error": ''.join(["invalid object length at object id: ", str(obj_id)])}, 400
    
    try:
        obj_length = float(obj_length)
    except ValueError:
        return {"error": ''.join(["invalid object length at object id: ", str(obj_id)])}, 400
    result["objectLength"] = obj_length

    obj_height = obj.get("height")
    if not obj_height:
        {"error": ''.join(["invalid object height at object id: ", str(obj_id)])}, 400
    
    try:
        obj_height = float(obj_height)  
    except ValueError:
        return {"error": ''.join(["invalid object height at object id: ", str(obj_id)])}, 400
    result["objectHeight"] = obj_height

    obj_width = obj.get("width")
    if not obj_width:
        return {"error": ''.join(["invalid object width at id: ", str(obj_id)])}, 400
    try:
        obj_width = float(obj_width)
    except ValueError:
        return {"error": ''.join(["invalid object width at id: ", str(obj_id)])}, 400
    result["objectWidth"] = obj_width
    
    return result, 200




@app.route('/api/v1/newProject', methods=['POST'])
def api_post_one():
    if not request.is_json:
        return jsonify({"Error": "data not json"}), 400
    
    request_data = request.get_json()
    result, code = validate_params_create(request_data)
    if code == 400:
        return result, code
    timestamp = datetime.now()
    result["timestamp"] = timestamp
    response = None
    try:
        response = collection.insert_one(result)
    except errors.WriteError as we:
        if we.details["code"] == 11000:
            return {"error": "duplicate project Id used"}, 400

    return {"inserted Project Id:": response.inserted_id}, code


@app.route('/api/v1/newProjects', methods=['POST'])
def api_post_many():
    if not request.is_json or not request.get_json().get("projects"):
        return {"Error": "data not json or projects field does not exist"}, 400
    
    projects = request.get_json().get("projects")
    request_data= []
    for project in projects:
        result, code = validate_params_create(project)
        timestamp = datetime.now()
        result["timestamp"] = timestamp
        request_data.append(result)

        if code == 400:
            return result, code
    
    response = None
    try:
        response = collection.insert_many(request_data).inserted_ids
    except errors.BulkWriteError as bwe:
        response = {}
        response["writeErrors"] = bwe.details['writeErrors']
        return response, 400

    return {"insertedId": response}, 200

@app.route('/api/v1/changeProject', methods=['POST'])
def api_update_one():
    if not request.is_json:
        return {"Error": "data not json"}, 400
    query_parameters = request.args
    update_filter, code = validate_parameters(query_parameters)
    if code == 400:
        update_filter["error"] = " ".join([update_filter["error"], "in filter"])
        return update_filter["error"], code
    
    request_data = request.get_json()
    set_to, code = validate_parameters(request_data)
    if code == 400:
        set_to["error"] = " ".join([update_filter["error"], "in value to be changed to"])
        return set_to["error"], code
    response = None
    try:
        response = collection.update_one(update_filter, {"$set": set_to}, upsert=False)
    except errors.WriteError as we:
        return {"error": we.details["errmsg"]}, 400
        # if we.details["code"] == 11000:
        #     return {"error": "duplicate project Id used"}, 400

    return {"matchedCount:": response.matched_count, "modifiedCount": response.modified_count}, 200

@app.route('/api/v1/changeProjects', methods=['POST'])
def api_update_many():
    if not request.is_json:
        return {"Error": "data not json"}, 400
    query_parameters = request.args
    update_filter, code = validate_parameters(query_parameters)
    if code == 400:
        update_filter["error"] = " ".join([update_filter["error"], "in filter"])
        return update_filter["error"], code
    
    request_data = request.get_json()
    set_to, code = validate_parameters(request_data)
    if code == 400:
        set_to["error"] = " ".join([update_filter["error"], "in value to be changed to"])
        return set_to["error"], code
    response = None
    try:
        response = collection.update_many(update_filter, {"$set": set_to}, upsert=False)
    except errors.WriteError as we:
        return {"error": we.details["errmsg"]}, 400

    return {"matchedCount:": response.matched_count, "modifiedCount": response.modified_count}, 200


@app.route('/api/v1/eraseProject', methods=['DELETE'])
def api_delete_one():
    query_parameters = request.args
    update_filter, code = validate_parameters(query_parameters)
    if code == 400:
        update_filter["error"] = " ".join([update_filter["error"], "in filter"])
        return update_filter["error"], code
    
    response = None
    try:
        response = collection.delete_one(update_filter)
    except errors.WriteError as we:
        return {"error": we.details["errmsg"]}, 400

    return {"matchedCount:": response.deleted_count}, 200

@app.route('/api/v1/eraseProjects', methods=['DELETE'])
def api_delete_many():
    query_parameters = request.args
    update_filter, code = validate_parameters(query_parameters)
    if code == 400:
        update_filter["error"] = " ".join([update_filter["error"], "in filter"])
        return update_filter["error"], code
    
    response = None
    try:
        response = collection.delete_many(update_filter)
    except errors.WriteError as we:
        return {"error": we.details["errmsg"]}, 400

    return {"matchedCount:": response.deleted_count}, 200



@app.errorhandler(404)
def page_not_found(e):
    return "page not found", 404






app.run()