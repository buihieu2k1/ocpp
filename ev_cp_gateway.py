import asyncio
import logging
import atexit
import time
import os
from unsync import unsync
from websockets import InvalidURI, ConnectionClosedError, ConnectionClosedOK
# from controller.v16.ChargePointV16 import ChargePointV16
from common import constant
import asyncio
import logging
import os

from ocpp.v16 import ChargePoint as cp
from ocpp.v16 import call
from ocpp.v16 import call_result
from ocpp.routing import on
from ocpp.v16.enums import Action, RegistrationStatus
import ocpp.v16.enums as enums
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime


# charge point v16
class ChargePointV16(cp):
    __instance = None

    @staticmethod
    def getInstance():
        if ChargePointV16.__instance is not None:
            return ChargePointV16.__instance
        else:
            raise Exception("Not initialized")

    ################### Constructor ###################
    def __init__(self, id, connection, charge_point_info: dict):
        if ChargePointV16.__instance is not None:
            return
        super().__init__(id, connection)
        self.charge_point_info: dict = charge_point_info
        # self.__scheduler: AsyncIOScheduler = SchedulerManager.getScheduler()
        ChargePointV16.__instance = self
        # self.__scheduler.add_job(self.heartbeat, 'interval',
        #                          seconds=int("HeartbeatInterval"))
        self.__is_available: bool = True

    @property
    def is_available(self) -> bool:
        return self.__is_available

    async def send_boot_notification(self):
        """
        Notify and connect to the central system at boot.
        :return:
        charge_point_vendor=self.charge_point_info["vendor"],
                                               charge_point_model=self.charge_point_info["model"]
        """

        request = call.BootNotificationPayload(
            charge_point_model="Optimus",
            charge_point_vendor="The Mobility House"
        )

        server_response = await self.call(request)
        print("7_nguyen")
        print(server_response)
        if server_response.status == enums.RegistrationStatus.accepted:
            # logger.debug("Connected to central system.")
            print("Connected to central system.")
            self.__is_available = True
            # await self._restore_state()
        else:
            # logger.debug("Cannot connect to the central system.")
            print("Cannot connect to the central system.")
            self.__is_available = False

    async def send_heartbeat(self, interval):
        request = call.HeartbeatPayload()
        while True:
            await self.call(request)
            await asyncio.sleep(interval)

    async def heartbeat(self):
        """
        Sends a heartbeat to the central system.
        :return:
        """
        print("Sent heartbeat")
        await self.call(call.HeartbeatPayload())

    @on(Action.BootNotification)
    def on_boot_notification(
            self, charge_point_vendor: str, charge_point_model: str, **kwargs
    ):
        # return Call(unique_id=1, action=Action.BootNotification, payload={}).to_json()

        return call_result.BootNotificationPayload(
            current_time=datetime.utcnow().isoformat(),
            interval=10,
            status=RegistrationStatus.accepted,
        )


charge_point_reference = None
logger = logging.getLogger('charge_logger')

try:
    import websockets
except ModuleNotFoundError:
    print("This example relies on the 'websockets' package.")
    print("Please install it by running: ")
    print()
    print(" $ pip install websockets")
    import sys

    sys.exit(1)


@unsync
async def main():
    # reserve to get input infos from device
    global charge_point_reference
    charge_point_info: dict = {"infor": "test"}
    charge_point_id: str = constant.CHARGE_POINT_ID
    charge_point_uri: str = constant.SERVER_ADDRES
    protocol_version = "1.6"

    # Try reconnecting every 10 seconds, If ther connectinon drop
    threads = []
    while True:
        try:
            # Connect to the server using websockets.
            async with websockets.connect("ws://103.176.179.98:8180/steve/websocket/CentralSystemService/502.001.01.SL",
                                          subprotocols=["ocpp1.6"]) as ws:
                # logger.info(f"Choosing protocol version {protocol_version}")
                if protocol_version == "1.6":
                    # Create a singleton
                    ChargePointV16(charge_point_id, ws, charge_point_info)
                    charge_point_reference = ChargePointV16.getInstance()
                elif protocol_version == "2.0.1":
                    # Create a singleton
                    # ChargePointV201(charge_point_id, ws, charge_point_info)
                    # charge_point_reference = ChargePointV201.getInstance()
                    pass
                else:
                    # If the version is not supported, exit
                    version_unsupported_str: str = f"Unsupported OCPP version: {protocol_version}"
                    print(version_unsupported_str)
                    exit(-1)

                # Start listening for requests and send boot notification to the server
                await asyncio.gather(charge_point_reference.start(), charge_point_reference.send_boot_notification())

        except ConnectionClosedOK as closed_ok:
            logger.error("Connection closed, no error", exc_info=closed_ok)
        except ConnectionClosedError as error:
            logger.error("Connection closed with error", exc_info=error)
        except InvalidURI as invalid_uri:
            logger.error("Invalid URI specified, exiting", exc_info=invalid_uri)
            exit(-1)
        except KeyboardInterrupt:
            exit(-1)
        except Exception as ex:
            logger.error("Unknown error", exc_info=ex)
        for thread in threads:
            try:
                thread.future.cancel()
                thread.thread.set_exception()
            except Exception:
                pass
        await asyncio.sleep(10)


if __name__ == "__main__":
    # asyncio.run() is used when running this example with Python >= 3.7v
    main().result()
