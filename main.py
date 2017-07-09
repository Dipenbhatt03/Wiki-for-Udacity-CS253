import webapp2
import jinja2
import os
import datetime
import time

from user_acounts import UserDetail
from user_acounts import SignUpHandler
from user_acounts import LoginHandler
from user_acounts import LogoutHandler

from google.appengine.ext import ndb
from google.appengine.api import memcache



template_dir=os.path.join(os.getcwd(),'templates')
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))


class PageContent(ndb.Model):
	version=ndb.IntegerProperty(required=True)
	created=ndb.DateTimeProperty(auto_now_add=True)
	content=ndb.StringProperty()


class Page(ndb.Model):
	code=ndb.StringProperty()
	versions=ndb.StructuredProperty(PageContent,repeated=True)

class Handler(webapp2.RequestHandler):
	def write(self,*a,**kw):
		self.response.write(*a)

	def render_str(self,template,**kwargs):
		t=jinja_env.get_template(template)
		return t.render(**kwargs)

	def render(self,template,**kwargs):
		self.write(self.render_str(template,**kwargs))

		
def check_if_logged_in(user_id=None):
	if user_id:
		user=UserDetail.query().filter(UserDetail.password == user_id).fetch()
		acount=''
		if user:	
			acount='logout({})'.format(user[0].name)
			return True,acount
	return False,'Fuck off'

def get_page(code):
	page=Page.query().filter(Page.code==code).fetch()
	if page:
		return page[0]
	return None

def get_latest_version_of_page(page):
	return page.versions[len(page.versions)-1]

def total_number_of_versions(versions):
	return len(versions)

def get_version_of_page(page,version):
	for p in page.versions:
		if p.version==int(version):
			return p
	return None

class WikiPageHandler(Handler):
	def get(self,code):
		user_id=self.request.cookies.get('user-id')
		logged,acount=check_if_logged_in(user_id)
		link=''
		if not logged:
			acount='login'
			link='login'
		else:
			link='logout'
		version=self.request.get('v')
		page=None
		page=get_page(code)
		print page
		if not page:
			#self.write('fffff')
			self.redirect('/_edit'+code)
		else:
			page_version=None
			p_vs=''
			if not version:
				page_version=get_latest_version_of_page(page)
			else:
				page_version=get_version_of_page(page,version)
				if not page_version:
					self.error(404)
					return
				else:
					p_vs='?v='+version
			self.render('Front page.html',content=page_version.content,
				acount=acount,logged=logged,link=link,code=code,p_vs=p_vs)


class EditPageHandler(Handler):
	def get(self,code):
		user_id=self.request.cookies.get('user-id')
		logged,a=check_if_logged_in(user_id)
		version=self.request.get('v')
		if not logged:
			self.redirect('/login')
			return
		page=None
		page=get_page(code)
		if page:
			if not version:
				page_version=get_latest_version_of_page(page)
			else:
				page_version=get_version_of_page(page,version)
				if not page_version:
					self.error(404)
					return
			self.render('Edit Page.html',content=page_version.content,code=code)
		else:

			self.render('Edit Page.html',code=code)
	def post(self,code):
		user_id=self.request.cookies.get('user-id')
		logged,a=check_if_logged_in(user_id)
		if not logged:
			self.redirect('/login')
			return
		content=self.request.get('content')
		page=get_page(code)
		if not page:
			Page(code=code,versions=[
				PageContent(version=1,content=content)
				]).put()
			time.sleep(2)
			self.redirect(code)
		else:
			total_versions=total_number_of_versions(page.versions)
			page.versions.append(PageContent(version=total_versions+1,content=content))
			page.put()
			self.redirect(code)


class PageHistoryHandler(Handler):
	def get(self,code):
		user_id=self.request.cookies.get('user-id')
		logged,acount=check_if_logged_in(user_id)
		link=''
		if not logged:
			acount='login'
			link='login'
		else:
			link='logout'

		page=get_page(code)
		if not page:
			self.error(404)
			return
		page.versions.reverse()
		self.render('page history.html',versions=page.versions,logged=logged,code=code,link=link,acount=acount)



		




PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'

app = webapp2.WSGIApplication([
						(r'/signup',SignUpHandler),
						(r'/login',LoginHandler),
						(r'/logout',LogoutHandler),
						('/_history'+PAGE_RE,PageHistoryHandler),
						
						(r'/_edit' + PAGE_RE, EditPageHandler), 
						(PAGE_RE, WikiPageHandler),
						(r'/_history'+PAGE_RE,PageHistoryHandler)
						
						]
						,debug=True)