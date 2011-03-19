
from pprint import pprint
from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET


class FormPage(Resource):
    def render_GET(self, request):
        return ''

    def render_POST(self, request):
        reactor.callLater(5, self._build_response, request)
        return NOT_DONE_YET

    def _build_response(self, request):
        pprint(request.__dict__)
        newdata = request.content.getvalue()
        print newdata
        request.write('')
        request.finish()

root = Resource()
root.putChild("options", FormPage())
site = Site(root)
reactor.listenTCP(8888, site)
reactor.run()

