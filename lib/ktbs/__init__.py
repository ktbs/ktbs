#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Universite de Lyon <http://www.universite-lyon.fr>
#
#    KTBS is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    KTBS is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with KTBS.  If not, see <http://www.gnu.org/licenses/>.

"""
KTBS: Kernel for Trace-Based Systems.
"""


__version__  = "0.6"
__commitno__ = ""

try:
    import git
    GIT_LIBRARY_INSTALLED = True


    def get_git_infos(path=None):
        """
        Get git repository information if available.
        """
        commit_no = ""
        try:
            repo = git.Repo(path)
            if git.__version__ > '0.1.7':
                commit_no = repo.head.commit.hexsha
            else:
                lcommits = repo.commits(start=repo.head, max_count=1)
                if len(lcommits) > 0:
                    commit_no = lcommits[0].id

            # Add a separation here to avoid managing it everywhere
            commit_no = ":%s" % commit_no

        except git.InvalidGitRepositoryError:
            # This is not a git repository
            pass

        return commit_no

except ImportError:
    # Git information can not be found
    GIT_LIBRARY_INSTALLED = False

if GIT_LIBRARY_INSTALLED:
    from pathlib import Path
    from os.path import dirname, abspath, join

    try:
        KTBS_WD = str(Path(__file__).parent.parent.parent)
            
    except NameError:
        # __file__ is not define in py2exe
        pass

    if len(KTBS_WD) > 0:
        __commitno__ = get_git_infos(KTBS_WD)
