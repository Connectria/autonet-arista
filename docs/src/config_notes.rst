Driver Configuration Notes
==========================
The Arista driver requires no additional configuration in most cases.
However, the following configuration is exposed for controlling TLS
behavior when connecting to EAPI.  The configuration can be set
directly in the Autonet application via config file or environment
variables.  Alternately, if using an inventory backend that supports
metadata, the configuration may also be set as metadata on a per device
basis.  Configuration from metadata will override global configuration.

============= ========= ===============================================
Option        Default   Description
============= ========= ===============================================
tls_verify    True      When True, the default, normal TLS verification
                        will be performed.  When False, any certificate
                        errors will be ignored. *NOTE*: Disabling TLS
                        verification is considered a security risk.
tls_ciphers   DEFAULT   The list of TLS ciphers to be offered during
                        the TLS handshake.  The cipher list must be
                        formatted as an OpenSSL cipher list.  See
                        `CIPHER LIST FORMAT <https://www.openssl.org/docs/man1.1.1/man1/ciphers.html>`_
                        for more information.
============= ========= ===============================================

