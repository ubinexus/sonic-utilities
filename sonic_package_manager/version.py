#!/usr/bin/env python

""" Version and helpers routines. """

import semantic_version


class Version(semantic_version.Version):
    """ Extends Version class from semantic_version package. """

    @classmethod
    def parse(cls, version_string: str) -> 'Version':
        """ Construct Version from version_string.

        Args:
            version_string: SemVer compatible version string.
        Returns:
            Version object.
        Raises:
            ValueError: when version_string does not follow SemVer.
        """

        return semantic_version.Version(version_string)


def version_to_tag(ver: Version) -> str:
    """ Converts the version to Docker compliant tag string. """

    return str(ver).replace('+', '_')


def tag_to_version(tag: str) -> Version:
    """ Converts the version to Docker compliant tag string. """

    try:
        return Version.parse(tag.replace('_', '+'))
    except ValueError as err:
        raise ValueError(f'Failed to convert {tag} to version string: {err}')
