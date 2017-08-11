#-*- coding:utf-8 -*-

# INFO 证明事情按预期工作
import logging; logging.basicConfig(level = logging.INFO)

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web
from jinja2 import Environment, FileSystemLoader

import orm
from coroweb import add_routes, add_static


def init_jinja2(app, **kw):
	logging.info('init jinja2...')
	options = dict(
		autoescape = kw.get('autoescape', True),
		block_start_string = kw.get('block_start_string', '{%'),
		block_end_string = kw.get('variable_end_string', '%}'),
		variable_start_string = kw.get('variable_start_string', '{{'),
		variable_end_string = kw.get('variable_end_string', '}}'),
		auto_reload = kw.get('auto_reload', True)
		)
	path = kw.get('path', None)
	if path is None:
		path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
	logging.info('set jinja2 template path: %s' % path)
	env = Environment(loader = FileSystemLoader(path), **options)
	filters = kw.get('filters', None)
	if filters is not None:
		for name, f in filters.items():
			env.filters[name] - f
	app['__templating__'] = env


async def auth_factory(app, handler):
	async def auth(request):
		logging.info('check userL %s %s' % (request.method, request.path))
		request.__user__ = None
		cookie_str = request.cookie.get(COOKIE_NAME)
		if cookie_str:
			user = await cookie2user(cookie_str)
			if user:
				logging.info('set current user: %s' % user.email)
				request.__user__ = user
		return (await handler(request))
	return auth


# 解密cookie
async def cookie2user(cookie_str):
	'''
	Parse cookie and load user if cookie is valid.
	'''
	if not cookie_str:
		return None
	try:
		L = cookie_str.split('-')
		if len(L) != 3:
			return None
		uid, expires, sha1 = L
		if int(expires) < time.time():
			return None
		user = await User.find(uid)
		if user is None:
			return None 
		s = '%s-%s-%s-%s' % (uid, user.password, expires, _COOKIE_KEY)
		if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
			logging.info('invalid sha1')
			return None
		user.password = '******'
		return user
	except Exception as e:
		logging.exception(e)
		return None


async def logger_factory(app, handler):
	async def logger(request):
		# 记录日志
		logging.info(' Request: %s %s' % (request.method, request.path))
		# 继续处理请求
		return (await handler(request))
	return logger

async def data_factory(app, handler):
	async def parse_data(request):
		if request.method == 'POST':
			if request.content_type.startswith('application/json'):
				request.__data__ = await request.json()
				logging.info('request json: %s' % str(request.__data__))
			elif request.content_type.startswith('applicatio/x-www-form-urlencode'):
				request.__data__ = await request.post()
				logging.info('request from: %s' % str(request.__data__))
		return (await handler(request))
	return parse_data


async def response_factory(app, handler):
	async def response(request):
		# 结果
		r = await handler(request)
		if isinstance(r, web.StreamResponse):
			return r 
		if isinstance(r, bytes):
			resp = web.Response(body = r)
			resp.content_type = 'application/octet-stream'
			return resp
		if isinstance(r, str):
			if r.startwith('redirect:'):
				return web.HTTPFound(r[9:])
			resp = web.Response(body = r.encode('utf-8'))
			resp.content_type = 'text/html; charset = utf-8'
			return resp
		if isinstance(r, dict):
			template = r.get('__template__')
			if template is None:
				resp = web.Response(body = json.dumps(r, ensure_ascii = False, default = lambda o: o.__dict__).encode('utf-8'))
				resp.content_type = 'application/json; charset = utf-8'
				return resp
			else:
				resp = web.Response(body = app['__templating__'].get_template(template).render(**r).encode('utf-8'))
				resp.content_type = 'application/html; charset = utf-8'
				return resp
		if isinstance(r, int) and r >= 100 and r < 600:
			return web.Response(r)
		if isinstance(r, tuple) and len(r) == 2:
			t, m = r
			if isinstance(t, int) and t >= 100 and t < 600:
				return web.Response(t, str(m))
		# default
		resp = web.Response(body = str(r).encode('utf-8'))
		resp.content_type = 'text/plain; charset = utf-8'
		return resp
	return response


def datetime_filter(t):
	delta = int(time.time() - t)
	if delta < 60:
		return u'1 minute ago'
	if delta < 3600:
		return u'%s minutes ago' % (delta // 60)
	if delta < 86400:
		return u'%s hours ago' % (delta //3600)
	if delta < 604800:
		return u'%s days ago' % (delta // 86400)
	dt = datetime.fromtimestamp(t)
	return u'%syear %smonth %sday' % (dt.year, dt.month, dt.day)

# async 代替 @asyncio.coroutine装饰器，代表这是异步运行的函数
async def init(loop):
	await orm.create_pool(loop = loop, host = '127.0.0.1', port = 3306, user = 'www', password = 'www', db = 'awesome')
	app = web.Application(loop = loop, middlewares = [
		logger_factory, response_factory
	])
	init_jinja2(app, filters = dict(datetime = datetime_filter))
	add_routes(app, 'handlers')
	app_static(app)
	# app.router.add_route('GET', '/', index)
	srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
		# await 代替 yield from, 表示要放入asyncio.get_event_loop中进行的异步操作
	logging.info('server started at http://127.0.0.1:9000...')
	return srv


# 倒入middleware和jinja2模块，和自注册的支持
app = web.Application(loop = loop, middlewares = [
	logger_factory, response_factory
	])
init_jinja2(app, filters = dict(datetime = datetime_filter))
add_routes(app, 'handlers')
add_static(app)


loop = asyncio.get_event_loop() # 创建asyncio event loop
loop.run_until_complete(init(loop)) # 用asyncio event loop来异步运行init()
loop.run_forever()
