# custom string formatter for use with complex HTML/JS files

import re

class CustomFormatter:
    def __init__(self, delimiters=('<<', '>>')):
        self.open, self.close = delimiters

    def format(self, string_to_format, format_dictionary):
        all_items = re.findall(
            r'.*(' + self.open + r'(.*)' + self.close + r').*', 
            string_to_format
        )
        for sub, key in all_items:
            if key not in format_dictionary:
                raise KeyError(f'missing format key {key} in dictionary')
            string_to_format = string_to_format.replace(
                sub, format_dictionary[key]
            )
        return string_to_format
