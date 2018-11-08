




















































































































































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





















































































































































############################################################################################





































###################################################