
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re, time, json, logging, hashlib, base64, asyncio

import markdown2

from aiohttp import web

from coroweb import get,post
from apis import APIValueError, APIResouceNotFoundError

from models import User, Comment, Blog, next_id
from config import configs

COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret


# 计算加密cookie
def user2cookie(user, max_age):
	# build cookie string by: is-expires-sha1
	expires = str(int(time.time() + max_age))
	s = '%s-%s-%s' % (user.id, user.password, expires, _COOKIE_KEY)
	L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
	return '-'.join(L)


async def cookie2user(cookie_str):

@get('/')
def index(request):
	summary = 'Summary Summary Summary Summary Summary Summary Summary Summary'
	blogs = [
		Blog(id = '1', name = 'Test Blog', summary = summary, created_at = time.time()-120),
		Blog(id = '2', name = 'Something new', summary = summary, created_at = time.time()-3600),
		Blog(id = '3', name = 'Learn Swift', summary = summary, created_at = time.time()-7200)
	]
	return {
		'__template__': 'blogs.html',
		'blogs': blogs
	}

'''
@get('/api/users')
def api_get_users(*, page='1'):
	page_index = get_page_index(page)
	num = yield from User.findNumber('count(id)')
	p = Page(num, page_index)
	if num == 0:
		return dict(page = p, users = ())
	users = yield from User.findAll(orderBy = 'created_at desc', limit = (p.offset, p.limit))
	for u in users:
		u.password = '******'
	return dict(page = p, users = users)
'''

@get('/register')
def register():
	return {
		'__template__': 'register.html'
	}

@get('/signin')
def signin():
	return {
		'__template__': 'signin.html'
	}


@post('/api/authenticate')
def authenticate(*, email, password):
	if not email:
		raise APIValueError('email', 'Invalid email.')
	if not password:
		raise APIValueError('password', 'Invalid password.')
	users = yield from User.findAll('email=?', [email])
	if len(users) == 0:
		raise APIValueError('email', 'Email not exist.')
	user = users[0]
	# check password:
	sha1 = hashlib.sha1()
	sha1.update(user.id.encode('utf-8'))
	sha1.update(b':')
	sha1.update(password.encode('utf-8'))
	if user.password != sha1.hexdigest():
		raise APIValueError('password', 'Invalid password.')
	# authenticate ok, set cookie
	r = web.Response()
	r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age = 86400, httponly = True)
	user.password = '******'
	r.content_type = 'application/json'
	r.body = json.dumps(user, ensure_ascii = False).encode('utf-8')
	return r

@get('/signout')
def signout(request):
	referer = request.headers.get('Referer')
	r = web.HTTPFound(referer or '/')
	r.set_cookie(COOKIE_NAME, '-deleted-', max_age = 0, httponly = True)
	logging.info('user signed out.')
	return r

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

@post('/api/users')
def api_register_user(*, email, name, password):
	if not name or not name.strip():
		raise APIValueError('name')
	if not email or not _RE_EMAIL.match(email):
		raise APIValueError('email')
	if not password or not _RE_SHA1.match(password):
		raise APIValueError('password')
	users = yield from User.findAll('email = ?', [email])
	if len(users) > 0:
		raise APIError('register:failed', 'email', 'Email is already in use.')
	uid = next_id()
	sha1_password = '%s:%s' % (uid, password)
	user = User(id = uid, name = name.strip(), email = email, password = hashlib.sha1(sha1_password.encode('utf-8')).hexdigest(), image = 'http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
	yield from user.save()
	# make session cookie
	r = web.Response()
	r.set_cookie(COOKIE_NAME, user2cookie(userm 86400), max_age = 86400, httponly = True)
	user.password = '******'
	r.content_type = 'application/json'
	r.body = json.dumps(user, ensure_ascii = False).encode('utf-8')
	return r

'''
@post('/api/blogs')
def api_create_blog(request, *, name, summary, content):
	check_admin(request)
	if not name or not name.strip():
		raise APIValueError('name', 'name cannot be empty.')
	if not summary or not summary.strip():
		raise APIValueError('summary', 'summary cannot be empty.')
	if not content or not content.strip():
		raise APIValueError('content', 'content cannot be empty.')
	blog = Blog(user_id = request.__user__.id, user_name = request.__user__.name, user_image = request.__user__.image, name = name.strip(), summary = summary.strip(), content = content.strip())
	await blog.save()
	return blog
'''








