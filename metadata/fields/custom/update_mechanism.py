#!/usr/bin/env python3
# Copyright 2025 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import re
from typing import Optional, Tuple

import metadata.fields.field_types as field_types
import metadata.fields.util as util
import metadata.validation_result as vr

# The regex for validating the structure of the Update Mechanism field.
UPDATE_MECHANISM_REGEX = re.compile(
    r"""
    ^           # Start of the string.

                # Group 1: Primary Mechanism (e.g., "Autoroll", "Manual", "Static").
                # It matches one or more characters that are not a dot, whitespace,
    ([^.\s(]+)  # or an opening parenthesis.

                # Group 2 (optional) Secondary Mechanism: preceded by a dot (e.g., ".HardFork").
    (?:         # Start of a non-capturing group for the optional part.
      \.        # .
      ([^\s(]+) # Capture the secondary mechanism.
    )?          # Indicates 'secondary' is optional.

                # Group 3 (optional): A bug link in parentheses (e.g., "(crbug.com/12345)").
    (?:         # Use a non-capturing group to catch the parentheses and whitespace.
      \s*       # Optional whitespace.
      \(        # (
      ([^)]+)   # Capture the content inside the parentheses.
      \)        # )
    )?          # Indicates 'bug_link' is optional.

    $           # End of the string.
    """, re.VERBOSE)

BUG_PREFIXES = ['crbug.com/']

# A set of the fully-qualified, allowed mechanism values.
ALLOWED_MECHANISMS = {
    "Autoroll",
    "Manual",
    "Static",
    "Static.HardFork",
}


def parse_update_mechanism(
        value: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Parses the Update Mechanism field value using a regular expression.
    Values are expected to be in the form Primary.Secondary (bug link)

    Args:
        value: The string value of the Update Mechanism field.

    Returns:
        A tuple (primary, secondary, bug_link).
        If the structure is invalid, all elements of the tuple are None.
    """
    match = UPDATE_MECHANISM_REGEX.match(value.strip())
    if not match:
        return None, None, None
    return match.groups()


class UpdateMechanismField(field_types.SingleLineTextField):
    """
    Field for 'Update Mechanism: <Value>'.
    The format is Primary[.SubsetSpecifier] [(crbug.com/BUG_ID)].
    """

    def __init__(self):
        super().__init__(name="Update Mechanism")

    def validate(self, value: str) -> Optional[vr.ValidationResult]:
        """
        Checks if the value is a valid Update Mechanism entry, including the
        logic for when a bug link is required or disallowed.
        """
        if util.is_empty(value):
            return vr.ValidationError(
                reason=f"{self._name} field cannot be empty.",
                additional=[
                    f"Must be one of {util.quoted(sorted(ALLOWED_MECHANISMS))}.",
                    "Example: 'Autoroll' or 'Manual (crbug.com/12345)'"
                ])

        primary, secondary, bug_link = parse_update_mechanism(value)
        # First, check if the value matches the general format.
        if primary is None:
            return vr.ValidationError(
                reason=f"Invalid format for {self._name} field.",
                additional=[
                    "Expected format: Mechanism[.SubMechanism] [(bug)]",
                    f"Allowed mechanisms: {util.quoted(sorted(ALLOWED_MECHANISMS))}.",
                    "Example: 'Static.HardFork (crbug.com/12345)'",
                ])

        mechanism = primary
        if secondary:
            mechanism += f".{secondary}"
        # Second, check if the mechanism is a known, allowed value.
        if mechanism not in ALLOWED_MECHANISMS:
            return vr.ValidationError(
                reason=f"Invalid mechanism '{mechanism}'.",
                additional=[
                    f"Must be one of {util.quoted(sorted(ALLOWED_MECHANISMS))}.",
                ])

        # If it's not Autorolled, it SHOULD have a bug link.
        # Only warn for Static, for now.
        elif primary == "Static" and bug_link is None:
            return vr.ValidationWarning(
                reason="No bug link to autoroll exception provided.",
                additional=[
                    "Please add a link if an exception bug has been filed.",
                    f"Example: '{mechanism} (crbug.com/12345)'"
                ])

        # The bug link must be for the public tracker or 'b/' for internal.
        elif bug_link and not any(x in bug_link for x in BUG_PREFIXES):
            return vr.ValidationError(
                reason=
                f"Bug links must begin with {util.quoted(sorted(BUG_PREFIXES))}.",
                additional=[
                    f"Please add a bug link using {util.quoted(sorted(BUG_PREFIXES))} in parentheses.",
                    f"Example: '{mechanism} (crbug.com/12345)'"
                ])

        # The bug link must be for the public tracker or 'b/' for internal.
        elif primary == "Autoroll" and bug_link:
            return vr.ValidationError(
                reason="Autoroll does not permit an autoroll exception.",
                additional=[
                    f"Please remove the unnecessary bug link {bug_link}.",
                    "If this bug is still relevant then maybe Autoroll isn't the right choice",
                    "You could move it to the description.",
                ])

        return None

    def narrow_type(self,
                    value: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Parses the field value into its components if it is valid.

        Returns:
            A tuple of (primary, secondary, bug_link) if valid, otherwise None, None, None.
        """
        validation = self.validate(value)
        if validation and validation.is_fatal():
            # It cannot be narrowed if there is a fatal error.
            return None, None, None
        return parse_update_mechanism(value)
