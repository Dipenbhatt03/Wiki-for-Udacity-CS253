import webapp2
import jinja2
import os
import hashlib
import hmac
import random
import string
from google.appengine.ext import ndb


template_dir=os.path.join(os.getcwd(),'templates/user_acounts')
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),autoescape=True)


LOGGED=False

class UserDetail(ndb.Model):
	name=ndb.StringProperty(required=True)
	password=ndb.StringProperty(required=True)
	email=ndb.StringProperty(required=False)

class Handler(webapp2.RequestHandler):
	def write(self,*a,**kw):
		self.response.write(*a)

	def render_str(self,template,**kwargs):
		t=jinja_env.get_template(template)
		return t.render(**kwargs)

	def render(self,template,**kwargs):
		self.write(self.render_str(template,**kwargs))
		
	

def make_salt():
	return ''.join([random.choice(string.ascii_letters) for i in range(0,5)])

def make_pw_hash(name,pw,salt=None):
	if not salt:
		salt=make_salt()

	return '{}|{}'.format(salt,hashlib.sha256(name+pw+salt).hexdigest())

def check_password(name,pw,h):
	salt=h.split('|')[0]
	return make_pw_hash(name,pw,salt)==h

def check_if_user_exist(name,password):
	users=UserDetail.query().fetch()
	for user in users:
		if user.name==name:
			h=user.password
			if check_password(name,password,h):
				return h
	return 1



class SignUpHandler(Handler):
	def get(self):
		name=self.request.get('username')
		email=self.request.get('email')
		self.render('form.html',name=name,email=email)

	def post(self):
		name=self.request.get('username')
		password=self.request.get('password')
		verify=self.request.get('verify')
		email=self.request.get('email')
		Name_Error=''
		Password_Error=''
		if name and password and password==verify:
			val=check_if_user_exist(name,password)
			if val==1:
				salt=make_salt()
				self.response.headers.add_header('Set-Cookie', 'user-id={}; Path=/'.format(make_pw_hash(name,password,salt)))
				user=UserDetail(name=name,password=make_pw_hash(name,password,salt),email=email)
				user.put()
				self.redirect("/")
			else:
				Name_Error='User already exist'
		else:
			if not name:
				Name_Error='Please enter name'
			if password and not password==verify:
				Password_Error='Your password do not match'
			if not password:
				Password_Error="Enter valid password"

		self.render('form.html',name=name,email=email,Name_Error=Name_Error,Password_Error=Password_Error)





class LoginHandler(Handler):
	def get(self):
	#	username=self.request.get('username')
	#	password=self.request.get('password')
		self.render('Login.html')		

	def post(self):
		username=self.request.get('username')
		password=self.request.get('password')
		Error='Invalid Login'
		if username and password:
			val=check_if_user_exist(username,password)
			if val!=1:
				#print val*10
				self.response.headers.add_header('set-cookie','user-id={}; Path=/'.format(val))
				self.redirect('/')
		self.render('Login.html',username=username,password=password,Error=Error)

class LogoutHandler(Handler):
	def get(self):
		LOGGED=False
		self.response.headers.add_header('set-cookie','user-id={};Path=/'.format(''))
		self.redirect('/')

