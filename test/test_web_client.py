
import httplib2
import simplejson


TESTDATA = {'target_uri': 'sip:test@sip.voice.google.com'}
URL = 'http://localhost:8888/options'

jsondata = simplejson.dumps(TESTDATA)
h = httplib2.Http()
resp, content = h.request(URL,
                          'POST',
                          jsondata,
                          headers={'Content-Type': 'application/json'})
print resp
print content

