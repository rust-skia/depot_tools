#!/usr/bin/env python3
# Copyright 2024 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# These licenses are used to verify that code imported to Android complies with
# their licensing requirements. Do not add entries to this list without approval.
# Any licenses added should be a valid SPDX Identifier. For the full list of
# identifiers; see https://spdx.org/licenses/.
# Licenses below are grouped by restrictiveness level and then alphabetically.
ALLOWED_SPDX_LICENSES = frozenset([
    # other_ignorable.
    # go/keep-sorted start case=no
    "LZMA-SDK-9.22",
    # go/keep-sorted end
    # unencumbered.
    # go/keep-sorted start case=no
    "blessing",
    "CC0-1.0",
    "Unlicense",
    # go/keep-sorted end
    # permissive.
    # go/keep-sorted start case=no
    "GPL-2.0-with-autoconf-exception",
    "GPL-2.0-with-classpath-exception",
    "GPL-3.0-with-autoconf-exception",
    "MIT-0",
    # go/keep-sorted end
    # notice.
    # go/keep-sorted start case=no
    "AML",
    "Apache-2.0",
    "Artistic-2.0",
    "Beerware",
    "BSD-2-Clause",
    "BSD-2-Clause-FreeBSD",
    "BSD-3-Clause",
    "BSD-3-Clause-Attribution",
    "BSD-4-Clause",
    "BSD-4-Clause-UC",
    "BSD-4.3TAHOE",
    "BSD-Source-Code",
    "BSL-1.0",
    "CC-BY-3.0",
    "CC-BY-4.0",
    "FTL",
    "HPND",
    "HPND-sell-variant",
    "ICU",
    "IJG",
    "ISC",
    "JSON",
    "Libpng",
    "libtiff",
    "MIT",
    "MIT-Modern-Variant",
    "MS-PL",
    "NAIST-2003",
    "NCSA",
    "OFL-1.1",
    "OpenSSL",
    "SGI-B-2.0",
    "SunPro",
    "Unicode-3.0",
    "Unicode-DFS-2015",
    "Unicode-DFS-2016",
    "X11",
    "Zlib",
    # go/keep-sorted end
])

# These are licenses that are not in the SPDX license list, but are identified
# by the license classifier.
EXTENDED_LICENSE_CLASSIFIERS = frozenset([
    # unencumbered.
    # go/keep-sorted start case=no
    "AhemFont",
    "Android-SDK",
    "LZMA",
    "public-domain-md5",
    "SPL-SQRT-FLOOR",
    # go/keep-sorted end
    # permissive.
    # go/keep-sorted start case=no
    "LicenseRef-AMSFonts-2.2",
    "test_fonts",
    # go/keep-sorted end
    # notice.
    # go/keep-sorted start case=no
    "Apache-with-LLVM-Exception",
    "Apache-with-Runtime-Exception",
    "Bitstream",
    "BSD-2-Clause-Flex",
    "BSD-3-Clause-OpenMPI",
    "BSD-4-Clause-Wasabi",
    "Caffe",
    "CERN",
    "cURL",
    "dso",
    "Entenssa",
    "FFT2D",
    "getopt",
    "GIF-Encoder",
    "GNU-All-permissive-Copying-License",
    "IBM-DHCP",
    "JsonCPP",
    "Khronos",
    "Libpng-2.0",
    "LicenseRef-base64",
    "LicenseRef-OpenGLUT",
    "LicenseRef-takuya-ooura",
    "pffft",
    "Punycode",
    "SSLeay",
    "WebM-Project-Patent",
    "X11-Lucent",
    "zxing",
    # go/keep-sorted end
])

# These licenses are only allowed in open source projects due to their
# reciprocal requirements.
OPEN_SOURCE_SPDX_LICENSES = frozenset([
    # reciprocal.
    # go/keep-sorted start case=no
    "APSL-2.0",
    "CDDL-1.0",
    "CDDL-1.1",
    "CPL-1.0",
    "EPL-1.0",
    "MPL-1.1",
    "MPL-2.0",
    # go/keep-sorted end
])

# TODO(b/388620886): Implement warning when changing to or from these licenses
# (but not every time the README.chromium file is modified).
WITH_PERMISSION_ONLY = frozenset([
    # restricted.
    # go/keep-sorted start case=no
    "CC-BY-SA-3.0",
    "GPL-2.0",
    "GPL-3.0",
    "LGPL-2.0",
    "LGPL-2.1",
    "LGPL-3.0",
    "NPL-1.1",
    # go/keep-sorted end
    # by_exception_only.
    # go/keep-sorted start case=no
    "Commercial",
    "LicenseRef-Play-Core-SDK-TOS",
    "LicenseRef-Unity-Companion-License-1.3",
    "Opus-Patent-BSD-3-Clause",
    "UnRAR",
    # go/keep-sorted end
])

ALLOWED_LICENSES = ALLOWED_SPDX_LICENSES | EXTENDED_LICENSE_CLASSIFIERS
ALLOWED_OPEN_SOURCE_LICENSES = ALLOWED_LICENSES | OPEN_SOURCE_SPDX_LICENSES
