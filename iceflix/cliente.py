#!/usr/bin/python3
# -*- coding: utf-8 -*-

import Ice
import time
import sys
import logging
import hashlib
import getpass
import hashlib
#import topics
#from iceflixrtsp import RTSPPlayer
import Ice
import IceStorm
Ice.loadSlice('iceflix/iceflix.ice')
import IceFlix

logging.basicConfig(level=logging.NOTSET)
INTENTOS = 3


class Client(Ice.Application):
    ''' Class that implements the Client '''
    def __init__(self):
        self.token = None
        self.mainPrx = None
        self.authenticatorPrx = None
        self.mediaCatalogPrx = None
        self.streamingCatalogPrx = None
        self.usertoken = None
        self.mediaid = None
    
    def salir(self):
        logging.info("### GRACIAS POR USAR ICEFLIX ###")
        return 0

    def menuPrincipal(self):
        logging.info("\n\n\n### BIENVENIDO A ICEFLIX ###")
        logging.info("1. Funciones de la aplicación")
        logging.info("2. Salir de la aplicación")
        opcion = self.pedirNumero(2)
        if int(opcion) == 1:
            self.iniciarSesion()
        elif int(opcion) == 2:
            self.salir

    def iniciarSesion(self):
        opc = self.yes_or_no("\n\n\n¿Quiere iniciar sesión?")
        if opc:
            self.opcionesDeSesion()
        else:
            self.menuSinSesion()

    def opcionesDeSesion(self):
        if self.yes_or_no("\n\n\n¿Desea inciar como administrador?"):
            tokenAdmin = input("Introduce el Token de admin: ")
            if self.mainPrx.isAdmin(tokenAdmin):
                self.menuAdminsitrador()
            else:
                logging.info("Token incorrecto, no se pudo iniciar como Administrador")
                logging.info("Reiniciando servicio...")
                self.menuPrincipal()
        else:
            for i in range(1):
                logging.info("\n\n\n--- Inicio de sesión ---")
                user = input("Nombre de usuario: ")
                passwordHash = self.hashearContrasena(input("Contraseña: "))

                self.usertoken = self.authenticatorPrx.refreshAuthorization(user,passwordHash)
                logging.debug(self.usertoken)
                self.token = self.authenticatorPrx.isAuthorized(self.usertoken)
                if self.token:
                	self.menuSesion()
                else:
                	logging.info("Usuario no autorizado. Vuele a identificarte")
                	self.menuPrincipal()
                
            

    def menuSinSesion(self):
        logging.info("\n\n\n--- OPCIONES SIN INICIAR SESIÓN ---")
        logging.info("1. Búsqueda por título")
        logging.info("2. Volver al menú principal")

        opcion = self.pedirNumero(2)

        if int(opcion) == 1:
            self.busquedaTitulo(False)
        else:
            self.menuPrincipal()

    def menuAdminsitrador(self):
        logging.info("\n\n\n--- OPCIONES DE ADMINSITRADOR ---")
        logging.info("1. Añadir usuario")
        logging.info("2. Eliminar usuario")
        logging.info("3. Renombrar medio")
        logging.info("4. Volver al menú principal")

        opcion = self.pedirNumero(4)

        if int(opcion) == 1:
            self.anadirUsuario()
        elif int(opcion) == 2:
            self.eliminarUsuario()
        elif int(opcion) == 3:
            self.renombrarMedio()
        else:
            self.menuPrincipal()

    def menuSesion(self):
        logging.info("\n\n\n--- OPCIONES DE USUARIO ---")
        logging.info("1. Búsqueda de medio por título")
        logging.info("2. Búsqueda de medio por tag/s")
        logging.info("3. Volver al menú principal")

        opcion = self.pedirNumero(5)

        if int(opcion) == 1:
            self.busquedaTitulo(True)
        elif int(opcion) == 2:
            self.busquedaTag()
        else:
            self.menuPrincipal()

    def hashearContrasena(self, password:str) -> str:
        '''Metodo para codificar una contraseña con SHA256'''
        passwordHash = hashlib.sha256(password.encode()).hexdigest()        
        return passwordHash 
        
    def listarMedios(self,ids) -> int:
        ''' Método para mostrar los medios '''
        listaMedia = []
        for mediaid in ids:
            listaMedia.append(self.mediaCatalogPrx.getTile(mediaid,self.usertoken))

        num = 0
        for media in listaMedia:
            num+=1
            logging.info(f"{num}.- {media.info.name}") 

        seleccion = int(input(f"Introduzca el número [1-{num}]"))

        return listaMedia[seleccion-1]

    def opcionesMedio(self, ids):
    	''' Método para elegir uno de los medios disponibles '''
    	logging.info("\n\n\nElige uno de los medios que tiene disponibles: ")
    	medio = self.listarMedios(ids)
    	logging.info(f"¿Qué operacion quiere hacer con el medio elegido: {medio.info.name}?")
    	logging.info("1. Editar medio")
    	logging.info("2. Reproducir medio")
    	logging.info("3. Volver al menu")
    	
    	eleccion = self.pedirNumero(2)
    	if int(eleccion) == 1:
    		self.editarMedio(medio)
    	elif int(eleccion) == 2:
    		self.reproducirMedio(medio)
    	else:
    		self.menuSesion()
    		
    		
    def editarMedio(self,medio):
    	''' Método para realizar un cambio en el medio '''
    	logging.info("\n\n\nEstas son las opciones posibles a elegir:")
    	logging.info("1. Añadir tag ")
    	logging.info("2. Eliminar tag ")
    	logging.info("3. Volver al menu")
    	
    	opcion = self.pedirNumero(2)
    	if int(opcion) == 1:
    		self.anadirTag(medio)
    	elif int(opcion) == 2:
    		self.eliminarTag(medio)
    	else:
    		self.menuSesion()
    		
    
    def reproducirMedio(self,medio):
    	logging.info("Reproducir Medio")
    
    		
    	
    def busquedaTitulo(self,sesion):
        ''' Metodo de busqueda por titulo '''
        logging.info("\n\n\n--- Búsqueda por título ---")
        titulo = input("Introduzca el título de la película:")
        opcExacta = self.yes_or_no("¿Quiere realizar una búsqueda por término exacto?")
        try:
            ids = self.mediaCatalogPrx.getTilesByName(titulo, opcExacta)
            logging.debug(ids)
        except IceFlix.TemporaryUnavailable:
            logging.error("Servicio Catalog no disponible. Inténtelo más tarde")
        if not ids:
        	logging.error("No hay ninguna pelicula con este nombre en la base de datos")
        else:
            if sesion:
                self.opcionesMedio(ids)
            else:
                self.menuPrincipal()

    def busquedaTag(self):
    	''' Metodo de busqueda por tag '''
    	tags = []
    	logging.info("\n\n\n--- Búsqueda por tag/s ---")
    	tag = input("Introduce los tags separados por comas sin espacio\n\n\nTags: ")
    	tag = tag.split(",")
    	opcExacta = self.yes_or_no("¿Desea optener todos los tags?")
    	try:
    		tags = self.mediaCatalogPrx.getTilesByTags(tag, opcExacta, self.usertoken)
    	except IceFlix.Unauthorized:
    		logging.error("El token no es valido")
    	except IceFlix.TemporaryUnavailable:
    		logging.error("Servicio Catalog no disponible. Inténtelo más tarde")
    	if not tags:
    		logging.error("No hay ninguna coincidencia en la base de datos con tu busqueda")
    	else:
    		self.opcionesMedio(tags)
    	self.menuSesion()

    def anadirTag(self,medio):
        ''' Metodo de añadir unas lista de Tags a un medio  '''
        logging.info("\n\n\n--- Añadir tag/s a un medio ---")
        tag = input("Introduzca el tag que desea añadir (separalo por coma si añade mas de uno)\n\n\nTags:").split(",")
        try:
        	self.mediaCatalogPrx.addTags(medio.mediaId, tag, self.usertoken)
        except IceFlix.Unauthorized:
            logging.error("El token de autenticación proporcionado no es válido")
        except IceFlix.WrongMediaId:
            logging.error("El id del medio proporcionado no es correcto")
        self.menuSesion()
       
     
    def eliminarTag(self,medio):
        ''' Metodo de busqueda por titulo '''
        logging.info("\n\n\n--- Eliminar tag/s a un medio ---")
        tag = input("Introduzca el tag que desea eliminar (separalo por coma si añade mas de uno)\n\n\nTags:").split(",")
        try:
        	self.mediaCatalogPrx.removeTags(medio.mediaId, tag, self.usertoken)
        except IceFlix.Unauthorized:
            logging.error("El token de autenticación proporcionado no es válido")
        except IceFlix.WrongMediaId:
            logging.error("El id del medio proporcionado no es correcto")
        self.menuSesion()
        
  
    def anadirUsuario(self):
        ''' Metodo añadir usuario '''
        logging.info("\n\n\n--- Añadir usuario ---")
        user = input("Nombre de usuario: ")
        password = input("Contraseña: ")
        passwordHash = self.hashearContrasena(password)
        try:
        	self.authenticatorPrx.addUser(str(user), str(passwordHash), str(ADMINTOKEN))
        except IceFlix.Unauthorized:
        	logging.error("El token de autenticación proporcionado no es válido")
        except IceFlix.WrongMediaId:
        	logging.error("El id del medio proporcionado no es correcto")
        self.menuAdminsitrador()
 
    def renombrarMedio(): #TODAVÍA NO SE PUEDE IMPLEMENTAR
        """ Metodo de busqueda por titulo """
        logging.info("\n\n\n--- Búsqueda por título ---")
        titulo = input("Introduzca el título de la película:")
        opcExacta = self.yes_or_no("¿Quiere realizar una búsqueda por término exacto?")
        ids = catalog_prx.removeUser(self, user, adminToken)
        self.menuAdminsitrador()
        
    def eliminarUsuario(self):
        """ Metodo eliminar usuario """
        logging.info("\n\n\n--- Eliminar usuario ---")
        userNominado = input("Introduzca el nombre del usuario que desea elminar:")
        try:
        	self.authenticatorPrx.removeUser(str(userNominado), str(ADMINTOKEN))
        except IceFlix.Unauthorized:
            logging.error("El token de autenticación proporcionado no es válido")
        except IceFlix.WrongMediaId:
        	logging.error("El id del medio proporcionado no es correcto")
        self.menuAdminsitrador()
	
    def yes_or_no(self, question):
        answer = None
        logging.info(question) 
        while str(answer).lower() not in ("s", "n"):  
            answer = input("Introduce 'S' o 'N': ")  
            if answer == "s":  
                return True 
            elif answer == "n":  
                return False  
            else:  
                logging.info("Por favor, introduce 'S' o 'N': ")

    def pedirNumero(self, pivote):
        num = input("Introduzca un número: ")
        while (int(num) < 1) or (int(num) > pivote):
            logging.info(f"Por favor, Introduzca un número correcto [1-{pivote}")
            num = input("Introduzca un número: ")
        return num

    def run(self, args):
        ''' Method that runs the Client '''
        
        broker = self.communicator()
        proxy = broker.stringToProxy(args[1])

        logging.debug(args[1])
        self.mainPrx = IceFlix.MainPrx.uncheckedCast(proxy)
        if not self.mainPrx:
            logging.debug("No hay proxy")

        try:
            self.authenticatorPrx = self.mainPrx.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            logging.error("Servicio Authenticator no disponible. Inténtelo más tarde...")

        try:
            self.mediaCatalogPrx = self.mainPrx.getCatalog()
        except IceFlix.TemporaryUnavailable:
            logging.error("Servicio Catalog no disponible. Inténtelo más tarde...")

        self.menuPrincipal()

        return 0

class Revocations(IceFlix.Revocations):
        def __init__(self,client):
            self.client = client
        
        def revokeToken(self, userToken, servicio_id, current=None):
            return
            
if __name__ == '__main__':
    APP = Client()
    sys.exit(APP.main(sys.argv))
