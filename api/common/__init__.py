"""Shared utilities and clients for Dyocense services."""

from . import dto, context, tracing
from .auth import AuthContext, BearerAuthMiddleware, noop_decoder, simple_decoder
from .kernel_client import KernelClient, KernelClientConfig, KernelClientError
from .mongo import get_client as get_mongo_client, get_collection as get_mongo_collection

__all__ = [
    "dto",
    "context",
    "tracing",
    "AuthContext",
    "BearerAuthMiddleware",
    "noop_decoder",
    "KernelClient",
    "KernelClientConfig",
    "KernelClientError",
    "get_mongo_client",
    "get_mongo_collection",
    "simple_decoder",
]
