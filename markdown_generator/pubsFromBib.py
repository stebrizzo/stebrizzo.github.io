#!/usr/bin/env python
# coding: utf-8

from pybtex.database.input import bibtex
from time import strptime
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


# ---------------------------------------------------------------------
# HTML escaping
# ---------------------------------------------------------------------

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;"
}


def html_escape(text):
    """Replace characters that may cause problems in generated HTML/YAML."""
    return "".join(html_escape_table.get(c, c) for c in text)


# ---------------------------------------------------------------------
# Ensure output directory exists
# ---------------------------------------------------------------------

os.makedirs("../_publications", exist_ok=True)


# ---------------------------------------------------------------------
# Process BibTeX files
# ---------------------------------------------------------------------

for pubsource in publist:

    parser = bibtex.Parser()
    bibdata = parser.parse_file(publist[pubsource]["file"])

    for bib_id in bibdata.entries:

        # Default date if month/day are not supplied
        pub_year = "1900"
        pub_month = "01"
        pub_day = "01"

        b = bibdata.entries[bib_id].fields

        try:
            # ---------------------------------------------------------
            # Publication date
            # ---------------------------------------------------------

            pub_year = str(b["year"])

            if "month" in b:
                month_value = str(b["month"]).strip()

                # Numeric month
                if month_value.isdigit():
                    pub_month = month_value.zfill(2)

                # Text month, e.g. Jan, January
                else:
                    try:
                        tmnth = strptime(month_value[:3], "%b").tm_mon
                        pub_month = f"{tmnth:02d}"
                    except ValueError:
                        pub_month = "01"

            if "day" in b:
                pub_day = str(b["day"]).zfill(2)

            pub_date = f"{pub_year}-{pub_month}-{pub_day}"

            # ---------------------------------------------------------
            # Clean title
            # ---------------------------------------------------------

            title = (
                b["title"]
                .replace("{", "")
                .replace("}", "")
                .replace("\\", "")
            )

            # Title used for filename/permalink
            clean_title = title.replace(" ", "-")

            url_slug = re.sub(
                r"\[.*\]|[^a-zA-Z0-9_-]",
                "",
                clean_title
            )

            # Remove repeated hyphens
            url_slug = re.sub(r"-+", "-", url_slug).strip("-")

            md_filename = f"{pub_date}-{url_slug}.md"
            html_filename = f"{pub_date}-{url_slug}"

            # ---------------------------------------------------------
            # Venue
            # ---------------------------------------------------------

            venue = (
                publist[pubsource]["venue-pretext"]
                + b[publist[pubsource]["venuekey"]]
                .replace("{", "")
                .replace("}", "")
                .replace("\\", "")
            )

            # ---------------------------------------------------------
            # YAML front matter
            # ---------------------------------------------------------

            md = "---\n"

            md += 'title: "' + html_escape(title) + '"\n'

            md += (
                "collection: "
                + publist[pubsource]["collection"]["name"]
                + "\n"
            )

            md += (
                "category: "
                + publist[pubsource]["category"]
                + "\n"
            )

            md += (
                "permalink: "
                + publist[pubsource]["collection"]["permalink"]
                + html_filename
                + "\n"
            )

            # Optional note
            note = False

            if "note" in b:
                if len(str(b["note"]).strip()) > 0:
                    md += (
                        "excerpt: '"
                        + html_escape(str(b["note"]).strip())
                        + "'\n"
                    )
                    note = True

            md += "date: " + pub_date + "\n"

            md += (
                "venue: '"
                + html_escape(venue)
                + "'\n"
            )

            # Optional paper URL
            url = False

            if "url" in b:
                paper_url = str(b["url"]).strip()

                if len(paper_url) > 0:
                    md += (
                        "paperurl: '"
                        + paper_url
                        + "'\n"
                    )
                    url = True

            md += "---\n"

            # ---------------------------------------------------------
            # Individual publication page content
            # ---------------------------------------------------------

            if note:
                md += "\n" + html_escape(str(b["note"]).strip()) + "\n"

            if url:
                md += (
                    "\n[Access paper here]("
                    + paper_url
                    + '){:target="_blank"}\n'
                )

            # ---------------------------------------------------------
            # Write Markdown file
            # ---------------------------------------------------------

            md_filename = os.path.basename(md_filename)

            output_path = os.path.join(
                "../_publications",
                md_filename
            )

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(md)

            print(
                f'SUCCESSFULLY PARSED {bib_id}: '
                f'"{title[:60]}'
                f'{"..." if len(title) > 60 else ""}"'
            )

        except KeyError as e:

            title_for_warning = b.get("title", "")

            print(
                f'WARNING Missing Expected Field {e} '
                f'from entry {bib_id}: '
                f'"{title_for_warning[:30]}'
                f'{"..." if len(title_for_warning) > 30 else ""}"'
            )

            continue
