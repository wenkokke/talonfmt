#!/usr/bin/env python3

import pathlib

import yaml  # type: ignore


def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, str_presenter)

# to use with safe_dump:
yaml.representer.SafeRepresenter.add_representer(str, str_presenter)

golden_dir = pathlib.Path(__file__).parent.parent / "tests" / "golden"

for golden_path in golden_dir.glob("**/*.yml"):
    contents = golden_path.read_text()
    golden = yaml.safe_load(contents)
    contents_formatted = yaml.safe_dump(golden)
    if contents != contents_formatted:
        print(f"Fixed {str(golden_path)}")
        golden_path.write_text(contents_formatted)
