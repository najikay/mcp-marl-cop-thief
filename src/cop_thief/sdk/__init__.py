"""SDK layer: the single business-logic entrypoint for all consumers."""

from cop_thief.sdk.exceptions import (
    AdversarialHijackDetectedError,
    IllegalGameMutationError,
    SdkInitializationError,
)
from cop_thief.sdk.facade import CopThiefSDK

__all__ = [
    "CopThiefSDK",
    "AdversarialHijackDetectedError",
    "SdkInitializationError",
    "IllegalGameMutationError",
]
