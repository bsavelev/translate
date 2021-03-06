# -*- coding: utf-8 -*-
#
# Copyright 2004-2008,2012 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
#
# Requires: git
#

import os

from translate.storage.versioncontrol import (GenericRevisionControlSystem,
                                              prepare_filelist, run_command)


def is_available():
    """check if git is installed"""
    exitcode, output, error = run_command(["git", "--version"])
    return exitcode == 0


class git(GenericRevisionControlSystem):
    """Class to manage items under revision control of git."""

    RCS_METADIR = ".git"
    SCAN_PARENTS = True

    def _get_git_dir(self):
        """git requires the git metadata directory for every operation
        """
        return os.path.join(self.root_dir, self.RCS_METADIR)

    def _get_git_command(self, args):
        """prepends generic git arguments to default ones
        """
        command = ["git", "--git-dir", self._get_git_dir()]
        command.extend(args)
        return command

    def _has_changes(self):
        command = self._get_git_command(["diff", "--cached", "--exit-code"])
        exitcode, output_checkout, error = run_command(command, self.root_dir)
        return bool(exitcode)

    def update(self, revision=None, needs_revert=True):
        """Does a clean update of the given path"""
        output_checkout = ""
        if needs_revert:
            # git checkout
            command = self._get_git_command(["checkout", self.location_rel])
            exitcode, output_checkout, error = run_command(command, self.root_dir)
            if exitcode != 0:
                raise IOError("[GIT] checkout failed (%s): %s" % (command, error))

        # pull changes
        command = self._get_git_command(["pull"])
        exitcode, output_pull, error = run_command(command, self.root_dir)
        if exitcode != 0:
            raise IOError("[GIT] pull failed (%s): %s" % (command, error))
        return output_checkout + output_pull

    def add(self, files, message=None, author=None):
        """Add and commit the new files."""
        args = ["add"] + prepare_filelist(files)
        command = self._get_git_command(args)
        exitcode, output, error = run_command(command, self.root_dir)
        if exitcode != 0:
            raise IOError("[GIT] add of files in '%s') failed: %s" % (
                          self.root_dir, error))

        return output + self.commit(message, author, add=False)

    def commit(self, message=None, author=None, add=True):
        """Commits the file and supplies the given commit message if present"""
        # add the file
        output_add = ""
        if add:
            command = self._get_git_command(["add", self.location_rel])
            exitcode, output_add, error = run_command(command, self.root_dir)
            if exitcode != 0:
                raise IOError("[GIT] add of ('%s', '%s') failed: %s" % (
                              self.root_dir, self.location_rel, error))

        if not self._has_changes():
            raise IOError("[GIT] no changes to commit")

        # commit file
        command = self._get_git_command(["commit"])
        if message:
            command.extend(["-m", message])
        if author:
            command.extend(["--author", author])
        exitcode, output_commit, error = run_command(command, self.root_dir)
        if exitcode != 0:
            if len(error):
                msg = error
            else:
                msg = output_commit
            raise IOError("[GIT] commit of ('%s', '%s') failed: %s" % (
                          self.root_dir, self.location_rel, msg))
        # push changes
        command = self._get_git_command(["push"])
        exitcode, output_push, error = run_command(command, self.root_dir)
        if exitcode != 0:
            raise IOError("[GIT] push of ('%s', '%s') failed: %s" % (
                          self.root_dir, self.location_rel, error))
        return output_add + output_commit + output_push

    def getcleanfile(self, revision=None):
        """Get a clean version of a file from the git repository"""
        # run git-show
        command = self._get_git_command(["show", "HEAD:%s" % self.location_rel])
        exitcode, output, error = run_command(command, self.root_dir)
        if exitcode != 0:
            raise IOError("[GIT] 'show' failed for ('%s', %s): %s" % (
                          self.root_dir, self.location_rel, error))
        return output
