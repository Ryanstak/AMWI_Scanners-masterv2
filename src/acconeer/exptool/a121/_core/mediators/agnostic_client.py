from __future__ import annotations

import time
from typing import Any, Optional, Union

from acconeer.exptool.a121._core.entities import (
    ClientInfo,
    Metadata,
    Result,
    SensorConfig,
    ServerInfo,
    SessionConfig,
)
from acconeer.exptool.a121._core.utils import unextend

from .communication_protocol import CommunicationProtocol
from .link import BufferedLink
from .recorder import Recorder


class ClientError(Exception):
    pass


class AgnosticClient:
    _link: BufferedLink
    _protocol: CommunicationProtocol
    _server_info: Optional[ServerInfo]
    _session_config: Optional[SessionConfig]
    _metadata: Optional[list[dict[int, Metadata]]]
    _session_is_started: bool
    _recorder: Optional[Recorder]

    def __init__(self, link: BufferedLink, protocol: CommunicationProtocol) -> None:
        self._link = link
        self._protocol = protocol
        self._server_info = None
        self._session_config = None
        self._session_is_started = False
        self._metadata = None
        self._recorder = None

    def _assert_connected(self):
        if not self.connected:
            raise ClientError("Client is not connected.")

    def _assert_session_setup(self):
        self._assert_connected()
        if not self.session_is_setup:
            raise ClientError("Session is not set up.")

    def _assert_session_started(self):
        self._assert_session_setup()
        if not self.session_is_started:
            raise ClientError("Session is not started.")

    def connect(self) -> None:
        """Connects to the specified host.

        :raises: Exception if the host cannot be connected to.
        """
        self._link.connect()

        self._link.send(self._protocol.get_sensor_info_command())
        sens_response = self._link.recv_until(self._protocol.end_sequence)
        sensor_infos = self._protocol.get_sensor_info_response(sens_response)

        self._link.send(self._protocol.get_system_info_command())
        sys_response = self._link.recv_until(self._protocol.end_sequence)
        self._server_info = self._protocol.get_system_info_response(sys_response, sensor_infos)

    def setup_session(
        self,
        config: Union[SensorConfig, SessionConfig],
    ) -> Union[Metadata, list[dict[int, Metadata]]]:
        """Sets up the session specified by ``config``.

        If the Client is not already connected, it will connect before setting up the session.

        :param config: The session to set up.
        :raises:
            ``ValueError`` if the config is invalid.

        :returns:
            ``Metadata`` if ``config.extended is False``,
            ``list[dict[int, Metadata]]`` otherwise.
        """
        if not self.connected:
            self.connect()

        if isinstance(config, SensorConfig):
            config = SessionConfig(config)

        config.validate()

        self._link.send(self._protocol.setup_command(config))
        reponse_bytes = self._link.recv_until(self._protocol.end_sequence)
        self._session_config = config
        self._metadata = self._protocol.setup_response(
            reponse_bytes, context_session_config=config
        )

        if self.session_config.extended:
            return self._metadata
        else:
            return unextend(self._metadata)

    def start_session(self, recorder: Optional[Recorder] = None) -> None:
        """Starts the already set up session.

        After this call, the server starts streaming data to the client.

        :param recorder:
            An optional ``Recorder``, which samples every ``get_next()``
        :raises: ``ClientError`` if ``Client``'s  session is not set up.
        """
        self._assert_session_setup()

        if recorder is not None:
            self._recorder = recorder
            self._recorder._start(
                client_info=self.client_info,
                extended_metadata=self.extended_metadata,
                server_info=self.server_info,
                session_config=self.session_config,
            )

        self._link.send(self._protocol.start_streaming_command())
        reponse_bytes = self._link.recv_until(self._protocol.end_sequence)
        self._protocol.start_streaming_response(reponse_bytes)
        self._session_is_started = True

    def get_next(self) -> Union[Result, list[dict[int, Result]]]:
        """Gets results from the server.

        :returns:
            A ``Result`` if the setup ``SessionConfig.extended is False``,
            ``list[dict[int, Result]]`` otherwise.
        :raises:
            ``ClientError`` if ``Client``'s session is not started.
        """
        self._assert_session_started()

        payload_size, partial_results = self._protocol.get_next_header(
            bytes_=self._link.recv_until(self._protocol.end_sequence),
            extended_metadata=self.extended_metadata,
            ticks_per_second=self.server_info.ticks_per_second,
        )
        payload = self._link.recv(payload_size)
        extended_results = self._protocol.get_next_payload(payload, partial_results)

        if self._recorder is not None:
            self._recorder._sample(extended_results)

        if self.session_config.extended:
            return extended_results
        else:
            return unextend(extended_results)

    def stop_session(self) -> Any:
        """Stops an on-going session

        :returns:
            The return value of the passed ``Recorder.stop()`` passed in ``start_session``.
        :raises:
            ``ClientError`` if ``Client``'s session is not started.
        """
        self._assert_session_started()

        recorder_result = None
        if self._recorder is not None:
            recorder_result = self._recorder._stop()

        self._link.send(self._protocol.stop_streaming_command())
        reponse_bytes = self._drain_buffer()
        self._protocol.stop_streaming_response(reponse_bytes)
        self._session_is_started = False
        return recorder_result

    def _drain_buffer(
        self, timeout_s: float = 1.0
    ) -> bytes:  # TODO: Make `timeout_s` session-dependant
        """Drains data in the buffer. Returning the first bytes that are not data packets."""
        start = time.time()

        while time.time() < start + timeout_s:
            next_header = self._link.recv_until(self._protocol.end_sequence)
            try:
                payload_size, _ = self._protocol.get_next_header(
                    bytes_=next_header,
                    extended_metadata=self.extended_metadata,
                    ticks_per_second=self.server_info.ticks_per_second,
                )
                _ = self._link.recv(payload_size)
            except Exception:
                return next_header
        raise ClientError("Client timed out when waiting for 'stop'-response.")

    def disconnect(self) -> None:
        """Disconnects the client from the host.

        :raises: ``ClientError`` if ``Client`` is not connected.
        """
        self._assert_connected()

        if self.session_is_started:
            _ = self.stop_session()

        self._server_info = None
        self._link.disconnect()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, type_, value, traceback):
        self.disconnect()

    @property
    def connected(self) -> bool:
        """Whether this Client is connected."""
        return self._server_info is not None

    @property
    def session_is_setup(self) -> bool:
        """Whether this Client has a session set up."""
        return self._session_config is not None

    @property
    def session_is_started(self) -> bool:
        """Whether this Client's session is started."""
        return self._session_is_started

    @property
    def server_info(self) -> ServerInfo:
        """The ``ServerInfo``."""
        self._assert_connected()

        return self._server_info  # type: ignore[return-value]

    @property
    def client_info(self) -> ClientInfo:
        """The ``ClientInfo``."""
        return ClientInfo()

    @property
    def session_config(self) -> SessionConfig:
        """The :class:`SessionConfig` for the current session"""

        self._assert_session_setup()
        assert self._session_config is not None  # Should never happen if session is setup
        return self._session_config

    @property
    def extended_metadata(self) -> list[dict[int, Metadata]]:
        """The extended :class:`Metadata` for the current session"""

        self._assert_session_setup()
        assert self._metadata is not None  # Should never happen if session is setup
        return self._metadata
