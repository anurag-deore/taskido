from flask import Flask,render_template
from flask_pymongo import PyMongo
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import jsonify,request
from flask_jwt_extended import JWTManager, jwt_required, create_access_token,verify_jwt_in_request
from werkzeug.security import generate_password_hash,check_password_hash
from flask_cors import CORS

app = Flask(__name__)
cors =CORS(app, resources={r"*": {"origins": "*"}})
app.secret_key = "security"

app.config["MONGO_URI"] = "mongodb+srv://Anurag:Deore@todo-637wb.gcp.mongodb.net/test"

mongo = PyMongo(app)
jwt = JWTManager(app)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False;

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['POST'])
def register():
    json = request.json
    name = json['name']
    email = json['email']
    pwd = json['password']
    user = mongo.db.users.find_one({'email':email})
    if user:
        return jsonify(message = email+" already exists. <a class='text-danger font-weight-bold' href='login.html'><u>Login</a></u> to continue."), 409
    else:
        try:
            _hashed_password = generate_password_hash(pwd)
            id = mongo.db.users.insert_one({'name':name,'email':email,'password':_hashed_password,'todos':[]})
            return jsonify(register=True), 200
        except:
            return jsonify(register=False), 500


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    user = mongo.db.users.find_one({'email':email})
    if user:
        if check_password_hash(user['password'],password):
            access_token = create_access_token(identity=email)
            return jsonify(message = "Login succeeded!", access_token=access_token,user=str(user['_id']))
        else:
            return jsonify(message = "Invalid email or Password",invalid='True'), 401
    else:
        return jsonify(message= email+" not found.<br> Please <u><a href='register.html' class='font-weight-bold text-danger link'>Register</a></u> to continue",invalid='True'), 401


@app.route('/verify')
@jwt_required
def verify():
    verify_jwt_in_request()
    return jsonify(message = True)

@app.route('/users')
@jwt_required
def users():
    user = mongo.db.users.find({},{ '_id': 0, 'email': 1 })
    return dumps(user), 200


@app.route('/user/<id>')
@jwt_required
def user(id):
    user = mongo.db.users.find_one({'_id':ObjectId(id)})
    return dumps(user), 200


@app.route('/user_update/<uid>', methods=['PUT'])
@jwt_required
def user_update(uid):
    id=uid
    user = mongo.db.users.find_one({'_id':ObjectId(id)})
    if user:
        name = request.json['name']
        email = request.json['email']
        pwd = request.json['password']
        if name and email and pwd and request.method == 'PUT':
            _hashed_password = generate_password_hash(pwd)
            mongo.db.users.update_one({'_id':ObjectId(id['$oid']) if '$oid' in id else ObjectId(id)},
            {'$set':{
                'name':name,
                'email':email,
                'password':_hashed_password,
                }})
        return "UserId "+ id +" updated sucessfully", 200
    else:
        return "User not found. Cannot Perform Operation", 404


@app.route('/user_delete/<id>', methods=['DELETE'])
@jwt_required
def user_delete(id):
    user = mongo.db.users.find_one({'_id':ObjectId(id)})
    if user:
        mongo.db.users.delete_one({'_id':ObjectId(id)})
        return 'User Deleted Successfully', 200
    else:
        return "User not found. Cannot Delete", 404

@app.route('/todos/<uid>')
@jwt_required
def gettodos(uid):
    user = mongo.db.users.find_one({'_id':ObjectId(uid)})
    if user:
        return dumps(user['todos']), 200
    else:
        return jsonify(error="Unauthorized User !"), 401

@app.route('/todo/add/<uid>',  methods=['POST'])
@jwt_required
def todo_add(uid):
    user = mongo.db.users.find_one({'_id':ObjectId(uid)})
    if user:
        mongo.db.users.update_one( {"_id": ObjectId(uid)}, {'$push':{ 'todos':
                {   '_id': ObjectId(),
                    "task":request.json['tasktitle'],
                    "date":request.json['date'],
                    "label":request.json['tasklabel'], 
                    "priority":request.json['importance'],
                    "archive": False, 
                    "deleted": False, 
                    "completed": False, 
                    "deadline_date":request.json["deadline_date"], 
                    "deadline_time":request.json["deadline_time"],
                } 
            }
        })
        todos = mongo.db.users.find_one({'_id':ObjectId(uid)},{'todos':1,'_id':0})
        return dumps(todos['todos']), 200
    else:
        return jsonify(error="Unauthorized User !"), 401


@app.route('/todos_mark_completed/<id>/<tid>')
@jwt_required
def todos_mark_completed(id,tid):
    todo = mongo.db.users.find_one({ "_id":ObjectId(id)},{'_id': 0, 'todos': {'$elemMatch': {"_id": ObjectId(tid)}}})
    if todo:
        print(not todo['todos'][0]['completed'])
        mongo.db.users.update_one(
                { "_id":ObjectId(id),"todos._id": ObjectId(tid) }, 
                { "$set": { "todos.$.completed": not todo['todos'][0]['completed'] } }
            )
        todos = mongo.db.users.find_one({'_id':ObjectId(id)},{'todos':1,'_id':0})
        return dumps(todos['todos']), 200
    else:
        return jsonify(error="Unauthorized User !"), 401


@app.route('/todo_archive/<id>/<tid>')
@jwt_required
def todo_archive(id,tid):
    todo = mongo.db.users.find_one({ "_id":ObjectId(id)},{'_id': 0, 'todos': {'$elemMatch': {"_id": ObjectId(tid)}}})
    if todo:
        print(not todo['todos'][0]['archive'])
        mongo.db.users.update_one(
                { "_id":ObjectId(id),"todos._id": ObjectId(tid) }, 
                { "$set": { "todos.$.archive": not todo['todos'][0]['archive'] } }
            )
        todos = mongo.db.users.find_one({'_id':ObjectId(id)},{'todos':1,'_id':0})
        return dumps(todos['todos']), 200
    else:
        return jsonify(error="Unauthorized User !"), 401



@app.route('/todo_deleted/<id>/<tid>')
@jwt_required
def todo_deleted(id,tid):
    todo = mongo.db.users.find_one({ "_id":ObjectId(id)},{'_id': 0, 'todos': {'$elemMatch': {"_id": ObjectId(tid)}}})
    if todo:
        print(not todo['todos'][0]['deleted'])
        mongo.db.users.update_one(
                { "_id":ObjectId(id),"todos._id": ObjectId(tid) }, 
                { "$set": { "todos.$.deleted": not todo['todos'][0]['deleted'] } }
            )
        todos = mongo.db.users.find_one({'_id':ObjectId(id)},{'todos':1,'_id':0})
        return dumps(todos['todos']), 200
    else:
        return jsonify(error="Unauthorized User !"), 401


@app.route('/todos_completed_list/<id>')
@jwt_required
def todos_completed_list(id):
    d = mongo.db.users.find({ "todos.priority":"Low"}, {'_id':0, 'todos': 1})
    if d:
        for todo in d[0]['todos']:
            print(todo)
        return jsonify(found = 'find'), 200
    else:
        return jsonify(error="Unauthorized User !"), 401



@app.route('/todo/<id>')
@jwt_required
def list(id):
    list = mongo.db.list.find_one({'_id':ObjectId(id)})
    return dumps(list), 200


@app.route('/todo_update/<uid>', methods=['PUT'])
@jwt_required
def list_update(uid):
    id=uid
    list = mongo.db.lists.find_one({'_id':ObjectId(id)})
    if list:
        listname = request.json['listname']
        if listname and request.method == 'PUT':
            mongo.db.lists.update_one({'_id':ObjectId(id['$oid']) if '$oid' in id else ObjectId(id)},
            {'$set':{
                'name':listname,
                }})
        return "list - "+ id +" updated sucessfully", 200
    else:
        return "List not found. Cannot Perform Operation", 404



@app.route('/todo_delete_completely/<id>/<tid>', methods=['DELETE'])
@jwt_required
def todo_delete_completely(id,tid):
    todo = mongo.db.users.find_one({ "_id":ObjectId(id)},{'_id': 0, 'todos': {'$elemMatch': {"_id": ObjectId(tid)}}})
    if todo:
        mongo.db.users.update_one({'_id':ObjectId(id)},{'$pull': { "todos" : { '_id': ObjectId(tid) } } })
        todos = mongo.db.users.find_one({'_id':ObjectId(id)},{'todos':1,'_id':0})
        return dumps(todos['todos']), 200
    else:
        return "Todo not found. Cannot Delete", 404




# @app.route('/user/add  ', methods=['POST'])
# def add():
#     if request.is_json:
#         name = request.json['name']
#         email = request.json['email']
#         pwd = request.json['password']

#     return jsonify({'name':email,'password':pwd})
    # if name and email and pwd and request.method == 'POST':
    #     _hashed_password = generate_password_hash(pwd)
    #     id = mongo.db.users.insert({'name':name,'email':email,'password':_hashed_password})
    #     return jsonify('User added Successfully'), 200
    # return jsonify('Error inserting data')


if __name__ == "__main__":
    app.run(debug=True)
