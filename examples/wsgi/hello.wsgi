def application(environ, start_response):
    status = '200 OK'

    if environ.has_key('mod_wsgi.version'):
        output = 'Hello mod_wsgi version {0} !\n\n'.format(environ.get('mod_wsgi.version'))
    else:
        output = 'Hello other WSGI hosting mechanism!'

    output += 'environ content is :\n--------------------\n'.format(str(environ))
    e_keys = environ.keys()
    e_keys.sort()
    for k in e_keys:
        output += '{0:<30}: {1}\n'.format(k, environ.get(k))

    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)

    return [output]
