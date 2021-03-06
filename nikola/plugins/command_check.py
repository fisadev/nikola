# Copyright (c) 2012 Roberto Alsina y otros.

# Permission is hereby granted, free of charge, to any
# person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the
# Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice
# shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from __future__ import print_function
from optparse import OptionParser
import os
import sys
try:
    from urllib import unquote
    from urlparse import urlparse
except ImportError:
    from urllib.parse import unquote, urlparse

import lxml.html

from nikola.plugin_categories import Command


class CommandCheck(Command):
    """Check the generated site."""

    name = "check"

    def run(self, *args):
        """Check the generated site."""
        parser = OptionParser(usage="nikola %s [options]" % self.name)
        parser.add_option('-l', '--check-links', dest='links',
            action='store_true',
            help='Check for dangling links.')
        parser.add_option('-f', '--check-files', dest='files',
            action='store_true',
            help='Check for unknown files.')

        (options, args) = parser.parse_args(list(args))
        if options.links:
            scan_links()
        if options.files:
            scan_files()

existing_targets = set([])


def analize(task):
    try:
        filename = task.split(":")[-1]
        d = lxml.html.fromstring(open(filename).read())
        for l in d.iterlinks():
            target = l[0].attrib[l[1]]
            if target == "#":
                continue
            parsed = urlparse(target)
            if parsed.scheme:
                continue
            if parsed.fragment:
                target = target.split('#')[0]
            target_filename = os.path.abspath(
                os.path.join(os.path.dirname(filename),
                    unquote(target)))
            if target_filename not in existing_targets:
                if os.path.exists(target_filename):
                    existing_targets.add(target_filename)
                else:
                    print("In %s broken link: " % filename, target)
                    if '--find-sources' in sys.argv:
                        print("Possible sources:")
                        print(os.popen(
                            'nikola build list --deps %s' % task, 'r').read())
                        print("===============================\n")

    except Exception as exc:
        print("Error with:", filename, exc)


def scan_links():
    print("Checking Links:\n===============\n")
    for task in os.popen('nikola build list --all', 'r').readlines():
        task = task.strip()
        if task.split(':')[0] in (
            'render_tags',
            'render_archive',
            'render_galleries',
            'render_indexes',
            'render_pages',
            'render_site') and '.html' in task:
            analize(task)


def scan_files():
    print("Checking Files:\n===============\n")
    task_fnames = set([])
    real_fnames = set([])
    # First check that all targets are generated in the right places
    for task in os.popen('nikola build list --all', 'r').readlines():
        task = task.strip()
        if 'output' in task and ':' in task:
            fname = task.split(':')[-1]
            task_fnames.add(fname)
     # And now check that there are no non-target files
    for root, dirs, files in os.walk('output'):
        for src_name in files:
            fname = os.path.join(root, src_name)
            real_fnames.add(fname)

    only_on_output = list(real_fnames - task_fnames)
    if only_on_output:
        only_on_output.sort()
        print("\nFiles from unknown origins:\n")
        for f in only_on_output:
            print(f)

    only_on_input = list(task_fnames - real_fnames)
    if only_on_input:
        only_on_input.sort()
        print("\nFiles not generated:\n")
        for f in only_on_input:
            print(f)
