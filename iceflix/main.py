"""Module containing a template for a main service."""

import logging
import uuid
import sys
import random

import Ice
import IceStorm
Ice.loadSlice('iceflix/iceflix.ice')

import IceFlix
from service_announcement import (
    ServiceAnnouncementsListener,
    ServiceAnnouncementsSender,
)

ADMINTOKEN = 'ADMIN'
logging.basicConfig(level=logging.NOTSET)

class Main(IceFlix.Main):
    """Servant for the IceFlix.Main interface.
    Disclaimer: this is demo code, it lacks of most of the needed methods
    for this interface. Use it with caution
    """

    def __init__(self):
        """Create the Main servant instance."""
        self.service_id = str(uuid.uuid4())
        self.subscriber = None
        self.actualizado = False

    def getAuthenticator(self,current=None):    
        while True:
            if not self.subscriber.authenticators:
                raise IceFlix.TemporaryUnavailable()
            try:
                proxy = random.choice(self.subscriber.authenticators)
                proxy.ice_ping()
                return proxy
            except Ice.LocalException:
                logging.info(f"No está disponible el Authenticator: {proxy}. Eliminando...")
                self.subscriber.authenticators.remove(proxy)

    def getCatalog(self,current=None):
        while True:
            if not self.subscriber.catalogs:
                raise IceFlix.TemporaryUnavailable()
            try:
                proxy = random.choice(self.subscriber.catalogs)
                proxy.ice_ping()
                return proxy
            except Ice.LocalException:
                logging.info(f"No está disponible el MediaCatalog: {proxy}. Eliminando...")
                self.subscriber.catalogs.remove(proxy)

    def share_data_with(self, service, currentServices):
        """Share the current database with an incoming service."""
        #currentServices = IceFlix.VolatileServices(super().subscriber.authenticators,service.catalogs)
        service.updateDB(currentServices, self.service_id)

    def isAdmin(self,adminToken, current=None):
        if ADMINTOKEN == adminToken:
            return True
        else:
            return False

    def updateDB(self, values, service_id, current=None):  
        # pylint: disable=invalid-name,unused-argument
        """Receives the current main service database from a peer."""
        if not self.actualizado:
            self.actualizado = True 
            if not service_id in self.subscriber.known_ids:
                raise IceFlix.UnknownService()
            logging.info(   
                "Receiving remote data base from %s to %s", service_id, self.service_id
            )
            self.subscriber.authenticators = values.authenticators
            self.subscriber.catalogs = values.mediaCatalogs


class MainApp(Ice.Application):
    """Example Ice.Application for a Main service."""

    def __init__(self):
        super().__init__()
        self.servant = Main()
        self.proxy = None
        self.adapter = None
        self.announcer = None
        self.subscriber = None

    def setup_announcements(self):
        """Configure the announcements sender and listener."""

        communicator = self.communicator()
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager"),
        )

        try:
            topic = topic_manager.create("ServiceAnnouncements")
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve("ServiceAnnouncements")

        self.announcer = ServiceAnnouncementsSender(
            topic,
            self.servant.service_id,
            self.proxy,
        )

        self.subscriber = ServiceAnnouncementsListener(
            self.servant, self.servant.service_id, IceFlix.MainPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)



    def run(self, args):
        """Run the application, adding the needed objects to the adapter."""
        logging.info("Running Main application")
        comm = self.communicator()
        self.adapter = comm.createObjectAdapter("MainAdapter")
        self.adapter.activate()

        self.proxy = self.adapter.addWithUUID(self.servant)
        print(self.proxy , flush=True)

        self.setup_announcements()
        self.servant.subscriber = self.subscriber
        self.announcer.start_service()

        self.shutdownOnInterrupt()
        comm.waitForShutdown()

        self.announcer.stop()
        return 0

if __name__ == "__main__":
    APP = MainApp()
    sys.exit(APP.main(sys.argv))