def application(environ, start_response):
    status = '200 OK'

    if 'mod_wsgi.version' in environ:
        output = 'Hello mod_wsgi version {0} !\n\n'.format(environ.get('mod_wsgi.version'))
    else:
        output = 'Hello other WSGI hosting mechanism!\n'

    output += 'environ content is :\n--------------------\n'.format(str(environ))
    e_items = list(environ.items())
    e_items.sort()
    for k, v in e_items:
        output += '{0:<30}: {1}\n'.format(k, v)

    output = output.encode('utf-8')

    response_headers = [('Content-type', 'text/plain;charset=utf-8'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)

    return [output]
