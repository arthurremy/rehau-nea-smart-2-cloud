"""Handlers for reading user/installation data from the REHAU cloud API."""
import logging

from curl_cffi.requests import AsyncSession

from ..exceptions import MqttClientCommunicationError, MqttClientAuthenticationError
from .auth import API_CURL_OPTIONS, API_IMPERSONATE, api_headers


_LOGGER = logging.getLogger(__name__)


async def read_user_state(payload: dict):
    """Read the current installation/user state from the REHAU cloud API.

    Uses curl_cffi with browser TLS impersonation and the mobile-app headers,
    otherwise REHAU's WAF returns 418/403 (see ``handlers.auth``).

    Args:
        payload: The payload to send to the API.

    Returns:
        dict: The response from the API call.

    Raises:
        MqttClientAuthenticationError: If the token is rejected (401).
        MqttClientCommunicationError: On any other API/transport error.
    """
    url = f"https://api.nea2aws.aws.rehau.cloud/v2/users/{payload['username']}/getDataofInstall?demand={payload['demand']}&installsList={payload['installs_ids']}&hash={payload['install_hash']}"
    try:
        async with AsyncSession(curl_options=API_CURL_OPTIONS) as session:
            user_response = await session.get(
                url,
                headers=api_headers(payload['token']),
                impersonate=API_IMPERSONATE,
                timeout=60,
            )
    except Exception as exception:  # noqa: BLE001 - curl_cffi transport errors
        raise MqttClientCommunicationError(
            "Could not read user data from the API. Reason: " + str(exception)
        ) from exception

    if user_response.status_code >= 400:
        if user_response.status_code == 401:
            raise MqttClientAuthenticationError("Could not read user data from the API. Status code: " + str(user_response.status_code) + " Reason: " + user_response.text)
        raise MqttClientCommunicationError("Could not read user data from the API. Status code: " + str(user_response.status_code) + " Reason: " + user_response.text)

    user = user_response.json()
    return user["data"]["user"]
