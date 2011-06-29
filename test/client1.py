from os.path import abspath, dirname, join
from sys import path

source_dir = dirname(dirname(abspath(__file__)))
lib_dir = join(source_dir, "lib")
path.insert(0, lib_dir)

from ktbs.client.root import KtbsRoot
from logging import basicConfig, DEBUG
from sys import stdout

def main():
    #basicConfig(level=DEBUG, stream=stdout)

    root = KtbsRoot("http://localhost:8001/")
    print "----- root.label: ", root.label
    #root.label = "Another label"
    #print root.label
    base2 = root.create_base("base2/")
    try:
        print "----- base2.label: ", base2.label
        #base2.label = "A new base"
        #print "----- base2.label: ", base2.label
        print "----- base2.uri: ", base2.uri
        print "----- bases: ", [ b.label for b in root.bases ]
    finally:
        base2.remove()

    base1 = root.get_base("base1/")
    print "----- base1.label", base1.label
    t01 = base1.get("t01/")
    print "----- t01.label", t01.label
    #t01.label = "Coucou"
    #print "----- t01.label", t01.label
    print "----- t01.obsels", [ o.label for o in t01.obsels ]
    print [at.label for at in t01.obsels[2].attribute_types ]

if __name__ == "__main__":
    main()
