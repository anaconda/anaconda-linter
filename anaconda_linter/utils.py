"""
Utility Functions and Classes

This module collects small pieces of code used throughout
:py:mod:`anaconda_linter`.
"""

import fnmatch
import glob
import logging
import os
import queue
import subprocess as sp
import sys
from collections import Counter
from copy import deepcopy
from functools import partial
from multiprocessing import Pool
from pathlib import Path
from threading import Thread
from typing import Any, Dict, List, Sequence

# FIXME(upstream): For conda>=4.7.0 initialize_logging is (erroneously) called
#                  by conda.core.index.get_index which messes up our logging.
# => Prevent custom conda logging init before importing anything conda-related.
import conda.gateways.logging
import jinja2
import requests
import tqdm as _tqdm
from conda_build import api
from jinja2 import Environment
from jsonschema import validate

try:
    from ruamel.yaml import YAML
    from ruamel.yaml.constructor import DuplicateKeyError
except ModuleNotFoundError:
    from ruamel_yaml import YAML
    from ruamel_yaml.constructor import DuplicateKeyError


conda.gateways.logging.initialize_logging = lambda: None


logger = logging.getLogger(__name__)


yaml = YAML(typ="safe")  # pylint: disable=invalid-name


class TqdmHandler(logging.StreamHandler):
    """Tqdm aware logging StreamHandler

    Passes all log writes through tqdm to allow progress bars and log
    messages to coexist without clobbering terminal
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # initialise internal tqdm lock so that we can use tqdm.write
        _tqdm.tqdm(disable=True, total=0)

    def emit(self, record):
        _tqdm.tqdm.write(self.format(record))


def tqdm(*args, **kwargs):
    """Wrapper around TQDM handling disable

    Logging is disabled if:

    - ``TERM`` is set to ``dumb``
    - ``CIRCLECI`` is set to ``true``
    - the effective log level of the is lower than set via ``loglevel``

    Args:
      loglevel: logging loglevel (the number, so logging.INFO)
      logger: local logger (in case it has different effective log level)
    """
    term_ok = (
        sys.stderr.isatty()
        and os.environ.get("TERM", "") != "dumb"
        and os.environ.get("CIRCLECI", "") != "true"
    )
    loglevel_ok = kwargs.get("logger", logger).getEffectiveLevel() <= kwargs.get(
        "loglevel", logging.INFO
    )
    kwargs["disable"] = not (term_ok and loglevel_ok)
    return _tqdm.tqdm(*args, **kwargs)


def ensure_list(obj):
    """Wraps **obj** in a list if necessary

    >>> ensure_list("one")
    ["one"]
    >>> ensure_list(["one", "two"])
    ["one", "two"]
    """
    if isinstance(obj, Sequence) and not isinstance(obj, str):
        return obj
    return [obj]


class JinjaSilentUndefined(jinja2.Undefined):
    def _fail_with_undefined_error(self, *args, **kwargs):
        return ""

    __add__ = (
        __radd__
    ) = (
        __mul__
    ) = (
        __rmul__
    ) = (
        __div__
    ) = (
        __rdiv__
    ) = (
        __truediv__
    ) = (
        __rtruediv__
    ) = (
        __floordiv__
    ) = (
        __rfloordiv__
    ) = (
        __mod__
    ) = (
        __rmod__
    ) = (
        __pos__
    ) = (
        __neg__
    ) = (
        __call__
    ) = (
        __getitem__
    ) = (
        __lt__
    ) = (
        __le__
    ) = (
        __gt__
    ) = __ge__ = __int__ = __float__ = __complex__ = __pow__ = __rpow__ = _fail_with_undefined_error


jinja = Environment(
    # loader=PackageLoader('bioconda_utils', 'templates'),
    trim_blocks=True,
    lstrip_blocks=True,
)


jinja_silent_undef = Environment(undefined=JinjaSilentUndefined)


def load_all_meta(recipe, config=None, finalize=True):
    """
    For each environment, yield the rendered meta.yaml.

    Parameters
    ----------
    finalize : bool
        If True, do a full conda-build render. Determines exact package builds
        of build/host dependencies. It involves costly dependency resolution
        via conda and also download of those packages (to inspect possible
        run_exports). For fast-running tasks like linting, set to False.
    """
    if config is None:
        config = load_conda_build_config()
    # `bypass_env_check=True` prevents evaluating (=environment solving) the
    # package versions used for `pin_compatible` and the like.
    # To avoid adding a separate `bypass_env_check` alongside every `finalize`
    # parameter, just assume we do not want to bypass if `finalize is True`.
    metas = [
        meta
        for (meta, _, _) in api.render(
            recipe,
            config=config,
            finalize=False,
            bypass_env_check=True,
        )
    ]
    # Render again if we want the finalized version.
    # Rendering the non-finalized version beforehand lets us filter out
    # variants that get skipped. (E.g., with a global `numpy 1.16` pin for
    # py==27 the env check fails when evaluating `pin_compatible('numpy')` for
    # recipes that use a pinned `numpy` and also require `numpy>=1.17` but
    # actually skip py==27. Filtering out that variant beforehand avoids this.
    if finalize:
        metas = [
            meta
            for non_finalized_meta in metas
            for (meta, _, _) in api.render(
                recipe,
                config=config,
                variants=non_finalized_meta.config.variant,
                finalize=True,
                bypass_env_check=False,
            )
        ]
    return metas


def load_conda_build_config(platform=None, trim_skip=True):
    """
    Load conda build config while considering global pinnings from conda-forge.
    """
    config = api.Config(no_download_source=True, set_build_id=False)

    # # get environment root
    # env_root = PurePath(shutil.which("conda-lint")).parents[1]
    # # set path to pinnings from conda forge package
    # config.exclusive_config_files = [
    #     os.path.join(env_root, "conda_build_config.yaml"),
    # ]
    # for cfg in chain(config.exclusive_config_files, config.variant_config_files or []):
    #     assert os.path.exists(cfg), ('error: {0} does not exist'.format(cfg))
    if platform:
        config.platform = platform
    config.trim_skip = trim_skip
    return config


def run(
    cmds: List[str],
    env: Dict[str, str] = None,
    mask: List[str] = None,
    live: bool = True,
    mylogger: logging.Logger = logger,
    loglevel: int = logging.INFO,
    **kwargs: Dict[Any, Any],
) -> sp.CompletedProcess:
    """
    Run a command (with logging, masking, etc)

    - Explicitly decodes stdout to avoid UnicodeDecodeErrors that can occur when
      using the ``universal_newlines=True`` argument in the standard
      subprocess.run.
    - Masks secrets
    - Passed live output to `logging`

    Arguments:
      cmd: List of command and arguments
      env: Optional environment for command
      mask: List of terms to mask (secrets)
      live: Whether output should be sent to log
      kwargs: Additional arguments to `subprocess.Popen`

    Returns:
      CompletedProcess object

    Raises:
      subprocess.CalledProcessError if the process failed
      FileNotFoundError if the command could not be found
    """
    logq = queue.Queue()

    def pushqueue(out, pipe):
        """Reads from a pipe and pushes into a queue, pushing "None" to
        indicate closed pipe"""
        for line in iter(pipe.readline, b""):
            out.put((pipe, line))
        out.put(None)  # End-of-data-token

    def do_mask(arg: str) -> str:
        """Masks secrets in **arg**"""
        if mask is None:
            # caller has not considered masking, hide the entire command
            # for security reasons
            return "<hidden>"
        if mask is False:
            # masking has been deactivated
            return arg
        for mitem in mask:
            arg = arg.replace(mitem, "<hidden>")
        return arg

    mylogger.log(loglevel, "(COMMAND) %s", " ".join(do_mask(arg) for arg in cmds))

    # bufsize=4 result of manual experimentation. Changing it can
    # drop performance drastically.
    with sp.Popen(
        cmds, stdout=sp.PIPE, stderr=sp.PIPE, close_fds=True, env=env, bufsize=4, **kwargs
    ) as proc:
        # Start threads reading stdout/stderr and pushing it into queue q
        out_thread = Thread(target=pushqueue, args=(logq, proc.stdout))
        err_thread = Thread(target=pushqueue, args=(logq, proc.stderr))
        out_thread.daemon = True  # Do not wait for these threads to terminate
        err_thread.daemon = True
        out_thread.start()
        err_thread.start()

        output_lines = []
        try:
            for _ in range(2):  # Run until we've got both `None` tokens
                for pipe, line in iter(logq.get, None):
                    line = do_mask(line.decode(errors="replace").rstrip())
                    output_lines.append(line)
                    if live:
                        if pipe == proc.stdout:
                            prefix = "OUT"
                        else:
                            prefix = "ERR"
                        mylogger.log(loglevel, "(%s) %s", prefix, line)
        except Exception:
            proc.kill()
            proc.wait()
            raise

        output = "\n".join(output_lines)
        if isinstance(cmds, str):
            masked_cmds = do_mask(cmds)
        else:
            masked_cmds = [do_mask(c) for c in cmds]

        if proc.poll() is None:
            mylogger.log(loglevel, "Command closed STDOUT/STDERR but is still running")
            waitfor = 30
            waittimes = 5
            for attempt in range(waittimes):
                mylogger.log(
                    loglevel,
                    "Waiting %s seconds (%i/%i)",
                    waitfor,
                    attempt + 1,
                    waittimes,
                )
                try:
                    proc.wait(timeout=waitfor)
                    break
                except sp.TimeoutExpired:
                    pass
            else:
                mylogger.log(loglevel, "Terminating process")
                proc.kill()
                proc.wait()
        returncode = proc.poll()

        if returncode:
            logger.error("COMMAND FAILED (exited with %s): %s", returncode, " ".join(masked_cmds))
            if not live:
                logger.error("STDOUT+STDERR:\n%s", output)
            raise sp.CalledProcessError(returncode, masked_cmds, output=output)

        return sp.CompletedProcess(returncode, masked_cmds, output)


def get_deps(recipe=None, build=True):
    """
    Generator of dependencies for a single recipe

    Only names (not versions) of dependencies are yielded.

    If the variant/version matrix yields multiple instances of the metadata,
    the union of these dependencies is returned.

    Parameters
    ----------
    recipe : str or MetaData
        If string, it is a path to the recipe; otherwise assume it is a parsed
        conda_build.metadata.MetaData instance.

    build : bool
        If True yield build dependencies, if False yield run dependencies.
    """
    # TODO: Fix this. Setting Meta to None to fix linting
    meta = None
    if recipe is not None:
        assert isinstance(recipe, str)
        metadata = load_all_meta(recipe, finalize=False)
    elif meta is not None:
        metadata = [meta]
    else:
        raise ValueError("Either meta or recipe has to be specified.")

    all_deps = set()
    for meta in metadata:
        if build:
            deps = meta.get_value("requirements/build", [])
        else:
            deps = meta.get_value("requirements/run", [])
        all_deps.update(dep.split()[0] for dep in deps)
    return all_deps


_max_threads = 1


def set_max_threads(n):
    global _max_threads
    _max_threads = n


def threads_to_use():
    """Returns the number of cores we are allowed to run on"""
    if hasattr(os, "sched_getaffinity"):
        cores = len(os.sched_getaffinity(0))
    else:
        cores = os.cpu_count()
    return min(_max_threads, cores)


def parallel_iter(func, items, desc, *args, **kwargs):
    pfunc = partial(func, *args, **kwargs)
    with Pool(threads_to_use()) as pool:
        yield from tqdm(pool.imap_unordered(pfunc, items), desc=desc, total=len(items))


def get_recipes(aggregate_folder, package="*", exclude=None):
    """
    Generator of recipes.

    Finds (possibly nested) directories containing a ``meta.yaml`` file.

    Parameters
    ----------
    aggregate_folder : str
        Top-level dir of the recipes

    package : str or iterable
        Pattern or patterns to restrict the results.
    """
    if isinstance(package, str):
        package = [package]
    if isinstance(exclude, str):
        exclude = [exclude]
    if exclude is None:
        exclude = []
    for p in package:
        logger.debug("get_recipes(%s, package='%s'): %s", aggregate_folder, package, p)
        path = os.path.join(aggregate_folder, p)
        for new_dir in glob.glob(path):
            meta_yaml_found_or_excluded = False
            for dir_path, dir_names, file_names in os.walk(new_dir):
                if any(fnmatch.fnmatch(dir_path[len(aggregate_folder) :], pat) for pat in exclude):
                    meta_yaml_found_or_excluded = True
                    continue
                if "meta.yaml" in file_names:
                    meta_yaml_found_or_excluded = True
                    yield dir_path
            if not meta_yaml_found_or_excluded and os.path.isdir(new_dir):
                logger.warn(
                    "No meta.yaml found in %s."
                    " If you want to ignore this directory, add it to the blocklist.",
                    new_dir,
                )
                yield new_dir


def validate_config(config):
    """
    Validate config against schema

    Parameters
    ----------
    config : str or dict
        If str, assume it's a path to YAML file and load it. If dict, use it
        directly.
    """
    if not isinstance(config, dict):
        config = yaml.load(open(config))
    fn = os.path.abspath(os.path.dirname(__file__)) + "/config.schema.yaml"
    schema = yaml.load(open(fn))
    validate(config, schema)


def load_config(path):
    """
    Parses config file, building paths to relevant blocklists

    Parameters
    ----------
    path : str
        Path to YAML config file
    """
    validate_config(path)

    if isinstance(path, dict):

        def relpath(p):
            return p

        config = path
    else:

        def relpath(p):
            return os.path.join(os.path.dirname(path), p)

        config = yaml.load(open(path))

    def get_list(key):
        # always return empty list, also if NoneType is defined in yaml
        value = config.get(key)
        if value is None:
            return []
        return value

    default_config = {"blocklists": [], "channels": ["defaults"], "requirements": None}
    if "blocklists" in config:
        config["blocklists"] = [relpath(p) for p in get_list("blocklists")]
    if "channels" in config:
        config["channels"] = get_list("channels")

    default_config.update(config)

    # store architecture information
    with open(Path(__file__).parent / "data" / "cbc_default.yaml") as text:
        init_arch = yaml.load(text.read())
        data_path = Path(__file__).parent / "data"
        for arch_config_path in data_path.glob("cbc_*.yaml"):
            arch = arch_config_path.stem.split("cbc_")[1]
            if arch != "default":
                with open(arch_config_path) as text:
                    default_config[arch] = deepcopy(init_arch)
                    default_config[arch].update(yaml.load(text.read()))

    return default_config


check_url_cache = {}


def check_url(url):
    """
    Validate a URL to see if a response is available

    Parameters
    ----------
    url: str
        URL to validate

    Return
    ------
    response_data: dict
        Limited set of response data
    """

    if url not in check_url_cache:
        response_data = {"url": url}
        try:
            response = requests.head(url, allow_redirects=False)
            if response.status_code >= 200 and response.status_code < 400:
                origin_domain = requests.utils.urlparse(url).netloc
                redirect_domain = origin_domain
                if "Location" in response.headers:
                    redirect_domain = requests.utils.urlparse(response.headers["Location"]).netloc
                if origin_domain != redirect_domain:  # For redirects to other domain
                    response_data["code"] = -1
                    response_data[
                        "message"
                    ] = f"URL domain redirect {origin_domain} ->  {redirect_domain}"
                    response_data["url"] = response.headers["Location"]
                    response_data["domain_origin"] = origin_domain
                    response_data["domain_redirect"] = redirect_domain
                else:
                    response_data["code"] = response.status_code
                    response_data["message"] = "URL valid"
            else:
                response_data["code"] = response.status_code
                response_data["message"] = f"Not reachable: {response.status_code}"
        except requests.HTTPError as e:
            response_data["code"] = e.response.status_code
            response_data["message"] = e.response.text
        except Exception as e:
            response_data["code"] = -1
            response_data["message"] = str(e)
        check_url_cache[url] = response_data
    return check_url_cache[url]


def generate_correction(pkg_license, compfile=Path(__file__).parent / "data" / "licenses.txt"):
    with open(compfile) as f:
        words = f.readlines()

    words = [w.strip("\n") for w in words]
    WORDS = Counter(words)

    def P(word, N=sum(WORDS.values())):
        "Probability of `word`."
        return WORDS[word] / N

    def correction(word):
        "Most probable spelling correction for word."
        return max(candidates(word), key=P)

    def candidates(word):
        "Generate possible spelling corrections for word."
        return known([word]) or known(edits1(word)) or known(edits2(word)) or [word]

    def known(words):
        "The subset of `words` that appear in the dictionary of WORDS."
        return {w for w in words if w in WORDS}

    def edits1(word):
        "All edits that are one edit away from `word`."
        letters = "abcdefghijklmnopqrstuvwxyz"
        symbols = "-.0123456789"
        letters += letters.upper() + symbols
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [L + R[1:] for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
        replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
        inserts = [L + c + R for L, R in splits for c in letters]
        return set(deletes + transposes + replaces + inserts)

    def edits2(word):
        "All edits that are two edits away from `word`."
        return (e2 for e1 in edits1(word) for e2 in edits1(e1))

    return correction(pkg_license)


def find_closest_match(string: str) -> str:
    closest_match = generate_correction(string)
    if closest_match == string:
        return None
    return closest_match


# copied and adapted from conda-build
def find_config_files(metadata_or_path, variant_config_files, exclusive_config_files):
    """
    Find config files to load. Config files are stacked in the following order:
        1. exclusive config files (see config.exclusive_config_files)
        2. user config files
           (see context.conda_build["config_file"] or ~/conda_build_config.yaml)
        3. cwd config files (see ./conda_build_config.yaml)
        4. recipe config files (see ${RECIPE_DIR}/conda_build_config.yaml)
        5. additional config files (see config.variant_config_files)

    .. note::
        Order determines clobbering with later files clobbering earlier ones.

    :param metadata_or_path: the metadata or path within which to find recipe config files
    :type metadata_or_path:
    :param exclusive_config_files
    :param variant_config_files
    :return: List of config files
    :rtype: `list` of paths (`str`)
    """

    def resolve(p):
        return os.path.abspath(os.path.expanduser(os.path.expandvars(p)))

    # exclusive configs
    files = [resolve(f) for f in ensure_list(exclusive_config_files)]

    if not files:
        # if not files and not config.ignore_system_variants:
        # user config
        # if cc_conda_build.get('config_file'):
        #     cfg = resolve(cc_conda_build['config_file'])
        # else:
        #     cfg = resolve(os.path.join('~', "conda_build_config.yaml"))
        cfg = resolve(os.path.join("~", "conda_build_config.yaml"))
        if os.path.isfile(cfg):
            files.append(cfg)

        cfg = resolve("conda_build_config.yaml")
        if os.path.isfile(cfg):
            files.append(cfg)

    path = getattr(metadata_or_path, "path", metadata_or_path)
    cfg = resolve(os.path.join(path, "conda_build_config.yaml"))
    if os.path.isfile(cfg):
        files.append(cfg)

    files.extend([resolve(f) for f in ensure_list(variant_config_files)])

    return files
