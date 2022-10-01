API reference - A121
====================

This page provides an auto-generated summary of Acconeer Exploration Tool's A121 API.

.. warning::

    The ``acconeer.exptool.a121`` package is currently an unstable API and may change at any time.

Configurations
--------------

Session
^^^^^^^

.. autoclass:: acconeer.exptool.a121.SessionConfig
    :members:

Sensor
^^^^^^

.. autoclass:: acconeer.exptool.a121.SensorConfig
    :members:

Subsweep
^^^^^^^^

.. autoclass:: acconeer.exptool.a121.SubsweepConfig
    :members:

Parameter enums
^^^^^^^^^^^^^^^

.. note::

    The configuration parameter enum values (e.g. 0, 1, 19500000, ...) are not to be used directly.
    They are subject to change at any time.

.. autoclass:: acconeer.exptool.a121.PRF
    :members:
    :undoc-members:

.. autoclass:: acconeer.exptool.a121.IdleState
    :members:
    :undoc-members:

.. autoclass:: acconeer.exptool.a121.Profile
    :members:
    :undoc-members:

Entities
--------

RSS representations
^^^^^^^^^^^^^^^^^^^

.. autoclass:: acconeer.exptool.a121.Result
    :members:
    :undoc-members:

.. autoclass:: acconeer.exptool.a121.Metadata
    :members:
    :undoc-members:

System info
^^^^^^^^^^^

.. autoclass:: acconeer.exptool.a121.ClientInfo
    :members:
    :undoc-members:

.. autoclass:: acconeer.exptool.a121.ServerInfo
    :members:
    :undoc-members:

.. autoclass:: acconeer.exptool.a121.SensorInfo
    :members:
    :undoc-members:

Client
------

.. autoclass:: acconeer.exptool.a121.Client
    :members:
    :undoc-members:
    :member-order: groupwise
    :inherited-members:

Recording
---------

Recorders
^^^^^^^^^

.. autoclass:: acconeer.exptool.a121.H5Recorder
    :members:
    :undoc-members:

Records
^^^^^^^

.. autoclass:: acconeer.exptool.a121.Record
    :members:
    :undoc-members:

.. autoclass:: acconeer.exptool.a121.PersistentRecord
    :members:
    :undoc-members:

.. autoclass:: acconeer.exptool.a121.StackedResults
    :members:
    :undoc-members:

Open/load/save functions
^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: acconeer.exptool.a121.load_record

.. autofunction:: acconeer.exptool.a121.open_record

.. autofunction:: acconeer.exptool.a121.save_record

.. autofunction:: acconeer.exptool.a121.save_record_to_h5
