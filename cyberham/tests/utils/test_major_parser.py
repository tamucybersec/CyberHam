import cyberham.utils.major_parser as parser


# just a utility so I can scrape a list of majors from the undergrad catalog
# https://catalog.tamu.edu/graduate/degrees-programs/
def test_major_parser():
    assert True, "parse only when necessary"
    return

    div = parser.get_html_file("majors.html")
    majors = parser.extract_major_names(div)
    majors.sort()
    parser.save_rows_to_json(majors)
