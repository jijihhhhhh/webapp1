

def get(path):
	'''
	Define decorator @get('/path')
	'''

	def decorator(func):
		@functools.wraps(func)
		def wrapper(*args, **kw):
			return func(*args, **kw)
		wrapper.__method__ = 'GET'
		wrapper.__route__ = path
		return wrapper
	return decorator

def post(path):
	'''
	Define decorator @post('/path')
	'''

	def decorator(func):
		@functools.wraps(func)
		def wrapper(*args, **kw):
			return func(*args, **kw)
		wrapper.__method__ = 'POST'
		wrapper.__route__ = path
		return wrapper
	return decorator


# 封装URL处理函数
class RequestHandler(object):

	def __init__(self, app, fn):
		self._app = app
		self._func = fn
		...

	@asyncio.coroutine
	def __call__(self, request):
		kw = ... 获取参数
		r = yield from self._func(**kw)
		return r 

# 注册URL处理函数
def add_route(app, fn):
	method = getattr(fn, '__method__', None)
	path = getattr(fn, '__route__', None)
	if path is None or method is None:
		raise ValueError('@get or @post not defined in %s.' % str(fn))
	if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
		fn = asyncio.coroutine(fn)
	logging.info('add route %s %s ==> %s(%s) ' % (method, path, fn.__name__, ','.join(inspect.signature(fn).parameters.keys())))
	app.route.add_route(method, path, RequestHandler(app, fn))


def add_routes(app, module_name):
	n = module_name.rfind('.')
	if n == (-1):
		mod = __import__(module_name, globals(), locals())
	else:
		name = module_name[n+1:]
		mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)
	for attr in dir(mod):
		if attr.startswith('_'):
			coroutine
		fn = getattr(mod, attr)
		if callable(fn):
			method = getattr(fn, '__method__', None)
			path = getattr(fn, '__route__', None)
			if method and path:
				add_route(app, fn)


# 注册调用
add_routes(app, 'handlers')




