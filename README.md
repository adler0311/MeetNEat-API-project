## 설명 및 개요: 

이 앱은 사람들이 음식 취향에 따라 약속을 제안하고 만날 수 있도록 도와주는 소셜 앱입니다. 

사용자는 각 API 엔드포인트를 통해 아이디를 생성하고, OAuth를 통해 로그인할 수 있습니다. 

또한 새로운 제안을 하고 존재하는 제안에 신청할 수 있으며 모임이 성사되었을 경우 구체적인 레스토랑 정보와 만날 시간을 정하여 약속을 잡을 수 있습니다. 

구글 맵 API와 Foursquare API를 사용하여 사용자가 원하는 지역의 Geocode를 정보를 가져오고 이를 Foursquare API에 적용하여 인지도 높은 인근지역 레스토랑 정보를 가져오도록 했습니다. 

각 엔드포인트는 플라스크 프레임워크에서 제공하는 Rate Limtit 기능을 통해 특정 IP에 대한 일일 사용횟수를 200회, 시간당 20회로 제한하였습니다. 

또한 구글 OAuth 제공자를 통해 로그인하고 사용자를 생성할 수 있는 API를 제공하고 있습니다.


## 시작하기

해당 프로젝트는 로컬 서버에서만 구동할 수 있습니다.

먼저 현재 저장소를 복사하여 로컬 드라이브에 저장하세요.

해당 폴더로 이동하여 `views.py` 파이썬 파일을 실행하세요.

해당 파일을 실행하기 위해서는 다음과 같은 모듈이 필요합니다.

`
flask
httplib2
sqlalchemy
httpauth
oauth2client
requests
json
`


## 사용한 스택, 언어 :

* [구글 맵 API] : <https://developers.google.com/maps/documentation/static-maps/?hl=ko>
* [포스퀘어 API] : <https://developer.foursquare.com/>
* [파이썬] : <https://www.python.org/>
* [파이썬 플라스크] : <http://flask-docs-kr.readthedocs.io/ko/latest/>
* [SQLAlchemy] : <https://www.sqlalchemy.org/>


## 파일 설명 :

- findARestaurant.py : geocode 파일에서 반환한 위도, 경도 위치정보를 사용하여 Foursquare API에서 인근 지역의 인지도 있는 레스토랑 이름, 주소, 사진 정보를 반환합니다.

- geocode.py : 구글 맵 API를 사용하여 찾고자 하는 지역의 위도와 경도를 반환합니다.

- models.py : 데이터베이스 정보를 담고 있습니다.

- views.py : 파이썬 플라스크를 기반으로 API에 대한 정보를 담고 있는 웹 서버 파일입니다.


## 엔드포인트 디자인 :

### get_auth_token

경로: '/api/v1/token'
메소드: GET
파라메터: 
반환값: 토큰 값
설명: 현재 사용자의 auth 토큰으 생성하고 토큰에 사용자 아이디를 저장함

### login

경로: '/api/v1/<provider>/login'
메소드: POST
파라메터: 1회용 Auth code
반환값: 성공적으로 로그인 했을 시에는 토큰을, 그렇지 않을 때는 에러 메시지를 반환.
설명: OAuth 제공자(현재는 구글만 제공)를 통해 로그인하는 엔드포인트. 클라이언트 측에서 받은 auth code를 \
	 구글 API를 통해 인증을 하고, 이를 통해 얻은 사용자 정보를 플라스크 로그인 세션에 저장. 또한 사용자 이메일을\
	 통해 데이터베이스에 사용자를 추가하고 클라이언트와 웹 서버 간 로그인 기능을 위한 토큰을 발행



### logout

경로: '/api/v1/<provider>/logout'
메소드: POST
파라메터: 토큰
반환값: 로그아웃 성공 여부에 대한 메시지
설명: 웹 서버 로그인 세션에 저장된 사용자 정보를 구글 API를 통해 로그아웃하고, 로그인 세션에 저장된 사용자 정보와 토큰을 제거


### users

경로: '/api/v1/users'
메소드: GET, POST
파라메터: 
	GET:
	POST: 사용자 이메일과 비밀번호, 사진(선택)
반환값:
	GET: 모든 사용자에 대한 정보
	POST: 저장한 사용자의 이메일
설명: 
	GET: 데이터베이스에 저장된 모든 사용자 정보를 쿼리
	POST: OAuth를 사용하지 않고 새로운 사용자 계정을 생성


### specificUser

경로: '/api/v1/users/<int:user_id>'
메소드: GET, PUT, DELETE
파라메터: 토큰
	GET: 
	PUT: 새로운 사용자 프로필 정보
	DELETE:
반환값:
	GET: 해당 사용자 아이디를 가진 사용자 정보
	PUT: 수정된 해당 사용자 정보
	DELETE: 사용자가 제거됬다는 메시지
설명: 
	GET: 특정 사용자 정보를 반환
	PUT: 특정 사용자 정보를 업데이트
	DELETE: 특정 사용자 정보를 제거


### requestsMeal

경로: '/api/v1/requests'
메소드: GET, POST
파라메터: 토큰
	GET: 
	POST: 모임 요청 정보
반환값:
	GET: 모든 모임 요청 정보
	POST: 저장한 새 모음 요청 정보
설명: 
	GET: 모든 모임 요청 정보를 쿼리
	POST: 새로운 모임 요청


### specificRequestMeal

경로: '/api/v1/requests/<int:request_id>'
메소드: GET, PUT, DELETE
파라메터: 토큰
	GET: 
	PUT: 수정할 모임 정보
	DELETE:
반환값:
	GET: 특정 모임 요청 정보
	PUT: 새로 업데이트한 모임 요청 정보
	DELETE: 해당 요청이 삭제되었다는 메시지
설명: 
	GET: 특정 모임 요청 정보를 반환
	PUT: 특정 모임 요청 정보를 업데이트
	DELETE: 특정 모임 요청 정보를 제거


### proposals

경로: '/api/v1/proposals'
메소드: GET, POST
파라메터: 토큰
	GET:
	POST: 
반환값:
	GET: 현재 사용자의 모든 모임 신청 정보
	POST: 새로 신청한 모임 정보
설명: 
	GET: 현재 사용자의 모든 모임 신청을 불러옴
	POST: 모임에 새로 신청


### specificProposal

경로: '/api/v1/proposals/<int:proposal_id>'
메소드: GET, PUT, DELETE
파라메터: 토큰
	GET: 
	PUT: 수정할 신청 정보.
	DELETE:
반환값:
	GET: 특정 신청 정보
	PUT: 새로 수정한 특정 신청 정보
	DELETE: 특정 신청 정보를 제거했다는 메시지
설명: 
	GET: 특정 신청 정보를 쿼리
	PUT: 특정 신청 정보를 업데이트
	DELETE: 특정 신청 정보를 삭제


### dates

경로: '/api/v1/dates'
메소드: GET, POST
파라메터: 토큰
	GET:
	POST: 
반환값:
	GET: 현재 사용자의 모든 약속
	POST: 현재 사용자가 추가한 새 약속 정보
설명: 
	GET: 현재 사용자의 모든 약속을 쿼리
	POST: 현재 사용자의 새 약속을 생성


### specificDate

경로: '/api/v1/dates/<int:date_id>'
메소드: GET, PUT, DELETE
파라메터: 토큰
	GET: 
	PUT: 수정할 약속 정보
	DELETE:
반환값:
	GET: 특정 약속 정보
	PUT: 새로 수정할 특정 약속 정보
	DELETE: 특정 약속 정보를 삭제했다는 메시지
설명: 
	GET: 특정 약속 정보를 쿼리.
	PUT: 특정 약속 정보를 업데이트.
	DELETE: 특정 약속 정보를 삭제.





