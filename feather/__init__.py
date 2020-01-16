import jinja2
import sys
import argparse
import os
import re
import glob
from feather import parser


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_path', default=None)
    parser.add_argument('--template_path', default=None)
    args, _ = parser.parse_known_args(sys.argv)

    if not args.output_path or not args.template_path:
        print_help()
        return

    doc_entries, templates = parse_doc_entries(args.template_path)
    code_entries = parse_code_entries(doc_entries)
    output_documentation(templates, code_entries, args.output_path, args.template_path)


class DocEntry:
    def __init__(self):
        self.list_name = ''
        self.props = []
        self.optional_props = []
        self.files = []
        self.format = ''


def print_help():
    print('Usage: feather --output_path <path> --template_path <path>')


def parse_code_entries(doc_entries):
    code_entries = {}
    for filepath in glob.glob('**', recursive=True):
        matched_doc_entries = []
        for doc_entry in doc_entries:
            for ext in doc_entry.files:
                if filepath.endswith(ext):
                    matched_doc_entries.append(doc_entry)
                    break
        if matched_doc_entries:
            parse_code_entries_from_file(filepath, matched_doc_entries, code_entries)
    return code_entries


def parse_code_entries_from_file(filepath, matched_doc_entries, code_entries):
    props = set()
    for entry in matched_doc_entries:
        props.update(entry.optional_props)
        props.update(entry.props)

    with open(filepath, encoding='utf-8', mode='r') as file:
        data = file.read()
    cpp_parser = parser.CppParser()
    blocks = cpp_parser.parse(data, props)

    for block in blocks:
        block: parser.CodeBlock
        if block.props:
            matched_something = False
            for doc_entry in matched_doc_entries:
                m = re.search(doc_entry.format, block.blob)
                if doc_entry.format and m:
                    entry = {}
                    for key, value in block.props.items():
                        if key in doc_entry.props or key in doc_entry.optional_props:
                            entry[key] = value
                    for key, value in m.groupdict().items():
                        entry[key] = value

                    if not [prop for prop in doc_entry.props if prop not in entry]:
                        if doc_entry.list_name not in code_entries:
                            code_entries[doc_entry.list_name] = []
                        code_entries[doc_entry.list_name].append(entry)
                        matched_something = True
                        print("Got entry", entry, "for list", doc_entry.list_name, "in file", filepath)
            if not matched_something:
                print("WARNING: Comment block at line %s in file %s did not match any rule." % (block.line, filepath))
                print("Code after comment:", repr(block.blob[0:50]))


def parse_doc_entries(path):
    config_path = os.path.join(path, '.feather')
    doc_entries = []
    templates = set()
    current_entry = None
    with open(config_path, encoding='utf-8', mode='r') as file:
        in_entry = False
        for line in file:
            line = line.rstrip()
            if not in_entry:
                if line == '$ENTRY':
                    current_entry = DocEntry()
                    in_entry = True
            elif line == '$END' and current_entry:
                doc_entries.append(current_entry)
                current_entry = None
                in_entry = False
            else:
                match = re.search('(\\w+)=(.*)', line)
                if match:
                    key = match.group(1)
                    value = match.group(2)
                    if key == 'list':
                        current_entry.list_name = value
                    elif key == 'format':
                        current_entry.format = value
                    elif key == 'props':
                        values = value.split(',')
                        current_entry.props = values
                    elif key == 'optional_props':
                        values = value.split(',')
                        current_entry.optional_props = values
                    elif key == 'ext':
                        current_entry.files = value.split(',')
                    else:
                        raise Exception('Unidentified key %s' % key)
    for filepath in glob.glob(os.path.join(path, '**')):
        if filepath.endswith('.jinja2'):
            templates.add(filepath)
    return doc_entries, templates


def output_documentation(templates, code_entries, output_path, template_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path))
    for template_path in templates:
        template = env.get_template(os.path.basename(template_path))
        output = template.render(**code_entries)
        template_name = os.path.splitext(os.path.basename(template_path))[0]
        output_filepath = os.path.join(output_path, template_name + '.md')
        with open(output_filepath, mode='w', encoding='utf-8') as fp:
            fp.write(output)
    print("Templates written: %s" % len(templates))