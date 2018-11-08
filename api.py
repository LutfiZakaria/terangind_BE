




















































































































































######################## WILAYAH KERJA ZACK #########################
################ Login Resource for take a Token ####################
# class LoginResource(Resource):
class LoginResource(Resource):
	def post(self):
		parser = reqparse.RequestParser()
		parser.add_argument('secret', location='json', required = True)
		args = parser.parse_args()
		qry = SignUp.query.filter_by(secret=args['secret']).first()
		if qry is None:
			return {'status':'UNAUTHORIZED'}, 401
		token = create_access_token(identity=qry.secret, expires_delta = datetime.timedelta(days=1))
		return {'token':token}, 200
###################### Start of Endpoint ##############################







############ Finish of Endpoint ##########################################

########### Handling override Message for consistently ##############
@jwt.expired_token_loader
def my_expired_token_callback():
	return json.dumps({"message":"EXPIRED TOKEN"})\
	,401 \
	,{'Content-Type': 'application/json'}

# ###################### Handling Userclaim in Payload ###################
@jwt.user_claims_loader
def add_claim(identity):
	qry = SignUp.query.filter_by(secret=identity).first()
	val = qry.types
	val2 = qry.sign_id
	return { 'type': val, 'sign_id':val2}
@jwt.unauthorized_loader
def unathorized_message(error_string):
	return json.dumps({'message': error_string}), 401, {'Content-Type': 'application/json'}

if __name__ == '__main__':
	try:
		if  sys.argv[1] == 'db':
			manager.run()
		else:
			app.run(debug=True, host = '0.0.0.0', port = 5000)
	except  IndexError as p:
		app.run(debug=True, host = '0.0.0.0', port = 5000)
#################################################################
from flask import Flask
# from flask_cors import CORS
from flask_restful import Resource, Api, reqparse, marshal, fields

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, insert, ForeignKey, DateTime, distinct, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_jwt_extended import JWTManager, create_access_token, verify_jwt_in_request, get_jwt_claims, jwt_required, get_jwt_identity, get_raw_jwt

from functools import wraps
import sys, json, datetime, math

Base = declarative_base()

app = Flask(__name__)
# CORS(app, resources={r"*": {"origin" : "*"}})
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@127.0.0.1/terangin'
app.config['JWT_SECRET_KEY'] = 'terangin-secret-key'


db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)
jwt = JWTManager(app)

api = Api(app)

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if claims['type'] != 'admin':
            return {'status':'FORBIDDEN'}, 403, {'Content-Type': 'application/json'}
        else:
            return fn(*args, **kwargs)
    return wrapper

def user_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if claims['type'] != 'user':
            return {'status':'FORBIDDEN'}, 403, {'Content-Type': 'application/json'}
        else:
            return fn(*args, **kwargs)
    return wrapper


UserPost = db.Table('UserPost',
    db.Column('User_UserID', db.Integer, db.ForeignKey('user.UserID'), primary_key=True),
    db.Column('Posting_PostID', db.Integer, db.ForeignKey('posting.PostID'), primary_key=True)
)

UserCom = db.Table('UserCom',
    db.Column('User_UserID', db.Integer, db.ForeignKey('user.UserID'), primary_key=True),
    db.Column('Comment_CommentID', db.Integer, db.ForeignKey('comment.CommentID'), primary_key=True)
)

PostCom = db.Table('PostCom',
    db.Column('Posting_PostID', db.Integer, db.ForeignKey('posting.PostID'), primary_key=True),
    db.Column('Comment_CommentID', db.Integer, db.ForeignKey('comment.CommentID'), primary_key=True)
)

class User(db.Model):
    UserID = db.Column(db.Integer, primary_key= True)
    Username = db.Column(db.String(255), unique= True, nullable= False)
    Email = db.Column(db.String(255), unique= True, nullable= False)
    Password = db.Column(db.String(255), nullable= False)
    Status = db.Column(db.String(50))
    CreatedAt = db.Column(db.DateTime, default= db.func.current_timestamp())
    UpdatedAt = db.Column(db.DateTime, default= db.func.current_timestamp())

    def __repr__(self):
        return '<User %r>' % self.UserID

class Posting(db.Model):
    PostID = db.Column(db.Integer, primary_key = True)
    PostText = db.Column(db.Text, nullable = False)
    Likes = db.Column(db.Integer, default = 0)
    createdAt = db.Column(db.DateTime, default= db.func.current_timestamp())
    updatedAt = db.Column(db.DateTime, default= db.func.current_timestamp())
    UserPost = db.relationship('User', secondary=UserPost, lazy='subquery', backref=db.backref('postings', lazy=True))

    def __repr__(self):
        return '<Posting %r>' % self.PostID

class Comment(db.Model):
    CommentID = db.Column(db.Integer, primary_key = True)
    CommentText = db.Column(db.Text, nullable = False)
    Likes = db.Column(db.Integer, default = 0)
    createdAt = db.Column(db.DateTime, default= db.func.current_timestamp())
    updatedAt = db.Column(db.DateTime, default= db.func.current_timestamp())
    UserCom = db.relationship('User', secondary=UserCom, lazy='subquery', backref=db.backref('comments', lazy=True))
    PostCom = db.relationship('Post', secondary=PostCom, lazy='subquery', backref=db.backref('comments', lazy=True))

    def __repr__(self):
        return '<Comment %r>' % self.CommentID











































































































































############################################################################################





































###################################################

if __name__ == "__main__":
    try:
        if sys.argv[1] == 'db':
            manager.run()
    except IndexError as identifier:
        app.run(debug=True, host='0.0.0.0', port=5000)