"""The compat module provides various compatibility functions"""
# pylint: disable=C0103

import abc
import os
import re
import socket
import sys
import time
from typing import Any, List, TypeVar, Mapping, Tuple, Iterable

K = TypeVar('K')
V = TypeVar('V')

RE_NUM = re.compile(r'(\d+).+')

ON_LINUX = sys.platform.startswith("linux")
ON_OSX = sys.platform == "darwin"
ON_WINDOWS = sys.platform == "win32"

# Portable Abstract Base Class
AbstractBase = abc.ABCMeta('AbstractBase', (object,), {})

SOCKET_ERROR = OSError

try:
    SOL_TCP = socket.SOL_TCP
except AttributeError:
    SOL_TCP = socket.IPPROTO_TCP

HAVE_SIGNAL = os.name == 'posix'

_LOCALHOST = '127.0.0.1'
_LOCALHOST_V6 = '::1'

# for assertions that the data is either encoded or non-encoded text
str_or_bytes = (str, bytes)


def time_now() -> float:
    """
    Returns monotonic time
    """
    return time.monotonic()


def dictkeys(dct: Mapping[K, V]) -> List[K]:
    """
    Returns a list of keys of dictionary
    """

    return list(dct.keys())


def dictvalues(dct: Mapping[K, V]) -> List[V]:
    """
    Returns a list of values of a dictionary
    """
    return list(dct.values())


def dict_iteritems(dct: Mapping[K, V]) -> Iterable[Tuple[K, V]]:
    """
    Returns an iterator of items (key/value pairs) of a dictionary
    """
    return dct.items()


def dict_itervalues(dct: Mapping[K, V]) -> Iterable[V]:
    """
    :param dict dct:
    :returns: an iterator of the values of a dictionary
    :rtype: iterator
    """
    return dct.values()


def byte(*args) -> bytes:
    """
    Returns a single byte `bytes` for the given int argument (we
    optimize it a bit here by passing the positional argument tuple
    directly to the bytes constructor.
    """
    return bytes(args)


class long(int):
    """
    A marker class that signifies that the integer value should be
    serialized as `l` instead of `I`
    """

    def __str__(self) -> str:
        return str(int(self))

    def __repr__(self) -> str:
        return str(self) + 'L'


def canonical_str(value: Any) -> str:
    """
    Return the canonical str value for the string.
    """

    return str(value)


def is_integer(value: Any) -> bool:
    """
    Is value an integer?
    """
    return isinstance(value, int)


def as_bytes(value: str) -> bytes:
    """
    Returns value as bytes
    """
    if not isinstance(value, bytes):
        return value.encode('UTF-8')
    return value


def to_digit(value: str) -> int:
    """
    Returns value as in integer
    """
    if value.isdigit():
        return int(value)
    match = RE_NUM.match(value)
    return int(match.groups()[0]) if match else 0


def get_linux_version(release_str: str) -> Tuple[int, ...]:
    """
    Gets linux version
    """
    ver_str = release_str.split('-')[0]
    return tuple(map(to_digit, ver_str.split('.', 3)[:3]))


LINUX_VERSION = None
if ON_LINUX:
    import platform
    LINUX_VERSION = get_linux_version(platform.release())



def nonblocking_socketpair(
    family: int = socket.AF_INET,
    socket_type: int = socket.SOCK_STREAM,
    proto: int = 0
) -> Tuple[socket.socket, socket.socket]:
    """
    Returns a pair of sockets in the manner of socketpair with the additional
    feature that they will be non-blocking. Prior to Python 3.5, socketpair
    did not exist on Windows at all.
    """
    if family == socket.AF_INET:
        host = _LOCALHOST
    elif family == socket.AF_INET6:
        host = _LOCALHOST_V6
    else:
        raise ValueError('Only AF_INET and AF_INET6 socket address families '
                         'are supported')
    if socket_type != socket.SOCK_STREAM:
        raise ValueError('Only SOCK_STREAM socket socket_type is supported')
    if proto != 0:
        raise ValueError('Only protocol zero is supported')

    lsock = socket.socket(family, socket_type, proto)
    try:
        lsock.bind((host, 0))
        lsock.listen(min(socket.SOMAXCONN, 128))
        # On IPv6, ignore flow_info and scope_id
        addr, port = lsock.getsockname()[:2]
        csock = socket.socket(family, socket_type, proto)
        try:
            csock.connect((addr, port))
            ssock, _ = lsock.accept()
        except Exception:
            csock.close()
            raise
    finally:
        lsock.close()

    # Make sockets non-blocking to prevent deadlocks
    # See https://github.com/pika/pika/issues/917
    csock.setblocking(False)
    ssock.setblocking(False)

    return ssock, csock
