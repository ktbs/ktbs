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
    base1 = root.create_base("base1/")
    print "----- base1.label: ", base1.label
    #base1.label = "A new base"
    #print "----- base1.label: ", base1.label
    print "----- base1.url: ", base1.uri

if __name__ == "__main__":
    main()
