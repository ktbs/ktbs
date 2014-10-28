from argparse import ArgumentParser
from os import fork
from sys import stderr
from timeit import timeit

from rdfrest.http_client import set_http_option
from ktbs.client import get_ktbs
from ktbs.engine.service import make_ktbs
from ktbs.namespace import KTBS
from ktbs.config import get_ktbs_configuration

ARGS = None
BASE = None

def parse_args():
    global ARGS
    parser = ArgumentParser("kTBS stress tool")
    parser.add_argument("-k", "--ktbs",
                        help="the URI of the kTBS to stress (a local "
                             "in-memory kTBS will be used if none is giveb)")
    parser.add_argument("-f", "--forks", type=int, default=1,
                        help="the number of processes to fork")
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
        ktbs_config = get_ktbs_configuration()
        config.set('rdf_database', 'repository', ARGS.ktbs[7:])
        my_ktbs = make_ktbs(ktbs_config)
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
    print "Stressing %s %s times with %sx%s obsels" % (
        ARGS.ktbs, ARGS.iterations, ARGS.nbpost, ARGS.nbobs)
    results = []
    for i in xrange(ARGS.iterations):
        def create_P_obsels():
            for j in xrange(ARGS.nbpost):
                if ARGS.nbobs > 1:
                    raise NotImplementedError("batch post not supported yet")
                trace.create_obsel(None, "#obsel", subject="Alice",
                                   no_return=True)
        res = timeit(create_P_obsels, number=1)
        print "%ss" % res
        results.append(res)
    print "average: %ss" % (sum(results)/len(results))

def tearDown():
    if not ARGS.no_clean:
        BASE.get("t/").delete()
        BASE.get("m").delete()
        BASE.delete()

def main(argv):
    parse_args()
    forks = ARGS.forks
    while forks > 1:
        forks -= 1
        rf = fork()
        if rf == 0:
            break # children must not spawn children of their own
        elif rf < 0:
            print >>stderr, "Fork failed..."
            break
    set_http_option("disable_ssl_certificate_validation", True)
    setUp()
    try:
        task()
    finally:
        tearDown()

if __name__ == "__main__":
    from sys import argv, exit
    main(argv)
