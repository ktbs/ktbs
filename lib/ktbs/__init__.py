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


__version__  = "0.4"
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
                commit_no = repo.active_branch.commit.hexsha
            else:
                lcommits = repo.commits(start=repo.active_branch, max_count=1)
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
    from pkg_resources import get_distribution, DistributionNotFound
    from os.path import dirname, abspath, join

    KTBS_WD = ""

    try:
        kp = get_distribution('kTBS')
        KTBS_PKG_INSTALLED = True
        KTBS_WD = kp.location
        if KTBS_WD.endswith('lib'):
            KTBS_WD = dirname(KTBS_WD)

    except DistributionNotFound:
        KTBS_PKG_INSTALLED = False

    if not KTBS_PKG_INSTALLED:
        try:
            KTBS_WD = dirname(dirname(abspath(__file__)))
            
        except NameError:
            # __file__ is not define in py2exe
            pass

    if len(KTBS_WD) > 0:
        __commitno__ = get_git_infos(KTBS_WD)
