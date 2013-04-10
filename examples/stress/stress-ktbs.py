from argparse import ArgumentParser
from timeit import timeit

from rdfrest.http_client import set_http_option
from ktbs.client import get_ktbs
from ktbs.engine.service import make_ktbs
from ktbs.namespace import KTBS

ARGS = None
BASE = None

def parse_args():
    global ARGS
    parser = ArgumentParser("kTBS stress tool")
    parser.add_argument("-k", "--ktbs",
                        help="the URI of the kTBS to stress (a local "
                             "in-memory kTBS will be used if none is giveb)")
    parser.add_argument("-i", "--iterations", type=int, default=10,
                        help="the number of iterations to run")
    parser.add_argument("-p", "--nbpost", type=int, default=100,
                        help="the number of post to perform at each iteration")
    parser.add_argument("-o", "--nbobs", type=int, default=1,
                        help="the number of obsels to send per post")
    parser.add_argument("--no-clean", action="store_true",
                        help="if set, do not clean kTBS after stressing")
    ARGS = parser.parse_args()

def setUp():
    global ARGS, BASE
    if ARGS.ktbs is None:
        my_ktbs = make_ktbs()
        ARGS.ktbs = my_ktbs.uri
    elif ARGS.ktbs.startswith("file://"):
        my_ktbs = make_ktbs(repository=ARGS.ktbs[7:])
        ARGS.ktbs = my_ktbs.uri
    else:
        my_ktbs = get_ktbs(ARGS.ktbs)
    
    BASE = my_ktbs.create_base(label="stress-ktbs-base")
    model = BASE.create_model("m")
    model.unit = KTBS.millisecond
    BASE.create_stored_trace("t/", "m", "2012-09-06T00:00:00Z",
                             default_subject="Alice")

def task():
    trace = BASE.get("t/")
    print "Stressing %s %s times with %s obsels" % (
        ARGS.ktbs, ARGS.iterations, ARGS.nbobs)
    for i in xrange(ARGS.iterations):
        def create_P_obsels():
            for j in xrange(ARGS.nbpost):
                if ARGS.nbobs > 1:
                    raise NotImplementedError("batch post not supported yet")
                trace.create_obsel(None, "#obsel", no_return=True)
        print "%ss" % timeit(create_P_obsels, number=1)

def tearDown():
    if not ARGS.no_clean:
        BASE.get("t/").delete()
        BASE.get("m").delete()
        BASE.delete()

def main(argv):
    set_http_option("disable_ssl_certificate_validation", True)
    parse_args()
    setUp()
    task()
    tearDown()

if __name__ == "__main__":
    from sys import argv, exit
    main(argv)
