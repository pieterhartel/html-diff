# HTML-Diff
#
# Copyright (C) 2019 Quentin Wenger
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import argparse
import html
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
import re
import sys
import timeit
import traceback
from urllib.parse import parse_qs

import bs4

from html_diff import diff
from html_diff.check import is_diff_valid
from html_diff.config import Config
from html_diff.config import config



html_template = """
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>HTML-Diff test</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css"/>
        <style>
            ins {{
                color: #00f;
                font-decoration: underline;
                text-decoration-style: wavy;
            }}
            del {{
                color: #f00;
                font-decoration: line-through;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="py-5 text-center">
                <h2>HTML-Diff test</h2>
            </div>
            <form method="post">
                <div class="mb-3">
                    <label for="old">Old string</label>
                    <input type="text" class="form-control" name="old" id="old" value='{old}' autofocus>
                </div>
                <div class="mb-3">
                    <label for="new">New string</label>
                    <input type="text" class="form-control" name="new" id="new" value='{new}'>
                </div>
                <div class="mb-3">
                    <button type="submit" class="btn btn-primary">Compute</button>
                </div>
            </form>
            <label for="old_rendered">Old</label>
            <div class="text-center card card-body bg-light" id="old_rendered">
                {old_rendered}
            </div>
            <label for="new_rendered">New</label>
            <div class="text-center card card-body bg-light" id="new_rendered">
                {new_rendered}
            </div>
            <label for="diff">Diff</label>
            <pre>
                {diff_escaped}
            </pre>
            <div class="text-center card" id="diff">
                <div class="card-body bg-light">
                    {diff}
                </div>
            </div>
            <div>
                <label>Diff test passed: {test_passed}</label>
            </div>
            <div>
                <label>Mean run time (10 runs): {mean_time}</label>
            </div>
        </div>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.bundle.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>
    </body>
</html>
"""


class TestRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes(html_template.format(
            old="",
            new="",
            old_rendered="",
            new_rendered="",
            diff="",
            diff_escaped="",
            test_passed="-",
            mean_time="-",
        ), "utf-8"))
        return
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        qs = parse_qs(self.rfile.read(content_length).decode("utf-8"))
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        try:
            # NOTE: Make a round-trip through bs4 to ensure validity or trigger errpr.
            if "old" in qs:
                old = str(bs4.BeautifulSoup(qs["old"][0], "html.parser"))
            else:
                old = ""
            if "new" in qs:
                new = str(bs4.BeautifulSoup(qs["new"][0], "html.parser"))
            else:
                new = ""
            diff_raw = diff(old, new)
            old_rendered = old
            new_rendered = new
            mean_time = "{:.5f}s".format(timeit.timeit(lambda: diff(old, new), number=10)/10.0)
        except Exception as e:
            old_rendered = ""
            new_rendered = ""
            diff_raw = "<h3>{}</h3><pre>{}</pre>".format(e, traceback.format_exc())
            mean_time = "-"
        self.wfile.write(bytes(html_template.format(
            old=html.escape(old),
            new=html.escape(new),
            old_rendered=old_rendered,
            new_rendered=new_rendered,
            diff=diff_raw,
            diff_escaped=html.escape(diff_raw),
            test_passed=str(is_diff_valid(old, new, diff_raw)),
            mean_time=mean_time,
        ), "utf-8"))
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serve an HTML-Diff test page.")
    parser.add_argument("-a", "--address", help="address of the server")
    parser.add_argument("-p", "--port", help="port of the server", type=int)
    parser.add_argument(
        "-b",
        "--blocks",
        help="definitions of tag -> bool functions to append to tags_fcts_as_blocks",
        action="append",
    )
    parser.add_argument(
        "-c",
        "--cuttable-words-mode",
        help="cuttable words mode, one of {} (default: CUTTABLE)".format(", ".join(m.name for m in Config.CuttableWordsMode)),
        type=lambda c: Config.CuttableWordsMode[c],
        choices=Config.CuttableWordsMode,
        default=Config.CuttableWordsMode.CUTTABLE,
        metavar="CUTTABLE_MODE",
    )
    args = parser.parse_args()
    if args.blocks is not None:
        for fct_def in args.blocks:
            config.tags_fcts_as_blocks.append(eval(fct_def))
    config.cuttable_words_mode = args.cuttable_words_mode
    print("Starting server...")
    address = "127.0.0.1" if args.address is None else args.address
    port = 8080 if args.port is None else args.port
    httpd = HTTPServer((address, port), TestRequestHandler)
    print("Running server...")
    httpd.serve_forever()

