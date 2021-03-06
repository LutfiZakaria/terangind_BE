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
#################################################################
Base = declarative_base()

app = Flask(__name__)
# CORS(app, resources={r"*": {"origin" : "*"}})
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:terangin123@terangin.cldtouwshewk.ap-southeast-1.rds.amazonaws.com:3306/terangin'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@127.0.0.1/terangin_baru'
app.config['JWT_SECRET_KEY'] = 'terangin-secret-key'


db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)
jwt = JWTManager(app)

api = Api(app)


class User(db.Model):
	UserID = db.Column(db.Integer, primary_key= True)
	Username = db.Column(db.String(255), unique= True, nullable= False)
	Email = db.Column(db.String(255), unique= True, nullable= False)
	Password = db.Column(db.String(255), nullable= False)
	UrlPict = db.Column(db.String(255), default="https://pixabay.com/en/blank-profile-picture-mystery-man-973460/")
	Status = db.Column(db.Integer, default=3)
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
	user_UserID = db.Column(db.Integer, db.ForeignKey('user.UserID', ondelete='CASCADE'), nullable=False)
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
	posting_PostID = db.Column(db.Integer, db.ForeignKey('posting.PostID', ondelete='CASCADE'), nullable=False)
	user_UserID = db.Column(db.Integer, db.ForeignKey('user.UserID', ondelete='CASCADE'), nullable=False)
	def __repr__(self):
		return '<Comment %r>' % self.CommentID

user_field = {
	"UserID" : fields.Integer,
	"Username" : fields.String,
	"Email" : fields.String,
	"Password" : fields.String,
	"UrlPict" : fields.String,
	"Status" : fields.String,
	"CreatedAt" : fields.String,
	"UpdatedAt" : fields.String,
}

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

comment_field = {
	"CommentID" : fields.Integer,
	"CommentText" : fields.String,
	"UrlComm" : fields.String,
	"Likes" : fields.Integer,
	"Hoax" : fields.Integer,
	"CreatedAt" : fields.String,
	"UpdatedAt" : fields.String,
	"user_UserID" : fields.Integer,
	"posting_PostID" : fields.Integer
}

#########################  CRUD  #########################
class PublicResource(Resource):
	############### get posts and comments for public ##################
	def get(self, id = None):
		if(id != None):
			qry = Posting.query.filter_by(PostID = id)
			posts = marshal(qry.first(), posting_field)

			qry = Comment.query.filter_by(posting_PostID = id)
			comments = marshal(qry.all(), comment_field)

			if posts["Title"] == None:
				return {'status':'Post not Found'}, 404
			
			else:
				postComm = {
					"Post": posts,
					"Comment": comments
				}
				return postComm, 200
		
		parser = reqparse.RequestParser()
		parser.add_argument("p", type= int, location= 'args', default= 1)
		parser.add_argument("rp", type= int, location= 'args', default= 25)
		parser.add_argument("PostID",type= int, help= 'PostID must be an integer', location= 'args')
		parser.add_argument("Title",type= str, help= 'Title must be string type', location= 'args')
		parser.add_argument("Likes",type= str, help= 'Likes must be an integer', location= 'args')
		parser.add_argument("Watch",type= str, help= 'Watch must be string type', location= 'args')
		parser.add_argument("user_UserID",type= int, help= 'user_UserID must be an integer', location= 'args')
		parser.add_argument("orderBy", help= 'invalid orderBy', location= 'args', choices=('PostID', 'Title', 'Likes', 'Watch', 'CreatedAt', 'UpdatedAt', 'user_UserID'))
		parser.add_argument("sort", help= 'invalid sort value', location= 'args', choices=('asc', 'desc'), default = 'asc')

		args = parser.parse_args()

		qry = Posting.query

		if args['p'] == 1:
			offset = 0
		else:
			offset = (args['p'] * args['rp']) - args['rp']
 
		if args["PostID"] != None:
			qry = qry.filter_by(PostID = args["PostID"])
		if args["Title"] != None:
			qry = qry.filter_by(Title = args["Title"])
		if args["Likes"] != None:
			qry = qry.filter_by(Likes = args["Likes"])
		if args["Watch"] != None:
			qry = qry.filter_by(Watch = args["Watch"])
		
		if args['orderBy'] != None:

			if args["orderBy"] == "PostID":
				field_sort = Posting.PostID
			elif args["orderBy"] == "Title":
				field_sort = Posting.Title
			elif args["orderBy"] == "Likes":
				field_sort = Posting.Likes
			elif args["orderBy"] == "Watch":
				field_sort = Posting.Watch
			elif args["orderBy"] == "CreatedAt":
				field_sort = Posting.CreatedAt
			elif args["orderBy"] == "UpdatedAt":
				field_sort = Posting.UpdatedAt
			elif args["orderBy"] == "user_UserID":
				field_sort = Posting.user_UserID

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
			rows.append(marshal(row, posting_field))

		ans["data"] = rows

		return ans, 200
	
class PostResource(Resource):

	@jwt_required
	def get(self,id = None):
		current_user = get_jwt_identity()

		if(id != None):
			qry = Posting.query.filter_by(user_UserID = current_user)
			qry = qry.filter_by(PostID = id)
			posts = marshal(qry.first(), posting_field)
			
			qry = Comment.query.filter_by(posting_PostID = id)
			comments = marshal(qry.all(), comment_field)

			if posts["Title"] == None:
				return {'status': 'Post not found!'}, 404

			else:
				postComm = {
					"Post": posts,
					"Comment": comments
				}
				return postComm, 200

		parser = reqparse.RequestParser()
		parser.add_argument("p", type= int, location= 'args', default= 1)
		parser.add_argument("rp", type= int, location= 'args', default= 5)
		parser.add_argument("PostID",type= int, help= 'PostID must be an integer', location= 'args')
		parser.add_argument("Title",type= str, help= 'Title must be string type', location= 'args')
		parser.add_argument("Likes",type= str, help= 'Likes must be an integer', location= 'args')
		parser.add_argument("Watch",type= str, help= 'Watch must be string type', location= 'args')
		parser.add_argument("user_UserID",type= int, help= 'user_UserID must be an integer', location= 'args')
		parser.add_argument("orderBy", help= 'invalid orderBy', location= 'args', choices=('PostID', 'Title', 'Likes', 'Watch', 'CreatedAt', 'UpdatedAt', 'user_UserID'))
		parser.add_argument("sort", help= 'invalid sort value', location= 'args', choices=('asc', 'desc'), default = 'asc')

		args = parser.parse_args()

		qry = Posting.query.filter_by(user_UserID = current_user)

		if args['p'] == 1:
			offset = 0
		else:
			offset = (args['p'] * args['rp']) - args['rp']
 
		if args["PostID"] != None:
			qry = qry.filter_by(PostID = args["PostID"])
		if args["Title"] != None:
			qry = qry.filter_by(Title = args["Title"])
		if args["Likes"] != None:
			qry = qry.filter_by(Likes = args["Likes"])
		if args["Watch"] != None:
			qry = qry.filter_by(Watch = args["Watch"])
		
		if args['orderBy'] != None:

			if args["orderBy"] == "PostID":
				field_sort = Posting.PostID
			elif args["orderBy"] == "Title":
				field_sort = Posting.Title
			elif args["orderBy"] == "Likes":
				field_sort = Posting.Likes
			elif args["orderBy"] == "Watch":
				field_sort = Posting.Watch
			elif args["orderBy"] == "CreatedAt":
				field_sort = Posting.CreatedAt
			elif args["orderBy"] == "UpdatedAt":
				field_sort = Posting.UpdatedAt
			elif args["orderBy"] == "user_UserID":
				field_sort = Posting.user_UserID

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
			rows.append(marshal(row, posting_field))

		ans["data"] = rows

		return ans, 200

	@jwt_required
	def post(self):
		parser = reqparse.RequestParser()
		parser.add_argument("Title",type= str, help= 'Title must be string type', location= 'json', required= True)
		parser.add_argument("PostText",type= str, help= 'PostText must be string type', location= 'json', required= True)
		parser.add_argument("Url",type= str, help= 'Url must be string type', location= 'json')
		args = parser.parse_args()
		current_user = get_jwt_identity()
		
		data = Posting(
				Title = args["Title"],
				PostText = args["PostText"],
				Url = args["Url"],
				user_UserID = current_user
			)

		db.session.add(data)
		db.session.commit()
		qry = Posting.query.filter_by( Title= args['Title']).first()
		rows = marshal(qry,posting_field)
		return  rows , 200

	@jwt_required
	def put(self, id):
		current_user = get_jwt_identity()

		data = Posting.query.filter_by(user_UserID = current_user, PostID = id).first()

		if(data == None): 
			return {'status': 'Post not found!'}, 404

		parser = reqparse.RequestParser()
		parser.add_argument("Title",type= str, help= 'Title must be string type', location= 'json', required= True)
		parser.add_argument("PostText",type= str, help= 'PostText must be string type', location= 'json', required= True)
		parser.add_argument("Url",type= str, help= 'Url must be string type', location= 'json')
		args = parser.parse_args()
		
		if args["Title"] != None:
			data.Title= args["Title"]
		if args["PostText"] != None:
			data.PostText= args["PostText"]
		if args["Url"] != None:
			data.Url= args["Url"]
		
		data.UpdatedAt = db.func.current_timestamp()
		data.user_UserID= current_user

		db.session.add(data)
		db.session.commit()

		qry = Posting.query.filter_by( Title= args['Title']).first()
		rows = marshal(qry,posting_field)
		return  rows, 200
		
	@jwt_required
	def delete(self,id):
		current_user = get_jwt_identity()
		data = Posting.query.filter_by(user_UserID = current_user, PostID = id).first()

		if(data == None): 
			return {'status': 'Post not found!'}, 404

		db.session.delete(data)
		db.session.commit()
		return { 'Status': "Your post has been deleted!"} , 200

class UserResource(Resource):
	
	def get(self,id=None):
		if (id!= None):
			qry=User.query.filter_by(UserID = id)

			rows = marshal(qry.first(), user_field)
			if rows["Username"] == None:
				return {'status':'User not Found'}, 404
			else:
				return rows,200
		
		qry=User.query
		rows = marshal(qry.all(), user_field)
		return rows,200

	# def post(self):
	# 	parser = reqparse.RequestParser()
	# 	parser.add_argument('Username', type=str, location = 'json',help= 'Username can\'t null and must be string', required = True)
	# 	parser.add_argument('Email', type=str, location = 'json', help= 'Email can\'t null and must be string',required = True)
	# 	parser.add_argument('Password', type=str, location = 'json', help= 'Email can\'t null and must be string', required = True)
	# 	parser.add_argument('Status', type=str, location = 'json',help= 'Email can\'t null and must be string', required = True)
	# 	args = parser.parse_args()
	# 	data = User(Username = args['Username'], Email = args['Email'], Password = args['Password'], Status= args['Status'])
		
	# 	db.session.add(data)
	# 	db.session.commit()
	# 	qry = User.query.filter_by(Username = args['Username']).first()
	# 	rows = marshal(qry,user_field)
	# 	return  rows , 200

	@jwt_required
	def delete(self,id):
		current_user = get_jwt_identity()
		qry = User.query.filter_by(UserID = current_user)
		data = qry.filter_by(UserID = id).first()

		if(data == None): 
			return {'status': 'User not found!'}, 404

		db.session.delete(data)
		db.session.commit()
		return { 'Status': "Your account has been deleted" } , 200


	@jwt_required
	def put(self,id):
		current_user = get_jwt_identity()
		qry = User.query.filter_by(UserID = current_user)
		data = qry.filter_by(UserID = id).first()

		if(data == None): 
			return {'status': 'User not found!'}, 404

		parser = reqparse.RequestParser()
		parser.add_argument('Username', type=str, location = 'json',help= 'Username can\'t null and must be string' )
		parser.add_argument('Email', type=str, location = 'json', help= 'Email can\'t null and must be string')
		parser.add_argument('Password', type=str, location = 'json', help= 'Password can\'t null and must be string')
		parser.add_argument('UrlPict', type=str, location = 'json')

		args = parser.parse_args()

		if args['Username'] != None:
			data.Username = args['Username']
		if args['Email'] != None:
			data.Email = args['Email']
		if args['Password'] != None:
			data.Password = args['Password']
		if args['UrlPict'] != None:
			data.UrlPict = args['UrlPict']
		
		# Time stamp untuk Update
		data.UpdatedAt= db.func.current_timestamp()
		db.session.commit()

		qry = User.query.filter_by(UserID = current_user).first()
		rows = marshal(qry,user_field)
		return  rows , 200

class CommentResource(Resource):
	def get(self, id):
		qry=Comment.query.filter_by(CommentID = id)

		rows = marshal(qry.first(), comment_field)
		if rows["CommentText"] == None:
			return {'status':'Comment not Found'}, 404
		else:
			return rows,200

	@jwt_required
	def post(self):
		current_user = get_jwt_identity()

		parser = reqparse.RequestParser()
		parser.add_argument('CommentText', type=str, location = 'json',help= 'CommentText can\'t null and must be string', required = True)
		parser.add_argument('UrlComm', type=str, location = 'json', help= 'UrlComm can\'t null and must be string')
		parser.add_argument('Hoax', type=int, location = 'json',help= 'UrlComm can\'t null and must be integer type', required = True)
		parser.add_argument('posting_PostID', type=int, location = 'json',help= 'UrlComm can\'t null and must be string', required = True)
		args = parser.parse_args()

		data = Comment(
			CommentText = args['CommentText'],
			UrlComm = args['UrlComm'],
			Hoax= args['Hoax'],
			user_UserID = current_user,
			posting_PostID= args['posting_PostID']
			)
		
		db.session.add(data)
		db.session.commit()
		qry = Comment.query.filter_by(user_UserID = current_user, posting_PostID= args['posting_PostID']).first()
		rows = marshal(qry,comment_field)
		return  rows , 200

	@jwt_required
	def delete(self,id):
		current_user = get_jwt_identity()
		data = Comment.query.filter_by(user_UserID = current_user, CommentID = id).first()

		if(data == None): 
			return {'status': 'Comment not found!'}, 404

		db.session.delete(data)
		db.session.commit()
		return { 'status': "Your comment has been deleted" } , 200

	@jwt_required
	def put(self,id):
		current_user = get_jwt_identity()
		data = Comment.query.filter_by(user_UserID = current_user, CommentID = id).first()

		if(data == None): 
			return {'status': 'Comment not found!'}, 404

		parser = reqparse.RequestParser()
		parser.add_argument('CommentText', type=str, location = 'json',help= 'CommentText can\'t null and must be string')
		parser.add_argument('UrlComm', type=str, location = 'json', help= 'UrlComm can\'t null and must be string')
		parser.add_argument('Hoax', type=int, location = 'json',help= 'UrlComm can\'t null and must be string')
		args = parser.parse_args()

		if args['CommentText'] != None:
			data.CommentText = args['CommentText']
		if args['UrlComm'] != None:
			data.UrlComm = args['UrlComm']
		if args['Hoax'] != None:
			data.Hoax = args['Hoax']
		# Time stamp untuk Update
		data.UpdatedAt= db.func.current_timestamp()
		data.user_UserID= current_user

		db.session.add(data)
		db.session.commit()

		qry = Comment.query.filter_by( CommentText= args['CommentText']).first()
		rows = marshal(qry,comment_field)
		return  rows , 200
# ################ Login Resource for take a Token ####################
class LoginResource(Resource):

	def post(self):
		parser = reqparse.RequestParser()
		parser.add_argument('Username', location= 'json', required= True)
		parser.add_argument('Password', location= 'json', required= True)

		args = parser.parse_args()

		qry = User.query.filter_by( Username= args['Username'], Password= args['Password']).first()
		
		if qry == None:
			return {"status": "UNAUTHORIZED"}, 401
		
		token = create_access_token(identity= qry.UserID, expires_delta = datetime.timedelta(days=1))

		return {"token": token}, 200

class RegisterResource(Resource):

	def post(self):
		parser = reqparse.RequestParser()
		parser.add_argument('Username', type=str, location = 'json',help= 'Username can\'t null and must be string', required = True)
		parser.add_argument('Email', type=str, location = 'json', help= 'Email can\'t null and must be string',required = True)
		parser.add_argument('Password', type=str, location = 'json', help= 'Password can\'t null and must be string', required = True)
		parser.add_argument('UrlPict', type=str, location = 'json')		
		args = parser.parse_args()
		data = User(Username = args['Username'], Email = args['Email'], Password = args['Password'], UrlPict = args['UrlPict'])
		
		db.session.add(data)
		db.session.commit()
		qry = User.query.filter_by(Username = args['Username']).first()
		rows = marshal(qry,user_field)
		return  rows , 200


###################### Start of Endpoint ##############################
# Endpoints for Public
api.add_resource(PublicResource, '/api/public/posts','/api/public/post/<int:id>')
api.add_resource(PostResource, '/api/users/posts', '/api/users/post/<int:id>')
api.add_resource(UserResource, '/api/users', '/api/user/<int:id>')
api.add_resource(LoginResource, '/api/login')
api.add_resource(RegisterResource, '/api/signup')
api.add_resource(CommentResource, '/api/comment/<int:id>','/api/comment')
############ Finish of Endpoint ##########################################

########### Handling override Message for consistently ##############
@jwt.expired_token_loader
def my_expired_token_callback():
	return json.dumps({"message":"EXPIRED TOKEN"})\
	,401 \
	,{'Content-Type': 'application/json'}

if __name__ == "__main__":
	try:
		if sys.argv[1] == 'db':
			manager.run()
	except IndexError as identifier:
		app.run(debug=True, host='0.0.0.0', port=5000)