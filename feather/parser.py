from enum import Enum
import re


class CodeBlock:
    def __init__(self, line_no):
        self.props = {}
        self.comment = '\n'
        self.blob = ''
        self.line = line_no

    def finalize(self, props):
        self.blob = self.blob.strip()
        self.blob = self.blob[:self.blob.find('\n')]
        matches = re.finditer('\n(\\s|/|\\*)*([^:]*):\\s+(.*)', self.comment, re.M)
        for match in matches:
            key = match.group(2)
            value = match.group(3)
            if not props or key in props:
                self.props[key] = value
        self.comment = self.comment.strip()

    def __bool__(self):
        return bool(self.comment)


class ParserState(Enum):
    IN_SLASH = 0
    IN_SLASH_NEWLINE = 1
    IN_BLOCK = 2
    IN_TEXT = 3


class CppParser:
    def __init__(self):
        self.parser_state = ParserState.IN_TEXT
        self.current_block = None
        self.index = 0
        self.data = None
        self.data_len = 0
        self.blocks = []
        self.props = set()
        self.line = 1

    def reset(self):
        self.parser_state = ParserState.IN_TEXT
        self.current_block = None
        self.index = 0
        self.data = None
        self.blocks = []
        self.data_len = 0
        self.props = set()

    def parse(self, data, props):
        self.reset()
        self.data = data.replace('\\\n', '')
        self.data_len = len(self.data)
        self.props = props

        for self.index in range(self.data_len):
            self.parse_char()

        self.start_new_block()
        return self.blocks

    def start_new_block(self):
        if self.current_block:
            self.current_block.finalize(self.props)
            self.blocks.append(self.current_block)
        self.current_block = CodeBlock(self.line)

    def change_state(self, new_state):
        if new_state == ParserState.IN_SLASH and not self.parser_state == ParserState.IN_SLASH_NEWLINE:
            self.start_new_block()
        elif new_state == ParserState.IN_BLOCK:
            self.start_new_block()
        self.parser_state = new_state

    def parse_normal_char(self):
        if self.parser_state == ParserState.IN_SLASH_NEWLINE:
            self.change_state(ParserState.IN_TEXT)

    def is_end_of_block(self):
        surrounding = self.data[self.index - 1:self.index + 1]
        return self.index > 0 and surrounding == '*/'

    def is_start_of_block(self):
        return self.index < self.data_len -1 and self.data[self.index:self.index+2] == '/*'

    def is_start_of_slash(self):
        return self.index < self.data_len -1 and self.data[self.index:self.index+2] == '//'

    def parse_slash(self):
        current = self.data[self.index:]
        if self.is_end_of_block() and self.parser_state == ParserState.IN_BLOCK:
            self.change_state(ParserState.IN_TEXT)
        elif self.is_start_of_block() and self.parser_state != ParserState.IN_BLOCK:
            self.change_state(ParserState.IN_BLOCK)
        elif self.is_start_of_slash():
            if self.parser_state == ParserState.IN_SLASH_NEWLINE or self.parser_state == ParserState.IN_TEXT:
                self.change_state(ParserState.IN_SLASH)

    def parse_newline(self):
        if self.parser_state == ParserState.IN_SLASH:
            self.change_state(ParserState.IN_SLASH_NEWLINE)
        self.line += 1

    def parse_char(self):
        char = self.data[self.index]
        prev_state = self.parser_state

        if char == '/':
            self.parse_slash()
        elif char == '\n':
            self.parse_newline()
        elif not char.isspace():
            self.parse_normal_char()

        if self.current_block and self.parser_state == ParserState.IN_TEXT and not prev_state == ParserState.IN_BLOCK:
            self.current_block.blob += char
        elif self.current_block:
            self.current_block.comment += char
