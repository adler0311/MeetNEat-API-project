#-*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from models import Base, User, RequestMeal, Proposal, MealDate
from flask import Flask, jsonify, request, url_for, abort, g, render_template
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

from geocode import getGeocodeLocation
from findARestaurant import findARestaurant

from flask.ext.httpauth import HTTPBasicAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import session as login_session


from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from flask import make_response
import requests
import json

engine = create_engine('sqlite:///MeetNEat.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)

auth = HTTPBasicAuth()
limiter = Limiter(app, key_func=get_remote_address, default_limits=["200 per day", "20 per hour"])

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


@auth.verify_password
def verify_password(email_or_token, password):
	user_id = User.verify_auth_token(email_or_token)
	if user_id:
		user = session.query(User).filter_by(id=user_id).one()
	else:
		user = session.query(User).filter_by(email = email_or_token).first()
		if not user or not user.verify_password(password):
			return False
	g.user = user
	return True


@app.route('/api/v1/token')
@auth.login_required
def get_auth_token():
	token = g.user.generate_auth_token()
	user_id = User.verify_auth_token(token)
	return jsonify({'token': token.decode('ascii')})


@app.route('/')
def hello_world():
	return "Hello World!"


@app.route('/api/v1/<provider>/login', methods=['POST'])
def login(provider):
	auth_code = request.json.get('auth_code')
	if provider == 'google':
		try:
			oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
			oauth_flow.redirect_uri = 'postmessage'
			credentials = oauth_flow.step2_exchange(auth_code)
		except FlowExchangeError:
			response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
			response.headers['Content-Type'] = 'application/json'
			return response

		access_token = credentials.access_token
		url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
		h = httplib2.Http()
		result = json.loads(h.request(url, 'GET')[1])

		if result.get('error') is not None:
			response = make_response(json.dumps(result.get('error')), 500)
			response.headers['Content-Type'] = 'application/json'

		# get user info
		h = httplib2.Http()
		userinfo_url =  "https://www.googleapis.com/oauth2/v1/userinfo"
		params = {'access_token': credentials.access_token, 'alt':'json'}
		answer = requests.get(userinfo_url, params=params)

		data = answer.json()
		email = data['email']
		picture = data['picture']

		# store data to login_session of flask for later use.
		login_session['credentials'] = credentials.access_token
		login_session['provider'] = 'google'
		login_session['email'] = email
		login_session['picture'] = picture


		user = session.query(User).filter_by(email=email).first()
		if not user:
			user = User(email=email, picture=picture)
			session.add(user)
			session.commit()

		token = user.generate_auth_token(600)

		login_session['token'] = token

		return jsonify({'token': token.decode('ascii')})

	else:
		return 'Unrecognized Provider'


# Not Implemented Yet.
@app.route('/api/v1/<provider>/logout', methods=['POST'])
@auth.login_required
def logout(provider):
	if provider == 'google':
		# google API에서 토큰을 취소하기

		return jsonify({'token': g.token, 'user_id': g.user_id})

		credentials = login_session.get('credentials')
		if credentials is None:
			response = make_response(json.dumps('Current user not connected.'), 401)
			response.headers['Content-Type'] = 'applcation/json'
			return response

		access_token = credentials
		url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
		h = httplib2.Http()
		result = h.request(url, 'GET')[0]
		if result['status'] != 200:
			response = make_response(json.dumps('Failed to revoke token for given user'), 400)
			response.headers['Content-Type'] = 'application/json'
			return response

		del login_session['credentials']
		del login_session['provider']
		del login_session['email']
		del login_session['picture']
		del login_session['token']

		return 'Successfuly logged out.'

	else:
		return 'Unrecognized Provider'

@app.route('/api/v1/users', methods=['GET', 'POST'])
def users():
	if request.method == 'GET':
		users = session.query(User).all()
		return jsonify(users = [u.serialize for u in users])

	elif request.method == 'POST':
		email = request.json.get('email')
		picture = request.json.get('picture')
		password = request.json.get('password')

		if email is None or password is None:
			print "이메일 혹은 비밀번호를 입력해주세요."
			abort(400)

		if session.query(User).filter_by(email=email).first() is not None:
			print "사용자가 이미 존재합니다."
			return jsonify({'message': 'user is already exists'})

		user = User(email=email, picture=picture)
		user.hash_password(password)
		session.add(user)
		session.commit()

		return jsonify({'user email': user.email}, 201)


@app.route('/api/v1/users/<int:user_id>', methods=['GET','PUT','DELETE'])
@auth.login_required
def specificUser(user_id):
	user = session.query(User).filter_by(id=user_id).first()
	if not user:
		abort(400)

	if request.method == 'GET':
		return jsonify({'user email': user.email,
						'picture': user.picture})

	elif request.method == 'PUT':
		email = request.json.get('email')
		password = request.json.get('password')
		picture = request.json.get('picture')

		if email:
			user.email = email
		if password:
			user.hash_password(password)
		if picture:
			user.picture = picture

		session.commit()

		return jsonify({'email': user.email,
						'picture': user.picture})
	elif request.method == 'DELETE':
		session.delete(user)
		session.commit()
		return "user deleted"


@app.route('/api/v1/requests', methods=['GET', 'POST'])
@auth.login_required
def requestsMeal():
	if request.method == 'GET':
		mealRequests = session.query(RequestMeal).all()
		return jsonify(requests = [r.serialize() for r in mealRequests])

	elif request.method == "POST":
		meal_type = request.json.get("meal_type")
		location_string = request.json.get("location_string")
		meal_time = request.json.get("meal_time")
		
		user_id = User.verify_auth_token(token)
		filled = False
		lat, lon = getGeocodeLocation(location_string)
		

		if meal_type is None or location_string is None or meal_time is None:
			# print "식사 타입 혹은 지역 정보, 혹은 식사 시간은 입력해주세요."
			abort(400)

	mealRequest = RequestMeal(user_id = user_id, meal_type=meal_type, location_string=location_string,
							latitude=str(lat), longditude=str(lon), filled=filled, meal_time=meal_time)
	session.add(mealRequest)
	session.commit()

	return jsonify({'user_id': mealRequest.user_id, 'meal_type': mealRequest.meal_type,
					'location_string':mealRequest.location_string, 'latitude':mealRequest.latitude,
					'longditude': mealRequest.longditude, 'meal_time': mealRequest.meal_time,
					'filled': filled}, 201)


@app.route('/api/v1/requests/<int:request_id>', methods=['GET', 'PUT', 'DELETE'])
@auth.login_required
def specificRequestMeal(request_id):
	mealRequest = session.query(RequestMeal).filter_by(id=request_id).first()

	if request.method == 'GET':
		return jsonify({'user_id': mealRequest.user_id, 'meal_type': mealRequest.meal_type,
						'location_string':mealRequest.location_string, 'latitude':mealRequest.latitude,
						'longditude': mealRequest.longditude, 'meal_time': mealRequest.meal_time,
						'filled': filled}, 201)
	
	elif request.method == 'PUT':
		meal_type = request.json.get("meal_type")
		location_string = request.json.get("location_string")
		meal_time = request.json.get("meal_time")

		if meal_type:
			mealRequest.meal_type = meal_type
		if location_string:
			mealRequest.location_string = location_string
			latitude, longditude = getGeocodeLocation(location_string)
			mealRequest.latitude = latitude
			mealRequest.longditude = longditude
		if meal_time:
			mealRequest.meal_time = meal_time

		session.commit()

		return jsonify({'user_id': mealRequest.user_id, 'meal_type': mealRequest.meal_type,
						'location_string':mealRequest.location_string, 'latitude':mealRequest.latitude,
						'longditude': mealRequest.longditude, 'meal_time': mealRequest.meal_time,
						'filled': filled}, 201)

	elif request.method == 'DELETE':
		session.delete(mealRequest)
		session.commit()

		return 'The request deleted'


@app.route('/api/v1/proposals', methods=['GET', 'POST'])
@auth.login_required
def proposals():
	if request.method == 'GET':
		proposals = session.query(Proposal).all()
		return jsonify(proposals = [p.serialize for p in proposals])

	elif request.method == 'POST':
		user_id = User.verify_auth_token(token)
		user_proposed_from = session.query(User).filter_by(id=user_id).first().email
		user_proposed_to = request.json.get('user_proposed_to')
		request_id = request.json.get('request_id')
		filled = False

		if user_proposed_from is None or user_proposed_to is None or request_id is None:
			print "제안받은 유저, 제안한 유저 혹은 요청 아이디를 입력하세요"
			abort(400)

		if session.query(Proposal).filter_by(request_id=request_id).first() is not None:
			print "요청 아이디가 존재하지 않습니다. 다시 확인해주세요."
			return jsonify({'message': 'the request_id is not exist'})

		proposal = Proposal(user_proposed_from=user_proposed_from, user_proposed_to=user_proposed_to,
							request_id=request_id, filled=filled)
		session.add(proposal)
		session.commit()

		return jsonify({'id': proposal.id, 'user_proposed_to': proposal.user_proposed_to,
						'user_proposed_from': proposal.user_proposed_from,
						'request_id': proposal.request_id, 'filled': proposal.filled}, 201)


@app.route('/api/v1/proposals/<int:proposal_id>', methods = ['GET', 'PUT', 'DELETE'])
@auth.login_required
def specificProposal(proposal_id):
	proposal = session.query(Proposal).filter_by(id=proposal_id).first()

	if request.method == 'GET':
		return jsonify({'id': proposal.id, 'user_proposed_to': proposal.user_proposed_to,
								'user_proposed_from': proposal.user_proposed_from,
								'request_id': proposal.request_id, 'filled': proposal.filled})
	
	elif request.method == 'PUT':
		user_proposed_to = request.json.get('user_proposed_to')
		user_proposed_from = request.json.get('user_proposed_from')
		request_id = request.json.get('request_id')
		filled = request.json.get('filled')

		if user_proposed_to:
			proposal.user_proposed_to = user_proposed_to
		if user_proposed_from:
			proposal.user_proposed_from = user_proposed_from
		if request_id:
			proposal.request_id = request_id
		if filled:
			proposal.filled = filled

		session.commit()

		return jsonify({'id': proposal.id, 'user_proposed_to': proposal.user_proposed_to,
								'user_proposed_from': proposal.user_proposed_from,
								'request_id': proposal.request_id, 'filled': proposal.filled})
	
	elif request.method == 'DELETE':
		session.delete(proposal)
		session.commit()
		return "Deletes a specific proposal"


@app.route('/api/v1/dates', methods=['GET','POST'])
@auth.login_required
def dates():
	user_id = User.verify_auth_token(token)
	user_1 = session.query(User).filter_by(id=user_id).first().email
		
	if request.method == 'GET':
		dates = session.query(MealDate).all()
		return jsonify(dates = [d.serialize for d in dates])

	elif request.method == 'POST':
		user_2 = request.json.get('user_2')
		meal_time = request.json.get('meal_time')

		proposal =  session.query(Proposal).filter_by(user_proposed_to = user_2).filter_by(user_proposed_from = user_1).first()
		requestMeal = session.query(RequestMeal).filter_by(id=proposal.request_id).first()

		meal_type = requestMeal.meal_type
		location_string = requestMeal.location_string

		restaurantInfo = findARestaurant(meal_type, location_string) # name, address, picture of the restaurant.

		restaurant_name = restaurantInfo['name']
		restaurant_address = restaurantInfo['address']
		restaurant_picture = restaurantInfo['picture']

		if user_2 is None or meal_time is None:
			print "사용자와 식사 시간을 입력해주세요."
			abort(400)
		if restaurant_name is None or restaurant_address is None:
			print "레스토랑 정보를 입력해주세요"
			abort(400)

		dates = MealDate(user_1=user_1, user_2=user_2, restaurant_name=restaurant_name,
						restaurant_address=restaurant_address,
						restaurant_picture=restaurant_picture, meal_time=meal_time)
		session.add(dates)
		session.commit()

		return jsonify({'user_1': dates.user_1, 'user_2': dates.user_2,
						'restaurant_name':dates.restaurant_name,
						'restaurant_address':dates.restaurant_address,
						'restaurant_picture':dates.restaurant_picture,
						'meal_time':dates.meal_time})


@app.route('/api/v1/dates/<int:date_id>', methods=['GET', 'PUT', 'DELETE'])
@auth.login_required
def specificDate(date_id):
	dates = session.query(MealDate).filter_by(id=date_id).first()

	if request.method == 'GET':
		return jsonify({'user_1': dates.user_1, 'user_2': dates.user_2,
						'restaurant_name':dates.restaurant_name,
						'restaurant_address':dates.restaurant_address,
						'restaurant_picture':dates.restaurant_picture,
						'meal_time':dates.meal_time})


	elif request.method == 'PUT':
		user_1 = request.json.get('user_1')
		user_2 = request.json.get('user_2')
		restaurant_name = request.json.get('restaurant_name')
		restaurant_address = request.json.get('restaurant_address')
		restaurant_picture = request.json.get('restaurant_picture')
		meal_time = request.json.get('meal_time')

		if user_2:
			dates.user_2 = user_2
		if restaurant_name:
			dates.restaurant_name = restaurant_name
		if restaurant_address:
			dates.restaurant_address = restaurant_address
		if restaurant_picture:
			dates.restaurant_picture = restaurant_picture
		if meal_time:
			dates.meal_time = meal_time

		session.commit()
		return jsonify({'user_1': dates.user_1, 'user_2': dates.user_2,
						'restaurant_name':dates.restaurant_name,
						'restaurant_address':dates.restaurant_address,
						'restaurant_picture':dates.restaurant_picture,
						'meal_time':dates.meal_time})

	elif request.method == 'DELETE':
		session.delete(dates)
		session.commit()
		return "Removes a specific date"


if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.run(debug=True)