"""
<OS> <branch> [type of build]

Examples:

The builder: <OS> <branch> build (e.g. 'Linux mozilla-central build')

A debug test: <OS> <branch> debug test <test type> 

An opt test: <OS> <branch> opt test <test type>

A leak test: <OS> <branch> leak test <test type>

Talos:
<OS> <branch> talos (e.g. 'Rev3 Fedora 12x64 mozilla-central talos')
-or-
<OS> <branch> talos <type> (e.g. 'Rev3 Fedora 12x64 mozilla-central talos cold')
"""

# OS mappings
OSes = [ 'Linux',
         'Linux x86-64',
         'OS X 10.5.2',
         'OS X 10.6.2',
         'Rev3 Fedora 12',
         'Rev3 Fedora 12x64',
         'Rev3 MacOSX Leopard 10.5.8',
         'Rev3 MacOSX Snow Leopard 10.6.2',
         'Rev3 WINNT 5.1',
         'Rev3 WINNT 6.1',
         'WINNT 5.2' ]
OS_to_index = dict([(OS, index) for index, OS in enumerate(OSes)])
index_to_OS = dict([(index, OS) for index, OS in enumerate(OSes)])
OSdata = { 'Linux': {'name': 'Linux', 'bits': 32 },
           'Rev3 Fedora 12': { 'name': 'Fedora', 'bits': 32}
           'Rev3 Fedora 12x64': { 'name': 'Fedora', 'bits': 64}
	   'Linux x86-64': { 'name': 'Linux', 'bits': 64}
	   'OS X 10.5.2': { 'name': 'MAC OSX', 'bits': 32}
	   'OS X 10.6.2': { 'name': 'MAC OSX', 'bits': 64}
	   'Rev3 MacOSX Leopard 10.5.8': { 'name': 'MAC OSX', 'bits': 32}
	   'Rev3 MacOSX Snow Leopard 10.6.2': { 'name': 'MAC OSX', 'bits': 64}
	   'Rev3 WINNT 5.1': { 'name': 'Windows', 'bits': 32}
	   'Rev3 WINNT 6.1': { 'name': 'Windows', 'bits': 64}
	   'WINNT 5.2': { 'name': 'Windows', 'bits': 32}
    }
