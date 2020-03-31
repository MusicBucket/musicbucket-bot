import re

OUTPUT_DATE_FORMAT = '%Y/%m/%d'


def to_snake_case(s):
    """
    Convert a string from camel case to snake case
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
