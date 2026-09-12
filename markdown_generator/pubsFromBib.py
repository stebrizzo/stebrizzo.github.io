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
    "journal": {
        "file": "pubs.bib",
        "venuekey": "journal",
        "category": "manuscripts",
        "collection": {
            "name": "publications",
            "permalink": "/publication/"
        }
    },

    "proceeding": {
        "file": "proceedings.bib",
        "venuekey": "booktitle",
        "category": "conferences",
        "collection": {
            "name": "publications",
            "permalink": "/publication/"
        }
    }
}


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def clean_text(text):
    """
    Remove simple BibTeX/LaTeX formatting characters that are not needed
    in the generated Markdown/YAML.
    """
    if text is None:
        return ""

    text = str(text)

    text = text.replace("{", "")
    text = text.replace("}", "")
    text = text.replace(r"\&", "&")

    return text.strip()


def yaml_escape(text):
    """
    Escape a string so that it can safely be written between double
    quotes in YAML front matter.
    """
    text = clean_text(text)
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    return text


def make_slug(text):
    """
    Generate a clean URL/filename slug from a publication title.
    """
    text = clean_text(text)

    # Spaces -> hyphens
    text = text.replace(" ", "-")

    # Keep only safe filename characters
    text = re.sub(r"[^a-zA-Z0-9_-]", "", text)

    # Collapse repeated hyphens
    text = re.sub(r"-+", "-", text)

    return text.strip("-")


def get_publication_date(fields):
    """
    Construct YYYY-MM-DD from BibTeX fields.
    Defaults to January 1 when month/day are missing.
    """

    pub_year = str(fields["year"])
    pub_month = "01"
    pub_day = "01"

    if "month" in fields:

        month_value = clean_text(fields["month"])

        if month_value.isdigit():
            pub_month = month_value.zfill(2)

        else:
            try:
                month_number = strptime(
                    month_value[:3],
                    "%b"
                ).tm_mon

                pub_month = f"{month_number:02d}"

            except ValueError:
                pub_month = "01"

    if "day" in fields:
        pub_day = clean_text(fields["day"]).zfill(2)

    return f"{pub_year}-{pub_month}-{pub_day}"


def get_authors(entry):
    """
    Convert Pybtex author objects into a readable
    'First Middle Last, First Last, ...' string.
    """

    authors = []

    for author in entry.persons.get("author", []):

        name_parts = []

        name_parts.extend(author.first_names)
        name_parts.extend(author.middle_names)
        name_parts.extend(author.prelast_names)
        name_parts.extend(author.last_names)
        name_parts.extend(author.lineage_names)

        name = " ".join(name_parts)
        name = clean_text(name)

        authors.append(name)

    return ", ".join(authors)


def get_paper_url(fields):
    """
    Prefer the BibTeX url field.
    If it is absent, generate a DOI URL when a DOI is available.
    """

    if "url" in fields:
        url = clean_text(fields["url"])

        if url:
            return url

    if "doi" in fields:
        doi = clean_text(fields["doi"])

        if doi:
            doi = re.sub(
                r"^https?://(dx\.)?doi\.org/",
                "",
                doi
            )

            return "https://doi.org/" + doi

    return ""


# ---------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------

output_directory = "../_publications"

os.makedirs(
    output_directory,
    exist_ok=True
)


# ---------------------------------------------------------------------
# Process publication sources
# ---------------------------------------------------------------------

for pubsource, source_config in publist.items():

    bib_file = source_config["file"]

    print(f"\nReading {bib_file}...")

    parser = bibtex.Parser()
    bibdata = parser.parse_file(bib_file)

    # -----------------------------------------------------------------
    # Process each BibTeX entry
    # -----------------------------------------------------------------

    for bib_id, entry in bibdata.entries.items():

        fields = entry.fields

        try:

            # ---------------------------------------------------------
            # Required fields
            # ---------------------------------------------------------

            title = clean_text(fields["title"])
            pub_year = clean_text(fields["year"])

            venue_key = source_config["venuekey"]
            venue = clean_text(fields[venue_key])

            # ---------------------------------------------------------
            # Authors
            # ---------------------------------------------------------

            authors = get_authors(entry)

            # ---------------------------------------------------------
            # Date
            # ---------------------------------------------------------

            pub_date = get_publication_date(fields)

            # ---------------------------------------------------------
            # Filename and permalink
            # ---------------------------------------------------------

            slug = make_slug(title)

            md_filename = (
                f"{pub_date}-{slug}.md"
            )

            html_filename = (
                f"{pub_date}-{slug}"
            )

            permalink = (
                source_config["collection"]["permalink"]
                + html_filename
            )

            # ---------------------------------------------------------
            # Paper URL
            # ---------------------------------------------------------

            paper_url = get_paper_url(fields)

            # ---------------------------------------------------------
            # Optional note
            # ---------------------------------------------------------

            note = ""

            if "note" in fields:
                note = clean_text(fields["note"])

            # ---------------------------------------------------------
            # YAML front matter
            # ---------------------------------------------------------

            md = "---\n"

            md += (
                'title: "'
                + yaml_escape(title)
                + '"\n'
            )

            md += (
                "collection: "
                + source_config["collection"]["name"]
                + "\n"
            )

            md += (
                "category: "
                + source_config["category"]
                + "\n"
            )

            md += (
                'authors: "'
                + yaml_escape(authors)
                + '"\n'
            )

            md += (
                'venue: "'
                + yaml_escape(venue)
                + '"\n'
            )

            md += (
                "date: "
                + pub_date
                + "\n"
            )

            md += (
                "permalink: "
                + permalink
                + "\n"
            )

            if paper_url:
                md += (
                    'paperurl: "'
                    + yaml_escape(paper_url)
                    + '"\n'
                )

            if note:
                md += (
                    'excerpt: "'
                    + yaml_escape(note)
                    + '"\n'
                )

            md += "---\n"

            # ---------------------------------------------------------
            # Individual publication page
            # ---------------------------------------------------------

            if note:
                md += "\n" + note + "\n"

            if paper_url:
                md += (
                    "\n[Access paper here]("
                    + paper_url
                    + '){:target="_blank"}\n'
                )

            # ---------------------------------------------------------
            # Write generated Markdown file
            # ---------------------------------------------------------

            output_path = os.path.join(
                output_directory,
                os.path.basename(md_filename)
            )

            with open(
                output_path,
                "w",
                encoding="utf-8"
            ) as f:
                f.write(md)

            print(
                f'SUCCESSFULLY PARSED {bib_id}: '
                f'"{title[:70]}'
                f'{"..." if len(title) > 70 else ""}"'
            )

        except KeyError as error:

            title_for_warning = clean_text(
                fields.get("title", "")
            )

            print(
                f'WARNING: Missing expected field {error} '
                f'in entry {bib_id}: '
                f'"{title_for_warning[:50]}"'
            )

            continue
