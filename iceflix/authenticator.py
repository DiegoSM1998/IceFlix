#python3
#utf-8
'''
    Modulo creado para implementar el servicio del catalogo
    Por: Manuel Avilés Rodríguez
         Jose Alberto Seco
         Andreea Tarabuta
         Diego Sepúlveda
'''

import logging
import uuid
import sys
import os.path
import secrets
import threading
import time
import json
import random

import Ice
import IceStorm
Ice.loadSlice('iceflix/iceflix.ice')

import IceFlix
from service_announcement import (
    ServiceAnnouncementsListener,
    ServiceAnnouncementsSender,
)


TAMANO_TOKEN = 40
USERS_FILE = 'iceflix/users.json'
TIEMPO_CADUCIDAD = 120

logging.basicConfig(level=logging.NOTSET)

def leer_bd(USERS_FILE):
    '''Metodo para leer usuarios del Json'''
    #pylint: disable=C0103
    #pylint: disable=W0621
    try:
        with open(USERS_FILE, "r") as file:
            json_users = json.load(file)
            return json_users
    except Exception:
        logging.error("Error en la lectura de fichero usuarios")
        raise ValueError
    #pylint: enable=C0103
    #pylint: enable=W0621

def escribir_bd(USERS_FILE, json_users):
    #pylint: disable=C0103
    #pylint: disable=W0621
    '''Metodo para escribir usuarios en el Json'''
    file = (open(USERS_FILE, "w"))
    json.dump(json_users, file, indent=6)
    logging.debug('La base de datos de Usuarios ha sido actualizada')
    file.close()
    #pylint: enable=C0103
    #pylint: enable=W0621

class UserUpdates(IceFlix.UserUpdates):
    '''Sirviente UserUpdates'''
    #pylint: disable=C0103
    #pylint: disable=W0613
    def __init__(self, service_announcements, authenticator):
        self.service_announcements = service_announcements
        self.authenticator = authenticator

    def newUser(self, user, password_hash, srv_id, current=None):
        """if srvId not in self.serviceAnnouncements.authenticators:
            return"""
        if srv_id == self.authenticator.service_id:
            logging.debug("Anuncio \"newUser\" recibido desde el propio sirviente. Ignorando...")
            return
        self.authenticator.dicc_users[user] = password_hash
        logging.debug(self.authenticator.dicc_users)


    def newToken(self, user, password_hash, srv_id, current=None):
        '''Metodo para generar un nuevo token'''
        if srv_id == self.authenticator.service_id:
            logging.debug("Anuncio \"newToken\" recibido desde el propio sirviente. Ignorando...")
            return
        self.authenticator.dicc_tokens[user] = password_hash
        logging.debug(self.authenticator.dicc_users)
    #pylint: enable=C0103
    #pylint: enable=W0613

class Revocations(IceFlix.Revocations):
    '''Sirviente Revocations'''
    #pylint: disable=C0103
    #pylint: disable=W0613
    def __init__(self, service_announcements, authenticator):
        self.service_announcements = service_announcements
        self.authenticator = authenticator

    # Emitted when token expires
    def revokeToken(self, user_token, srv_id, current=None):
        '''Metodo para eliminar un token'''
        if srv_id == self.authenticator.service_id:
            logging.debug(
                "Anuncio \"revokeToken\" recibido desde el propio sirviente. Ignorando...")
            return
        if user_token in self.authenticator.dicc_tokens:
            del self.authenticator.dicc_tokens[self.authenticator.whois(user_token)]
        logging.debug("La base de datos de tokens ha sido actualizada")

    # Emitted when user is removed
    def revokeUser(self, user, srv_id, current=None):
        '''Metodo para eliminar un usuario'''
        if srv_id == self.authenticator.service_id:
            logging.debug(
                "Anuncio \"revokeUser\" recibido desde el propio sirviente. Ignorando...")
            return
        del self.authenticator.dicc_users[user]
        logging.debug(self.authenticator.dicc_users)
    #pylint: enable=C0103
    #pylint: enable=W0613

class Authenticator(IceFlix.Authenticator):
    '''Clase sirviente authenticator'''
    #pylint: disable=C0103
    #pylint: disable=W0613
    def __init__(self):
        """Create the Main servant instance."""
        self.service_id = str(uuid.uuid4())
        self.dicc_users = leer_bd(USERS_FILE)
        self.dicc_tokens = {}
        self.user_updates = None
        self.revocations = None
        self.actualizado = False
        self.subscriber = None

    def refreshAuthorization(self, user: str, password_hash: str, current=None) -> str:
        '''Metodo para regenerar una autorizacion'''
        if user in self.dicc_users:
            if self.dicc_users[user] == password_hash:
                new_token = secrets.token_urlsafe(TAMANO_TOKEN)
                self.dicc_tokens[user] = new_token

                timer = threading.Timer(TIEMPO_CADUCIDAD, self.token_caduca, args=(new_token, user))
                timer.start()
                return new_token
            raise IceFlix.Unauthorized()

    def token_caduca(self, password_hash: str, user: str) -> None:
        '''Metodo para eliminar los token'''
        if user in self.dicc_users.keys():
            if self.dicc_users[user] == password_hash:
                new_token = secrets.token_urlsafe(TAMANO_TOKEN)
                self.dicc_tokens[user] = new_token
                self.user_updates.newToken(user, new_token, self.service_id)
                logging.debug(self.dicc_tokens)
                timer = threading.Timer(TIEMPO_CADUCIDAD, self.token_caduca, args=(new_token, user))
                timer.start()
                return new_token
            raise IceFlix.Unauthorized()
        raise IceFlix.Unauthorized()

    def isAuthorized(self, user_token: str, current=None) -> bool:
        '''Metodo para comprobar si el token es valido'''
        if user_token in self.dicc_tokens.values():
            return True
        return False

    def whois(self, user_token: str, current=None) -> str:
        '''Medoto para obtener datos de usuario a traves del token'''
        if user_token in self.dicc_tokens.values():
            dicc_del_reves = {userToken: user for user, userToken in self.dicc_tokens.items()}
            user = dicc_del_reves[user_token]
            return user
        else:
            raise IceFlix.Unauthorized()

    def addUser(self, user, password_hash, admin_token, current=None):
        '''Metodo para añadir usuarios'''
        isAdmin = None
        try:
            mainPrx = random.choice(self.subscriber.mains)
            isAdmin = mainPrx.isAdmin(admin_token)
        except Exception:
            raise IceFlix.TemporaryUnavailable()

        if not isAdmin:
            if user not in self.dicc_users:
                self.dicc_users[user] = password_hash
                escribir_bd(USERS_FILE, self.dicc_users)
                self.user_updates.newUser(user, password_hash, self.service_id)
        else:
            raise IceFlix.Unauthorized()

    def removeUser(self, user: str, admin_token: str, current=None) -> None:
        '''Medodo para eliminar usuarios'''
        isAdmin = None
        try:
            mainPrx = random.choice(self.subscriber.mains)
            isAdmin = mainPrx.isAdmin(admin_token)
        except Exception:
            raise IceFlix.TemporaryUnavailable()

        if not isAdmin:
            if user in self.dicc_users:
                del self.dicc_users[user]
                escribir_bd(USERS_FILE, self.dicc_users)
                if user in self.dicc_tokens:
                    del self.dicc_tokens[user]
                self.revocations.revokeUser(user, self.service_id)
        else:
            raise IceFlix.Unauthorized()


    def share_data_with(self, service, current_database):
        """Share the current database with an incoming service."""
        service.updateDB(current_database, self.service_id)

    def updateDB(self, values, service_id, current=None):  # pylint: disable=invalid-name,unused-argument
        """Receives the current main service database from a peer."""
        if not self.actualizado:
            self.actualizado = True
            if not service_id in self.subscriber.known_ids:
                raise IceFlix.UnknownService()
            logging.info(
                "Receiving remote data base from %s to %s", service_id, self.service_id
            )
            self.subscriber.dicc_users = values.userPasswords
            self.subscriber.dicc_tokens = values.usersToken
    #pylint: enable=C0103
    #pylint: enable=W0613

class AuthenticatorApp(Ice.Application):
    """Example Ice.Application for a Main service."""

    def __init__(self):
        super().__init__()
        self.servant = Authenticator()
        self.proxy = None
        self.adapter = None
        self.announcer = None
        self.subscriber = None
        self.user_updates = None
        self.revocations = None

    def setup_announcements(self):
        """Configure the announcements sender and listener."""
        #pylint: disable=E1101

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
            self.servant, self.servant.service_id, IceFlix.AuthenticatorPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)
        #pylint: enable=E1101

    def setup_user_updates(self):
        """Configure the announcements sender and listener."""
        #pylint: disable=E1101
        communicator = self.communicator()
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager"),
        )

        try:
            topic = topic_manager.create("UserUpdates")
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve("UserUpdates")

        serv_user_updates = UserUpdates(None, self.servant)
        user_updates_prx = self.adapter.addWithUUID(serv_user_updates)
        topic.subscribeAndGetPublisher({}, user_updates_prx)

        user_updates_publisher = topic.getPublisher()
        user_updates_publisher = IceFlix.UserUpdatesPrx.uncheckedCast(user_updates_publisher)
        self.servant.user_updates = user_updates_publisher
        #pylint: enable=E1101

    def setup_revocations(self):
        '''Configure the announcements sender and listener.'''
        #pylint: disable=E1101

        communicator = self.communicator()
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager"),
        )

        try:
            topic = topic_manager.create("Revocations")
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve("Revocations")

        serv_revocations = Revocations(None, self.servant)
        revocations_prx = self.adapter.addWithUUID(serv_revocations)
        topic.subscribeAndGetPublisher({}, revocations_prx)

        revocations_publisher = topic.getPublisher()
        revocations_publisher = IceFlix.RevocationsPrx.uncheckedCast(revocations_publisher)
        self.servant.revocations = revocations_publisher
        #pylint: enable=E1101

    def run(self, args):
        """Run the application, adding the needed objects to the adapter."""
        logging.info("Running Authenticator application")
        comm = self.communicator()
        self.adapter = comm.createObjectAdapter("AuthenticatorAdapter")
        self.adapter.activate()

        self.proxy = self.adapter.addWithUUID(self.servant)
        print(self.proxy, flush=True)

        self.setup_announcements()
        self.servant.subscriber = self.subscriber
        self.setup_user_updates()
        self.setup_revocations()
        self.announcer.start_service()

        self.shutdownOnInterrupt()
        comm.waitForShutdown()

        self.announcer.stop()
        return 0

if __name__ == "__main__":
    APP = AuthenticatorApp()
    sys.exit(APP.main(sys.argv))
