"""access_signature — digital-signature access approval for the GitHub repos
masaaki-avnturle/tuplenetwork and masaaki-avnturle/Bada.

People who clone / push / pull trigger an approval request emailed to the
owner; the owner approves and a digital-signature password (signed with the
owner's Ed25519 key) is issued to the approved person.
"""

from .gatekeeper import Gatekeeper
from .registry import Registry, PROTECTED_REPOS
from . import ca

__all__ = ["Gatekeeper", "Registry", "PROTECTED_REPOS", "ca"]
