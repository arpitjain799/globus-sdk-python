#!/usr/bin/env python

import itertools
import pathlib
import textwrap
from typing import Iterator, List, Tuple

HERE = pathlib.Path(__file__).parent

FIXED_PREAMBLE = f"""\
# isort:skip_file
# fmt:off
#
# this __init__.py file is generated by {pathlib.Path(__file__).name}
# do not edit it directly or testing will fail
import importlib
import logging
import sys
import typing

from .version import __version__


def _force_eager_imports() -> None:
    current_module = sys.modules[__name__]

    for attribute_set in _LAZY_IMPORT_TABLE.values():
        for attr in attribute_set:
            getattr(current_module, attr)
"""

FIXED_EPILOG = """
# configure logging for a library, per python best practices:
# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logging.getLogger("globus_sdk").addHandler(logging.NullHandler())
"""


_LAZY_IMPORT_TABLE: List[Tuple[str, Tuple[str, ...]]] = [
    (
        "authorizers",
        (
            "AccessTokenAuthorizer",
            "BasicAuthorizer",
            "ClientCredentialsAuthorizer",
            "NullAuthorizer",
            "RefreshTokenAuthorizer",
        ),
    ),
    ("client", ("BaseClient",)),
    (
        "exc",
        (
            "GlobusAPIError",
            "GlobusConnectionError",
            "GlobusConnectionTimeoutError",
            "GlobusError",
            "GlobusSDKUsageError",
            "GlobusTimeoutError",
            "NetworkError",
        ),
    ),
    (
        "local_endpoint",
        (
            "GlobusConnectPersonalOwnerInfo",
            "LocalGlobusConnectPersonal",
        ),
    ),
    ("response", ("GlobusHTTPResponse",)),
    (
        "services.auth",
        (
            "AuthAPIError",
            "AuthClient",
            "ConfidentialAppAuthClient",
            "IdentityMap",
            "NativeAppAuthClient",
            "OAuthDependentTokenResponse",
            "OAuthTokenResponse",
        ),
    ),
    (
        "services.gcs",
        (
            "CollectionDocument",
            "GCSAPIError",
            "GCSClient",
            "GCSRoleDocument",
            "GuestCollectionDocument",
            "MappedCollectionDocument",
            "CollectionPolicies",
            "POSIXCollectionPolicies",
            "POSIXStagingCollectionPolicies",
            "GoogleCloudStorageCollectionPolicies",
            "StorageGatewayDocument",
            "StorageGatewayPolicies",
            "POSIXStoragePolicies",
            "POSIXStagingStoragePolicies",
            "BlackPearlStoragePolicies",
            "BoxStoragePolicies",
            "CephStoragePolicies",
            "GoogleDriveStoragePolicies",
            "GoogleCloudStoragePolicies",
            "OneDriveStoragePolicies",
            "AzureBlobStoragePolicies",
            "S3StoragePolicies",
            "ActiveScaleStoragePolicies",
            "IrodsStoragePolicies",
            "HPSSStoragePolicies",
            "UserCredentialDocument",
        ),
    ),
    (
        "services.flows",
        (
            "FlowsClient",
            "FlowsAPIError",
            "IterableFlowsResponse",
            "SpecificFlowClient",
        ),
    ),
    (
        "services.groups",
        (
            "BatchMembershipActions",
            "GroupMemberVisibility",
            "GroupPolicies",
            "GroupRequiredSignupFields",
            "GroupRole",
            "GroupsAPIError",
            "GroupsClient",
            "GroupsManager",
            "GroupVisibility",
        ),
    ),
    (
        "services.search",
        (
            "SearchAPIError",
            "SearchClient",
            "SearchQuery",
            "SearchScrollQuery",
        ),
    ),
    ("services.timer", ("TimerAPIError", "TimerClient", "TimerJob")),
    (
        "services.transfer",
        (
            "ActivationRequirementsResponse",
            "DeleteData",
            "IterableTransferResponse",
            "TransferAPIError",
            "TransferClient",
            "TransferData",
        ),
    ),
]


def _generate_imports() -> Iterator[str]:
    for modname, items in _LAZY_IMPORT_TABLE:
        for item in items:
            yield textwrap.indent(f"from .{modname} import {item}", "    ")


def _generate_lazy_import_table() -> Iterator[str]:
    yield "_LAZY_IMPORT_TABLE = {"
    for modname, items in _LAZY_IMPORT_TABLE:
        yield textwrap.indent(f'"{modname}": {{', " " * 4)
        for item in items:
            yield textwrap.indent(f'"{item}",', " " * 8)
        yield textwrap.indent("},", " " * 4)
    yield "}"


def _generate_all_tuple() -> Iterator[str]:
    yield "__all__ = ("
    yield '    "__version__",'
    yield '    "_force_eager_imports",'
    yield from (
        f'    "{item}",'
        for item in sorted(itertools.chain(*[items for _, items in _LAZY_IMPORT_TABLE]))
    )
    yield ")"


def _init_pieces() -> Iterator[str]:
    yield FIXED_PREAMBLE
    yield ""
    yield from _generate_lazy_import_table()
    yield ""
    yield "if typing.TYPE_CHECKING or sys.version_info < (3, 7):"
    yield from _generate_imports()
    yield """
else:
    def __dir__() -> typing.List[str]:
        # dir(globus_sdk) should include everything exported in __all__
        # as well as some explicitly selected attributes from the default dir() output
        # on a module
        #
        # see also:
        # https://discuss.python.org/t/how-to-properly-extend-standard-dir-search-with-module-level-dir/4202
        return list(__all__) + [
            # __all__ itself can be inspected
            "__all__",
            # useful to figure out where a package is installed
            "__file__",
            "__path__",
        ]

    def __getattr__(name: str) -> typing.Any:
        for modname, items in _LAZY_IMPORT_TABLE.items():
            if name in items:
                mod = importlib.import_module("." + modname, __name__)
                value = getattr(mod, name)
                setattr(sys.modules[__name__], name, value)
                return value

        raise AttributeError(f"module {__name__} has no attribute {name}")
"""
    yield ""
    yield from _generate_all_tuple()
    yield ""
    yield FIXED_EPILOG


def _generate_init() -> str:
    return "\n".join(_init_pieces())


def main() -> None:
    with open(HERE / "__init__.py", "w", encoding="utf-8") as fp:
        fp.write(_generate_init())


if __name__ == "__main__":
    main()
