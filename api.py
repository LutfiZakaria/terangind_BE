#################################################################

#########################  IMPORT TOOLS #########################
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:terangin123@terangin.cldtouwshewk.ap-southeast-1.rds.amazonaws.com:3306/terangin'
app.config['JWT_SECRET_KEY'] = 'terangin-secret-key'


db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)
jwt = JWTManager(app)

api = Api(app)

#Wrapping untuk fungsi Super admin
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
#Wrapping untuk fungsi user admin
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

#########################  MODEL DECLARATION #########################

# UserPost = db.Table('UserPost',
#     db.Column('User_UserID', db.Integer, db.ForeignKey('user.UserID'), primary_key=True),
#     db.Column('Posting_PostID', db.Integer, db.ForeignKey('posting.PostID'), primary_key=True)
# )

# UserCom = db.Table('UserCom',
#     db.Column('User_UserID', db.Integer, db.ForeignKey('user.UserID'), primary_key=True),
#     db.Column('Comment_CommentID', db.Integer, db.ForeignKey('comment.CommentID'), primary_key=True)
# )

# PostCom = db.Table('PostCom',
#     db.Column('Posting_PostID', db.Integer, db.ForeignKey('posting.PostID'), primary_key=True),
#     db.Column('Comment_CommentID', db.Integer, db.ForeignKey('comment.CommentID'), primary_key=True)
# )

class User(db.Model):
	UserID = db.Column(db.Integer, primary_key= True)
	Username = db.Column(db.String(255), unique= True, nullable= False)
	Email = db.Column(db.String(255), unique= True, nullable= False)
	Password = db.Column(db.String(255), nullable= False)
	Status = db.Column(db.String(50))
	CreatedAt = db.Column(db.DateTime, default= db.func.current_timestamp())
	UpdatedAt = db.Column(db.DateTime, default= db.func.current_timestamp())
	postings = db.relationship('Posting', backref='person', lazy=True)
	comments = db.relationship('Comment', backref='person', lazy=True)
	def __repr__(self):
		return '<User %r>' % self.UserID

class Posting(db.Model):
	PostID = db.Column(db.Integer, primary_key = True)
	Title = db.Column(db.String(255), nullable=False)
	PostText = db.Column(db.Text, nullable = False)
	Url = db.Column(db.String(255))
	Likes = db.Column(db.Integer, default = 0)
	Watch = db.Column(db.Integer, default = 0)
	CreatedAt = db.Column(db.DateTime, default= db.func.current_timestamp())
	UpdatedAt = db.Column(db.DateTime, default= db.func.current_timestamp())
	# UserPost = db.relationship('User', secondary=UserPost, lazy='subquery', backref=db.backref('postings', lazy=True))
	user_UserID = db.Column(db.Integer, db.ForeignKey('user.UserID'), nullable=False)
	def __repr__(self):
		return '<Posting %r>' % self.PostID

class Comment(db.Model):
	CommentID = db.Column(db.Integer, primary_key = True)
	CommentText = db.Column(db.Text, nullable = False)
	UrlComm = db.Column(db.String(255))
	Likes = db.Column(db.Integer, default = 0)
	# Column Hoax terdapat 1 = Yes, 2 = No, 3 = Don't Know
	Hoax = db.Column(db.Integer, default =3)
	CreatedAt = db.Column(db.DateTime, default= db.func.current_timestamp())
	UpdatedAt = db.Column(db.DateTime, default= db.func.current_timestamp())
	# UserCom = db.relationship('User', secondary=UserCom, lazy='subquery', backref=db.backref('comments', lazy=True))
	# PostCom = db.relationship('Post', secondary=PostCom, lazy='subquery', backref=db.backref('comments', lazy=True))
	user_UserID = db.Column(db.Integer, db.ForeignKey('user.UserID'), nullable=False)
	posting_PostID = db.Column(db.Integer, db.ForeignKey('posting.PostID'), nullable=False)
	def __repr__(self):
		return '<Comment %r>' % self.CommentID


#########################  CRUD  #########################

##################  CRUD Endpoint Public  #################

class PublicResource(Resource):
	posting_field = {
		"PostID" : fields.Integer,
		"Title" : fields.String,
		"PostText" : fields.String,
		"Url" : fields.String,
		"Likes" : fields.Integer,
		"Watch" : fields.Integer,
		"CreatedAt" : fields.String,
		"UpdatedAt" : fields.String,
		"user_UserID" : fields.Integer
	}
	def get(self, id = None):
		if(id != None):
			qry = User.query.get(UserID = id)
			if(qry == None):
				return {'status': 'Post not found!'}, 404
			ans = {
				"page": 1,
				"total_page": 1,
				"per_page": 25,
				"data": []
			}

			rows = marshal(qry, self.posting_field)
			ans["data"] = rows
			return ans, 200
		
		parser = reqparse.RequestParser()
		parser.add_argument("p", type= int, location= 'args', default= 1)
		parser.add_argument("rp", type= int, location= 'args', default= 25)
		parser.add_argument("PostID",type= int, help= 'PostID must be an integer', location= 'args')
		parser.add_argument("Likes",type= str, help= 'Likes must be an integer', location= 'args')
		parser.add_argument("orderBy", help= 'invalid orderBy', location= 'args', choices=('PostID', 'Likes', 'CreatedAt', 'UpdatedAt'))
		parser.add_argument("sort", help= 'invalid sort value', location= 'args', choices=('asc', 'desc'), default = 'asc')

		args = parser.parse_args()

		qry = Posting.query

		if args['p'] == 1:
			offset = 0
		else:
			offset = (args['p'] * args['rp']) - args['rp']
 
		if args["PostID"] != None:
			qry = qry.filter_by(PostID = args["PostID"]) 
		if args["Likes"] != None:
			qry = qry.filter_by(Likes = args["Likes"])
		
		if args['orderBy'] != None:

			if args["orderBy"] == "Likes":
				field_sort = Posting.Likes
			elif args["orderBy"] == "category":
				field_sort = Posting.category
			elif args["orderBy"] == "CreatedAt":
				field_sort = Posting.CreatedAt
			elif args["orderBy"] == "UpdatedAt":
				field_sort = Posting.UpdatedAt

			if args['sort'] == 'desc':
				qry = qry.order_by(desc(field_sort))
			   
			else:
				qry = qry.order_by(field_sort)

			rows= qry.count()
			qry =  qry.limit(args['rp']).offset(offset)
			tp = math.ceil(rows / args['rp'])
			
			ans = {
				"page": args['p'],
				"total_page": tp,
				"per_page": args['rp'],
				"data": []
			}

			rows = []
			for row in qry.all():
				rows.append(marshal(row, self.posting_field))

			ans["data"] = rows

			return ans, 200






















































class UserResource(Resource):
	user_field = {
		"UserID" : fields.Integer,
		"Username" : fields.String,
		"Email" : fields.String,
		"Password" : fields.String,
		"Status" : fields.String,
		"CreatedAt" : fields.String,
		"UpdatedAt" : fields.String,
		}

	def get(self,id=None):
		if (id!= None):
			qry=User.query.get(id)
		else :
			return {'status':'User not Found'}, 404
		rows = marshal(qry, self.user_field)
		return rows, 200

	def post(self):
		parser = reqparse.RequestParser()
		parser.add_argument('Username', type=str, location = 'json',help= 'Username can\'t null and must be string', required = True)
		parser.add_argument('Email', type=str, location = 'json', help= 'Email can\'t null and must be string',required = True)
		parser.add_argument('Password', type=str, location = 'json', help= 'Email can\'t null and must be string', required = True)
		parser.add_argument('Status', type=str, location = 'json',help= 'Email can\'t null and must be string', required = True)
		args = parser.parse_args()
		data = User(Username = args['Username'], Email = args['Email'], Password = args['Password'], Status= args['Status'])
		
		db.session.add(data)
		db.session.commit()
		qry = User.query.filter_by(Username = args['Username']).first()
		rows = marshal(qry,self.user_field)
		return  rows , 200

	def delete(self,id=None):
		if (id!= None):
			qry=User.query.get(id)
		else :
			return {'status':'User not Found'}, 404
		db.session.delete(qry)
		db.session.commit()
		qry = User.query.all() # supaya return item yang hilang
		rows = marshal(qry,self.user_field)
		return rows , 200

	def put(self,id=None):
		parser = reqparse.RequestParser()
		parser.add_argument('Username', type=str, location = 'json',help= 'Username can\'t null and must be string' )
		parser.add_argument('Email', type=str, location = 'json', help= 'Email can\'t null and must be string')
		parser.add_argument('Password', type=str, location = 'json', help= 'Email can\'t null and must be string')
		parser.add_argument('Status', type=str, location = 'json',help= 'Email can\'t null and must be string')
		args = parser.parse_args()
		qry = User.query.filter_by(UserID = id).first()
		if args['Username'] != "":
			qry.Username = args['Username']
		if args['Email'] != "":
			qry.Email = args['Email']
		if args['Password'] != "":
			qry.Password = args['Password']
		if args['Status'] != "":
			qry.Status = args['Status']
		
		# Time stamp untuk Update
		qry.UpdatedAt= db.func.current_timestamp()
		db.session.commit()
		rows = marshal(qry,self.user_field)
		return  rows , 200







# ######################## WILAYAH KERJA ZACK #########################
# ################ Login Resource for take a Token ####################
# # class LoginResource(Resource):
# class LoginResource(Resource):
# 	def post(self):
# 		parser = reqparse.RequestParser()
# 		parser.add_argument('secret', location='json', required = True)
# 		args = parser.parse_args()
# 		qry = SignUp.query.filter_by(secret=args['secret']).first()
# 		if qry is None:
# 			return {'status':'UNAUTHORIZED'}, 401
# 		token = create_access_token(identity=qry.secret, expires_delta = datetime.timedelta(days=1))
# 		return {'token':token}, 200
###################### Start of Endpoint ##############################
# Endpoints for Public
api.add_resource(PublicResource, '/api/public/posts', '/api/public/post/<int:id>' )
api.add_resource(UserResource, '/api/user/<int:id>','/api/signup','/api/user/delete/<int:id>')
############ Finish of Endpoint ##########################################

# ########### Handling override Message for consistently ##############
# @jwt.expired_token_loader
# def my_expired_token_callback():
# 	return json.dumps({"message":"EXPIRED TOKEN"})\
# 	,401 \
# 	,{'Content-Type': 'application/json'}

# # ###################### Handling Userclaim in Payload ###################
# @jwt.user_claims_loader
# def add_claim(identity):
# 	qry = SignUp.query.filter_by(secret=identity).first()
# 	val = qry.types
# 	val2 = qry.sign_id
# 	return { 'type': val, 'sign_id':val2}
# @jwt.unauthorized_loader
# def unathorized_message(error_string):
# 	return json.dumps({'message': error_string}), 401, {'Content-Type': 'application/json'}

# # if __name__ == '__main__':
# # 	try:
# # 		if  sys.argv[1] == 'db':
# # 			manager.run()
# # 		else:
# # 			app.run(debug=True, host = '0.0.0.0', port = 5000)
# # 	except  IndexError as p:
# # 		app.run(debug=True, host = '0.0.0.0', port = 5000)












































































































































# ############################################################################################





































# ###################################################

if __name__ == "__main__":
	try:
		if sys.argv[1] == 'db':
			manager.run()
	except IndexError as identifier:
		app.run(debug=True, host='0.0.0.0', port=5000)