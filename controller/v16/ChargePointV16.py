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
#from controller.scheduler import SchedulerManager


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
        #self.__scheduler: AsyncIOScheduler = SchedulerManager.getScheduler()
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
            #logger.debug("Connected to central system.")
            print("Connected to central system.")
            self.__is_available = True
            #await self._restore_state()
        else:
            #logger.debug("Cannot connect to the central system.")
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