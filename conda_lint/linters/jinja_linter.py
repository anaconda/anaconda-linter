from conda_lint.linters import BaseLinter

from jinja2 import Environment, BaseLoader
from ruamel.yaml import YAML
yaml = YAML(typ="safe", pure=True)


class JinjaLinter(BaseLinter):
    """
    Currently only lints one file, no package linting at the moment.
    """
    def __init__(self, args=[]):
        super(JinjaLinter, self).__init__(*args)
        self.add_argument(
            "--return_yaml",
            action="store_true"
        )

    def lint(self, args):
        lints = []
        # figure out jinja lint logic later
        # also add -f and -p logic
        if args.return_yaml:
            text = self.remove_jinja(args.file[0])
            return lints, text

    def remove_jinja(self, file: str) -> str:
        with open(file, "r") as f:
            text = f.read()
            no_curlies = text.replace('{{ ', '{{ "').replace(' }}', '" }}')

        try:
            content = yaml.load(
                                Environment(loader=BaseLoader())
                                .from_string(no_curlies).render()
                                )
            return content
        except Exception as e:
            print(e)
            return None
