Driver Behavior Notes
=====================
In an effort to emulate CLI configuration semantics, the Arista driver
will make an effort to expand shorthand names of interfaces when performing
interface operations.  Take note that even when an interface is defined
using shorthand notation, the driver will return the fully qualified name.