#!/usr/bin/env python
# coding: utf-8

from pybtex.database.input import bibtex
from time import strptime
import html
import os
import re


# ---------------------------------------------------------------------
# Publication sources
#
# pubs.bib        -> Journal Articles
# proceedings.bib -> Conference Papers
# ---------------------------------------------------------------------

publist = {
    "proceeding": {
        "file": "proceedings.bib",
        "venuekey": "booktitle",
        "venue-pretext": "In the proceedings of ",
        "category": "conferences",
        "collection": {
            "name": "publications",
            "permalink": "/publication/"
        }
    },

    "journal": {
        "file": "pubs.bib",
        "venuekey": "journal",
        "venue-pretext": "",
        "category": "manuscripts",
        "collection": {
            "name": "publications",
            "permalink": "/publication/"
        }
    }
}


html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;"
}


def html_escape(text):
    """Produce HTML entities within text."""
    return "".join(html_escape_table.get(c, c) for c in text)


# Make sure the output directory exists
os.makedirs("../_publications", exist_ok=True)


for pubsource in publist:

    parser = bibtex.Parser()
    bibdata = parser.parse_file(publist[pubsource]["file"])

    # Loop through individual references
    for bib_id in bibdata.entries:

        pub_year = "1900"
        pub_month = "01"
        pub_day = "01"

        b = bibdata.entries[bib_id].fields

        try:
            pub_year = f'{b["year"]}'

            # Month
            if "month" in b.keys():
                if len(b["month"]) < 3:
                    pub_month = "0" + b["month"]
                    pub_month = pub_month[-2:]
                else:
                    try:
                        tmnth = strptime(b["month"][:3], "%b").tm_mon
                        pub_month = "{:02d}".format(tmnth)
                    except ValueError:
                        pub_month = str(b["month"])

            # Day
            if "day" in b.keys():
                pub_day = str(b["day"]).zfill(2)

            pub_date = pub_year + "-" + pub_month + "-" + pub_day

            # Clean title for filename / URL
            clean_title = (
                b["title"]
                .replace("{", "")
                .replace("}", "")
                .replace("\\", "")
                .replace(" ", "-")
            )

            url_slug = re.sub(r"\[.*\]|[^a-zA-Z0-9_-]", "", clean_title)
            url_slug = url_slug.replace("--", "-")

            md_filename = (
                str(pub_date) + "-" + url_slug + ".md"
            ).replace("--", "-")

            html_filename = (
                str(pub_date) + "-" + url_slug
            ).replace("--", "-")

            # ---------------------------------------------------------
            # Build citation
            # ---------------------------------------------------------

            citation = ""

            for author in bibdata.entries[bib_id].persons["author"]:
                citation += (
                    " "
                    + author.first_names[0]
                    + " "
                    + author.last_names[0]
                    + ", "
                )

            citation += (
                "\""
                + html_escape(
                    b["title"]
                    .replace("{", "")
                    .replace("}", "")
                    .replace("\\", "")
                )
                + ".\""
            )

            venue = (
                publist[pubsource]["venue-pretext"]
                + b[publist[pubsource]["venuekey"]]
                .replace("{", "")
                .replace("}", "")
                .replace("\\", "")
            )

            citation += " " + html_escape(venue)
            citation += ", " + pub_year + "."

            # ---------------------------------------------------------
            # YAML front matter
            # ---------------------------------------------------------

            md = (
                "---\n"
                + 'title: "'
                + html_escape(
                    b["title"]
                    .replace("{", "")
                    .replace("}", "")
                    .replace("\\", "")
                )
                + '"\n'
            )

            md += (
                "collection: "
                + publist[pubsource]["collection"]["name"]
            )

            # THIS IS THE IMPORTANT LINE
            md += (
                "\ncategory: "
                + publist[pubsource]["category"]
            )

            md += (
                "\npermalink: "
                + publist[pubsource]["collection"]["permalink"]
                + html_filename
            )

            note = False

            if "note" in b.keys():
                if len(str(b["note"])) > 5:
                    md += (
                        "\nexcerpt: '"
                        + html_escape(b["note"])
                        + "'"
                    )
                    note = True

            md += "\ndate: " + str(pub_date)

            md += "\nvenue: '" + html_escape(venue) + "'"

            url = False

            if "url" in b.keys():
                if len(str(b["url"])) > 5:
                    md += "\npaperurl: '" + b["url"] + "'"
                    url = True


            md += "\n---"

            # ---------------------------------------------------------
            # Individual publication page
            # ---------------------------------------------------------

            if note:
                md += "\n" + html_escape(b["note"]) + "\n"

            if url:
                md += (
                    "\n[Access paper here]("
                    + b["url"]
                    + '){:target="_blank"}\n'
                )
            else:
                md += (
                    "\nUse [Google Scholar]"
                    "(https://scholar.google.com/scholar?q="
                    + html.escape(clean_title.replace("-", "+"))
                    + '){:target="_blank"} for full citation'
                )

            md_filename = os.path.basename(md_filename)

            with open(
                "../_publications/" + md_filename,
                "w",
                encoding="utf-8"
            ) as f:
                f.write(md)

            print(
                f'SUCCESSFULLY PARSED {bib_id}: "',
                b["title"][:60],
                "..." * (len(b["title"]) > 60),
                '"'
            )

        except KeyError as e:
            print(
                f'WARNING Missing Expected Field {e} '
                f'from entry {bib_id}: "',
                b.get("title", "")[:30],
                "..." * (len(b.get("title", "")) > 30),
                '"'
            )
            continue
