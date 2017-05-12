from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context
import random, string
from itsdangerous import(TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

Base = declarative_base()
secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key = True)
    email = Column(String)
    picture = Column(String)
    password_hash = Column(String(64))

    @property
    def serialize(self):
        return {
                'id': self.id,
                'email': self.email,
                'picture': self.picture
        }


    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(secret_key, expires_in = expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        user_id = data['id']
        return user_id


class RequestMeal(Base):
    __tablename__ = 'requestmeal'
    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey('user.id'))
    meal_type = Column(String)
    location_string = Column(String)
    latitude = Column(String)
    longditude = Column(String)
    meal_time = Column(String)
    filled = Column(Boolean)

    @property
    def serialize(self):
        return {
                'id': self.id,
                'user_id': self.user_id,
                'meal_type': self.meal_type,
                'location_string': self.location_string,
                'latitude': self.latitude,
                'longitude': self.longitude,
                'meal_time': self.meal_time,
                'filled': self.filled
        }
 

class Proposal(Base):
    __tablename__ = 'proposal'
    id = Column(Integer, primary_key = True)
    user_proposed_to = Column(String)
    user_proposed_from = Column(String)
    request_id = Column(Integer, ForeignKey('requestmeal.id'))
    filled = Column(Boolean)

    @property
    def serialize(self):
        return {
                'id': self.id,
                'user_proposed_to': self.user_proposed_to,
                'user_proposed_from': self.user_proposed_from,
                'request_id' : self.request_id,
                'filled': self.filled
        }


class MealDate(Base):
    __tablename__ = 'mealdate'
    id = Column(Integer, primary_key = True)
    user_1 = Column(String)
    user_2 = Column(String)
    restaurant_name = Column(String)
    restaurant_address = Column(String)
    restaurant_picture = Column(String)
    meal_time = Column(String)

    @property
    def serialize(self):
        return {
                'id': self.id,
                'user_1': self.user_1,
                'user_2': self.user_2,
                'restaurant_name': self.restaurant_name,
                'restaurant_adderess': self.restaurant_address,
                'restaurant_picture': self.restaurant_picture,
                'meal_time': self.meal_time
        }


engine = create_engine('sqlite:///MeetNEat.db')
 

Base.metadata.create_all(engine)
    
