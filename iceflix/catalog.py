#!/usr/bin/python3

'''
    Modulo creado para implementar el servicio del catalogo
    Por: Manuel Avilés Rodríguez
         Jose Alberto Seco
         Andreea Tarabuta
         Diego Sepúlveda
'''
from distutils.util import subst_vars
import logging
import json
import random
import sys
import uuid

import Ice
import IceStorm
Ice.loadSlice('iceflix/iceflix.ice')

import IceFlix
from service_announcement import (
    ServiceAnnouncementsListener,
    ServiceAnnouncementsSender,
)

logging.basicConfig(level=logging.NOTSET)

class StreamProvider(IceFlix.StreamProvider):
    logging.info("Servidor de StreamProvider creado")


class Catalog(IceFlix.MediaCatalog):
    '''Sirviente de Catalog'''
    def __init__(self):
        """main_prx, catalog_updates_pub, serv_announ"""
        self.service_id = str(uuid.uuid4())
        self.providers = None
        #self.main_prx = main_prx
        self.catalog_updates = None
        self.updated = False
        self.subscriber = None
        self.movies_db = []
        self.tags_db = {}
        self.actualizado = False
    #pylint: disable=C0103
    #pylint: disable=R0914

    def get_media_db(self):
        '''Metodo para leer la base de datos'''
        with open('iceflix/movies.json', "r") as file:
            movies = json.load(file)
            self.movies_db = movies
            file.close()

        with open('iceflix/tags.json', "r") as file:
            tags = json.load(file)
            self.tags_db = tags
            file.close()


    def getTile(self, media_id: str, user_token: str, current = None):
        #pylint: disable=W0703
        '''Metodo para obtener un media a través de su id'''
        main_prx = random.choice(self.subscriber.mains)
        tags = []
        try:
            auth = main_prx.getAuthenticator()
            if user_token:
                usuario = auth.whois(user_token)
        except IceFlix.TemporaryUnavailable:
            raise IceFlix.TemporaryUnavailable()
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized()
        try:
            pelicula = self.movies_db[media_id]
            if user_token:
                tags = self.tags_db[media_id][usuario]
        except IceFlix.WrongMediaId:
            raise IceFlix.WrongMediaId(media_id)
        except Exception:
            logging.error("Error al conectarse a la base de datos")

        """
        try:
            proveedor_prx = self.providers[media_id]
            proveedor_prx = IceFlix.StreamProviderPrx.checkedCast(proveedor_prx)
            proveedor_prx.ice_ping()
        except Ice.LocalException:
            self.providers[media_id] = ""
            raise IceFlix.TemporaryUnavailable()
        """
        media_info = IceFlix.MediaInfo(pelicula, tags)
        media = IceFlix.Media(media_id, self.providers, media_info)
        return media
        #pylint: enable=W0703

    def getTilesByName(self, name, exact, current=None):
        '''Método que obtiene los titulos de un medio por su nombre'''
        #pylint: disable=W0703
        #pylint: disable=W0613
        try:
            lista_pelis = []
            if exact:
                for mediaid, medianame in self.movies_db.items():
                    logging.debug(medianame)
                    if name == medianame:
                        lista_pelis.append(mediaid)
            elif not exact:
                for mediaid, medianame in self.movies_db.items():
                    logging.debug(medianame)
                    if name in medianame:
                        lista_pelis.append(mediaid)
            return lista_pelis
        except Exception:
            logging.error("Error al conectarse a la base de datos")
        #pylint: enable=W0703
        #pylint: enable=W0613

    def getTilesByTags(self, tags, include_all_tags, user_token, current=None):
        '''Método que obtiene los títulos de un medio por sus tags'''
        #pylint: disable=W0703
        #pylint: disable=W0613
        autorizado = None
        main_prx = random.choice(self.subscriber.mains)
        usuario = None
        try:
            auth_prx = main_prx.getAuthenticator()
            autorizado = auth_prx.isAuthorized(user_token)
            usuario = auth_prx.whois(user_token)
        except IceFlix.TemporaryUnavailable:
            logging.error(
                "El servicio de autenticación no está disponible actualmente. Inténtalo más tarde")
        if not autorizado:
            raise IceFlix.Unauthorized()

        try:
            lista_pelis = []
            pelisID = []
            if include_all_tags:
                for movieID, usertags in self.tags_db.items():
                    for usuario in usertags:
                        usuariotags = usertags[usuario]
                        if all(tag in usuariotags for tag in tags):
                            pelisID.append(movieID)
            else:
                for movieID, usertags in self.tags_db.items():
                    for usuario in usertags:
                        usuariotags = usertags[usuario]
                        if any(tag in usuariotags for tag in tags):
                            pelisID.append(movieID)

            for movieID, movieName in self.movies_db.items():
                for peliID in pelisID:
                    if peliID == movieID:
                        lista_pelis.append(movieID)
                        pass
            return lista_pelis
        except Exception:
            logging.error(
                "Error al conectarse a la base de datos")
        #pylint: enable=W0703
        #pylint: enable=W0613

    def addTags(self, media_id, tags, user_token, current=None):
        '''Método que permite añadir tags a un medio'''
        autorizado = False
        main_prx = random.choice(self.subscriber.mains)
        #pylint: disable=W0703
        #pylint: disable=W0613
        #pylint: disable=W1202
        usuario = None
        try:
            auth_prx = main_prx.getAuthenticator()
            autorizado = auth_prx.isAuthorized(user_token)
        except IceFlix.TemporaryUnavailable:
            logging.error(
                "El servicio de autenticación no está disponible actualmente. Inténtalo más tarde")
        if not autorizado:
            raise IceFlix.Unauthorized()

        try:
            usuario = auth_prx.whois(user_token)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized()

        for tag in tags:
            if usuario in self.tags_db[media_id]:
                if tag not in self.tags_db[media_id][usuario]:
                    logging.debug(self.tags_db[media_id][usuario])
                    self.tags_db[media_id][usuario].append(tag)
            else:
                self.tags_db[media_id][usuario] = tags
                logging.debug(self.tags_db)

        try:
            file = open('iceflix/tags.json', "w")
            logging.debug(self.tags_db)
            json.dump(self.tags_db, file)
            logging.info(f"Los tags {tags} se han añadido correctamente")
        except IceFlix.WrongMediaId:
            raise IceFlix.WrongMediaId(media_id)
            file.close()
        except Exception:
            logging.error("Error añadiendo tags")
        self.catalog_updates.addTags(media_id, tags, usuario, self.service_id)
        #pylint: enable=W0703
        #pylint: enable=W0613
        #pylint: enable=W1202

    def removeTags(self, media_id, tags, user_token, current=None):
        '''Método que permite eliminar tags de un medio'''
        #pylint: disable=W0703
        #pylint: disable=W0613
        #pylint: disable=W1202
        autorizado = None
        main_prx = random.choice(self.subscriber.mains)
        try:
            auth_prx = main_prx.getAuthenticator()
            autorizado = auth_prx.isAuthorized(user_token)
        except IceFlix.TemporaryUnavailable:
            logging.error(
                "El servicio de autenticación no está disponible actualmente. Inténtalo más tarde")
        if not autorizado:
            raise IceFlix.Unauthorized()
        try:
            usuario = auth_prx.whois(user_token)
        except IceFlix.Unauthorized:
            raise IceFlix.Unauthorized()
        try:
            for tag in tags:
                if usuario in self.tags_db[media_id]:
                    logging.debug(self.tags_db)
                    if tag in self.tags_db[media_id][usuario]:
                        self.tags_db[media_id][usuario].remove(tag)
                        logging.info(f"Los tags {tags} se han eliminado correctamente")
                else:
                    logging.info("No tiene ningún tag en este medio")
                    return
            file = open('iceflix/tags.json', 'w')
            json.dump(self.tags_db, file)
            file.close()
            self.catalog_updates.removeTags(media_id, tags, usuario, self.service_id)
        except IceFlix.WrongMediaId:
            raise IceFlix.WrongMediaId(media_id)
        except Exception:
            logging.error("Error eliminando tags")
        #pylint: enable=W0703
        #pylint: enable=W0613
        #pylint: enable=W1202

    def renameTile(self, media_id, name, admin_token, current=None):
        '''Metodo que renombra un titulo'''
        #pylint: disable=W0613
        #pylint: disable=W0703
        autorizado = False
        encontrado = False
        try:
            main_prx = random.choice(self.subscriber.mains)
            logging.debug(main_prx)
            autorizado = main_prx.isAdmin(admin_token)
            logging.debug(autorizado)
        except Ice.NotRegisteredException:
            logging.error("Servicio principal no dispuesto")

        if not autorizado:
            raise IceFlix.Unauthorized()

        try:
            self.movies_db[media_id] = name
            file = open('iceflix/movies.json', 'w')
            json.dump(self.movies_db, file)
            file.close()
            self.catalog_updates.renameTile(media_id, name, self.service_id)
        except IceFlix.WrongMediaId:
            raise IceFlix.WrongMediaId(media_id)
        except Exception:
            logging.error("Error cambiando el nombre")
        #pylint: enable=W0613
        #pylint: enable=W0703

    def share_data_with(self, service, mediaDBList):
        '''Share the current database with an incoming service'''
        service.updateDB(mediaDBList, self.service_id)

    def updateDB(self, mediaDBList, service_id, current=None):
        #pylint: disable=W0613
        '''Receives the current service database from a peer'''
        tags = {}
        movies_db = {}
        for mediaDB in mediaDBList:
            self.tags_db[mediaDB.mediaId] = mediaDB.tagsPerUser
            self.movies_db[mediaDB.mediaId] = mediaDB.name
        logging.info("Receiving remote database from %s to %s", service_id, self.service_id)
        #pylint: enable=W0613

    def print_peliculas():
        '''Metodo para printear peliculas (borrar luego)'''
        with open('iceflix/movies.json', 'r') as file:
            peliculas = json.load(file)
        for pelicula in peliculas['media']:
            print(pelicula)
        file.close()
        with open('iceflix/tags.json', 'r') as file:
            tags = json.load(file)
        for tag in tags['tagss']:
            print(tag)
    #pylint: enable=C0103
    #pylint: enable=R0914

class CatalogUpdates(IceFlix.CatalogUpdates):
    '''Sirviente de CatalogUpdates'''

    def __init__(self, serv_announ, catalogo):
        self.subscriber = serv_announ
        self.catalog = catalogo

    def renameTile(self, media_id, name, service_id, current=None):
        #pylint: disable=W0703
        #pylint: disable=C0103
        #pylint: disable=W0613
        '''Metodo para renombrar un titulo'''
        if service_id == self.catalog.service_id:
            logging.info("Anuncio \"revokeUser\" recibido desde el propio sirviente. Ignorando...")
        else:
            self.catalog.movies_db[media_id] = name
            logging.info("Anuncio \"revokeUser\" recibido. Actualizando...")
        #pylint: enable=W0703
        #pylint: enable=C0103
        #pylint: enable=W0613

    def addTags(self, media_id, tags, usuario, service_id, current=None):
        '''Metodo para añadir tags'''
        #pylint: disable=W0703
        #pylint: disable=C0103
        #pylint: disable=W0613
        if service_id == self.catalog.service_id:
            logging.info("Anuncio \"addTags\" recibido desde el propio sirviente. Ignorando...")
        else:
            for tag in tags:
                if usuario in self.catalog.tags_db[media_id]:
                    if tag not in self.catalog.tags_db[media_id][usuario]:
                        self.catalog.tags_db[media_id][usuario].append(tag)
                else:
                    self.catalog.tags_db[media_id][usuario] = tags
            logging.info("Anuncio \"addTags\" recibido. Actualizando...")
        #pylint: enable=W0703
        #pylint: enable=C0103
        #pylint: enable=W0613

    def removeTags(self, media_id, tags, usuario, service_id, current=None):
        '''Metodo para eliminar tags'''
        #pylint: disable=C0103
        #pylint: disable=W0703
        if service_id == self.catalog.service_id:
            logging.info("Anuncio \"removeTags\" recibido desde el propio sirviente. Ignorando...")
        else:
            for tag in tags:
                if usuario in self.catalog.tags_db[media_id]:
                    if tag in self.catalog.tags_db[media_id][usuario]:
                        self.catalog.tags_db[media_id][usuario].remove(tag)
                else:
                    logging.info("No tiene ningún tag en este medio")
                    return
            logging.info("Anuncio \"removeTags\" recibido. Actualizando...")
        #pylint: enable=W0703
        #pylint: enable=C0103

class StreamAnnouncements(IceFlix.StreamAnnouncements):
    '''Sirviente de Stream Announcements'''

    def __init__(self, serv_announcements, catalog):
        self.serv_announcements = serv_announcements
        self.catalog = catalog

    def newMedia(self, media_id: str, inital_name: str, srv_id: str):
        '''Metodo para anunciar nuevos medios'''
        if srv_id in self.serv_announcements.stream_provider:
            self.catalog.providers[media_id] = self.serv_announcements.stream_provider[srv_id]
            if media_id not in self.catalog.movies_db:
                self.catalog.movies_db[media_id] = inital_name
            else:
                logging.error("El medio ya se encuentra en la base de datos")

    def removedMedia(self, media_id: str, srv_id: str):
        '''Metodo para anunciar la eliminacion de medios'''
        if srv_id in self.serv_announcements.stream_provider:
            del self.catalog.providers[media_id]
            del self.catalog.movies_db[media_id]

class CatalogServer(Ice.Application):
    '''Ice.Application para un servidor de Catalogo'''
    #pylint: disable=E1101
    def __init__(self):
        super().__init__()
        self.servant = Catalog()
        self.proxy = None
        self.adapter = None
        self.announcer = None
        self.subscriber = None
        self.catalog_updates = None
        self.stream_announcements = None

    def setup_announcements(self):
        '''Configure the announcements sender and listener'''
        communicator = self.communicator()
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create("ServiceAnnouncements")
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve("ServiceAnnouncements")

        self.announcer = ServiceAnnouncementsSender(
            topic,
            self.servant.service_id,
            self.proxy)

        self.subscriber = ServiceAnnouncementsListener(
            self.servant, self.servant.service_id, IceFlix.MediaCatalogPrx
        )

        subscriber_prx = self.adapter.addWithUUID(self.subscriber)
        topic.subscribeAndGetPublisher({}, subscriber_prx)

    def setup_catalog_updates(self):
        '''Configure the catalog updates sender and listener'''
        communicator = self.communicator()
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create("CatalogUpdates")
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve("CatalogUpdates")

        serv_catalog_up = CatalogUpdates(self.subscriber, self.servant)
        catalog_up_prx = self.adapter.addWithUUID(serv_catalog_up)
        topic.subscribeAndGetPublisher({}, catalog_up_prx)

        catalog_updates_pub = topic.getPublisher()
        catalog_updates_pub = IceFlix.CatalogUpdatesPrx.uncheckedCast(catalog_updates_pub)
        self.servant.catalog_updates = catalog_updates_pub

    def setup_stream_announcements(self):
        '''Configure the stream announcements listener'''
        communicator = self.communicator()
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(
            communicator.propertyToProxy("IceStorm.TopicManager")
        )

        try:
            topic = topic_manager.create("StreamAnnouncements")
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve("StreamAnnouncements")
        
        serv_stream_announ = StreamAnnouncements(self.subscriber, self.servant)
        stream_announ_prx = self.adapter.addWithUUID(serv_stream_announ)
        topic.subscribeAndGetPublisher({}, stream_announ_prx)

    def run(self, args):
        '''Run the application, adding the needed objects to the adapter'''
        logging.info("Ejecutando Catalog Aplicacion")
        self.servant.get_media_db()
        comm = self.communicator()
        self.adapter = comm.createObjectAdapter("MediaCatalogAdapter")
        self.adapter.activate()

        self.proxy = self.adapter.addWithUUID(self.servant)
        print(self.proxy, flush=True)

        self.setup_announcements()
        provider = StreamProvider()
        providers = self.adapter.addWithUUID(provider)
        providers = IceFlix.StreamProviderPrx.checkedCast(providers)
        self.servant.providers = providers

        self.servant.subscriber = self.subscriber
        self.setup_catalog_updates()
        self.setup_stream_announcements()
        self.announcer.start_service()

        self.shutdownOnInterrupt()
        comm.waitForShutdown()

        self.announcer.stop()
        return 0
    #pylint: enable=E1101

if __name__ == "__main__":
    APP = CatalogServer()
    sys.exit(APP.main(sys.argv))
