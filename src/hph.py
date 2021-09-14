#!/usr/bin/python
#
# Copyright 2021 Christophe Levantis
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
    This is a pattern highlighter taylored for hexadecimal data.
"""

import sys
import argparse
import re


def substring_analysis(data, max_len=48, substr_len=4, stride=1, remove_comment=True):
    """
    Cut data in substrings of length sub_size using a stride stride and
    return a dictionary of these substrings with the line number where they occur.
    """

    substr_dict = {}

    for line_number, line in enumerate(data):
        # If the line starts with #, it's a comment
        if remove_comment and line.startswith('#'):
            continue

        # Strip spaces at end of line
        line = line.rstrip()

        # Cut the string in substrings of length substr_len with a stride stride
        last_offset = min(max_len, len(line))
        last_offset = last_offset - (substr_len - 1)
        idx = list(range(0, last_offset, stride))
        substr_list = [ line[i:i+substr_len] for i in idx ]

        # Add reference to a substring
        for substr in substr_list:
            substr_dict.setdefault(substr, []).append(line_number)

    return substr_dict


def generate_html(string_list, filename='output.html'):
    """
    Generate a HTML document given a list of strings.
    """

    html_doc = """<!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" type="text/css" href="./web/set.css">
</head>
<body>
"""

    with open(filename, 'w') as fout:
        fout.write(html_doc)

        for string in string_list:
            fout.write("""<div class="results">\n""")
            fout.write(string)
            fout.write("\n</div>\n")

        fout.write("</body></html>")


def substrings_to_set(substrings_dict):
    """
    Transform a dictionary of substring occurences into a dictionary of substrings set.
    A set represents the same lines where some substrings occur.
    """

    matching_substr = [ (k, v) for k, v in substrings_dict.items() if len(v) > 1 ]

    # Create a dictionary of sets of matching strings indexes
    # keys are a set string and values are substrings
    set_dict = {}
    for key_value in matching_substr:
        substr, match_list = key_value[0], key_value[1]
        lines_set = set(match_list)
        if len(lines_set) > 1:
            set_str = ' '.join([ str(x) for x in lines_set ])
            set_dict.setdefault(set_str, []).append(substr)

    # Create a dictionary with substrings as keys and index of set as values
    pattern_dict = {}
    for index, key in enumerate(set_dict.keys()):
        for k in set_dict[key]:
            pattern_dict[k] = index

    return pattern_dict

def highlight_substrings(substr_list, set_list, stride):
    """
    Format data in order to highlight chunks of data according to their set.
    """

    new_s = []
    prev_set = None
    for idx, substr in enumerate(substr_list):
        substr_set = set_list[idx]

        if prev_set is None and substr_set is None:
            new_s.append(substr[0:stride])

        elif prev_set is None and substr_set is not None:
            new_s.append("""<span class="set_{0}">""".format(substr_set))
            new_s.append(substr[0:stride])

        elif prev_set is not None and substr_set is not None:
            if prev_set != substr_set:
                new_s.append("""</span><span class="set_{0}">""".format(substr_set))
            new_s.append(substr[0:stride])

        elif prev_set is not None and substr_set is None:
            # Previous substring belong to a set and current substring does not belong to a set
            new_s.append("""</span>""")
            new_s.append(substr[0:stride])

        prev_set = substr_set


    # Check if last set was None, if not end it properly
    if substr_set is not None:
        new_s.append("""</span>""")

    return "".join(new_s)


def hex_pat(data, max_len, substr_len, stride, test=False):
    """
    Take strings as input and return highlighted common patterns.
    """
    # TODO: hardcoded values need to be replaced

    substr_dict = substring_analysis(data, max_len, substr_len, stride)

    substr_set_dict = substrings_to_set(substr_dict)

    # Reconstruct data and highlight patterns
    # The reconstruction uses the following algorithm:
    # data : 00112233445566
    # substring length = 8, stride = 2
    #
    # 00112233
    # < ---- >      substring length
    #   11223344
    # <>            stride
    # ^^            data chunk used for reconstruction
    #
    #
    # Work with data of length stride of a substring to reconstruct the whole data
    # When 2 substrings with different sets overlap, the first set is kept.
    # When there is no set, use the previous encountered set.

    results = []

    for line in data:
        if line.startswith('#'):
            continue

        line = line.rstrip()

        # Truncate data if too big
        last_offset = min(max_len, len(line))
        last_offset = last_offset - (substr_len - 1)

        # Cut data into chunk of length substr_len
        idx = list(range(0, last_offset, stride))
        substr_list = [ line[i:i+substr_len] for i in idx ]

        # Generate set for substrings
        list_set = [ substr_set_dict.get(s) for s in substr_list ]

        # Duplicate last set for the number of chunks
        list_set += ( [ list_set[-1] ] * 3)

        # Initialise variable for the start of reconstruction
        list_set = ([ list_set[0] ] * 4) + list_set
        list_set.reverse()

        # Replace no set data by previous set if possible
        new_set = list(list_set)
        for i in range(len(list_set) - 3):
            new_set[i] = list_set[i+3]
            if list_set[i+3] is None:
                for k in range(3,-1, -1):
                    if list_set[i+k] is not None:
                        new_set[i] = list_set[i+k]
                        break

        new_set.reverse()
        new_set = new_set[4:]

        # Cut last substring into chunks for reconstruction
        last_item = substr_list[-1]
        chunks = [ last_item[idx:idx+stride] for idx in range(stride, substr_len, stride) ]
        substr_list += chunks

        hled_data = highlight_substrings(substr_list, new_set, stride)
        results.append(hled_data)

        # Test if reconstructed data is the same as the original.
        if test:
            rec_data = re.sub('<.*?>', '', hled_data)
            if rec_data != line:
                print("--Original and reconstructed data are different:")
                print(line)
                print(rec_data)

    return results

# Lambda handler for AWS
def lambda_handler(event, context):
    """
    This is a AWS serverless lambda handler function.
    """

    print("In lambda handler")
    print(event)

    lines = event['body'].split("\n")

    max_len = 4096
    substr_len = 8
    stride = 2
    test = False

    results = hex_pat(lines, max_len, substr_len, stride, test)

    resp = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
        },
        "body": ""
    }
    body = ""
    for string in results:
        body += """<div class="results">\n"""
        body += string
        body += "\n</div>\n"
    resp['body'] = "".join(body)
    print(resp)

    return resp


if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description='Find data parts common to payload')
    parser.add_argument("-d", "--stride", help="stride (in byte)",
                        action='store', type=int, default=2)
    parser.add_argument("-m", "--max_len", help="truncate data to max bytes",
                        action='store', type=int, default=2048)
    parser.add_argument("-s", "--size", help="size of pattern / chunk in byte",
                        action='store', type=int, default=8)
    parser.add_argument("-f", "--file", help="file containing hex data  \
                        (one per line, # for comment, on separate line)", action='store')
    parser.add_argument("-t", "--test", help="test if reconstructed data matches original data \
                        (allows to detect bugs)", action='store_true', default=False)

    args = parser.parse_args()

    if args.file is None:
        parser.print_help(sys.stderr)
        sys.exit(0)

    if not sys.argv:
        sys.exit(1)

    with open(args.file, 'r') as fin:
        lines = fin.readlines()

    results = hex_pat(lines, args.max_len, args.size, args.stride, args.test)

    generate_html(results)
