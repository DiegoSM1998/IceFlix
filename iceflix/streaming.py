#!/usr/bin/python3

from ast import main
import Ice
import hashlib
import sys
import os
import logging
import uuid
import string
import random
import threading
from time import sleep
from iceflixrtsp import RTSPEmitter
Ice.loadSlice("iceflix.ice")
import IceFlix

logging.basicConfig(level=logging.NOTSET)
MEDIA_FOLDER = 'iceflix/media'

class StreamProvider(IceFlix.StreamProvider):
    '''Sirviente de ServiceAnnouncements'''

    def __init__(self, proxy, main_proxy, stream_announcement_prx, serv_announcement):
        self.proxy = proxy
        self.main_prx = main_proxy
        self.service_id = str(uuid.uuid4())
        self.stream_announcement_prx = stream_announcement_prx
        self.media = {}
        self.serv_announcement = serv_announcement
        
    #bool isAvailable(string mediaId);
    def isAvailable(self, media_id: str):
        '''Metodo que indica si un medio esta disponible'''
        available = False
        if media_id in self.media.keys():
            available = True
        return available

    #void reannounceMedia(string srvId) throws UnknownService;
    def reannounceMedia(self, srv_id: str):#Metodo incompleto
        '''Metodo para reanunciar todos los medios'''
        if not srv_id in self.serv_announcement.catalogs:
            raise IceFlix.UnknowknService()
        else:
            for path in os.listdir(MEDIA_FOLDER):
                medio = path.name
                print(f"Subiendo medio {medio}")
                with open(medio, 'rb') as file:
                    contenido = file.read()
                    id = hashlib.sha256(str(contenido).encode()).hexdigest()
                    nombre_archivo = medio.split(".")[0]
                    self.stream_announcement_prx.newMedia(id, nombre_archivo, self.service_id)
                    
     #void deleteMedia(string mediaId, string adminToken) throws Unauthorized, WrongMediaId;             
     def deleteMedia(self, media_id: str, adminToken: str):#Metodo pendiente de probar
     	''' Metodo que permite al administrador eliminar un medio del servicio indicando su id '''
     	auth = self.mainPrx.isAdmin(adminToken)
     	if not auth:
     		raise IceFlix.Unauthorized()
     	try:
     		ruta = "MEDIA_FOLDER"+self.media[media_id]+".mp4"
     		del self.MEDIA_FOLDER[media_id]
     		os.remove(ruta)
     		self.stream_announcement_prx.removeMedia(self.media_Id, self.srvId)
     		
     	except:
     		raise IceFlix.WrongMediaId(media_id)
     		
     #string uploadMedia(string fileName, MediaUploader* uploader, string adminToken) throws Unauthorized, UploadError;		
     def uploadMedia(self, fileName: str, uploader, adminToken: str):
     	''' Metodo que permite al administrador subir un nuevo medio al servicio '''
     	auth = self.mainPrx.isAdmin(adminToken)
     	if not auth:
     		raise IceFlix.Unauthorized()
     	try:
     		titulo = fileName.split("/")[-1]
     		tamano = os.path.getsize(fileName)
     		ruta = "MEDIA_FOLDER" + titulo
     		#No entiendo muy bien el funcionamiento
     	except:
     		raise IceFlix.UploadError()
     	return media_id
     	
        	
     	
     	
     	
     	 
           
           
           
           


            




