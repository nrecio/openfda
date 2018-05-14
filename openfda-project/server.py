
import http.server#para implementar la logica del servidor, sus utilidades
import http.client#para que nuestro servidor pueda realizar peticiones en https, porque tambein hace de cliente
import json#para tratamiento de la respuesta de openfda, que es un json
import socketserver#necesito para reservar la ip y el puerto donde mi servidor va a escuchar


Puerto=8000


class testHTTPRequestHandler(http.server.BaseHTTPRequestHandler):#clase que define el comportamiento del manejador ante una peticion http.

    #tiene cuatro metodos
    def get_formulario(self):#construye una pagina web html para devolver los formularios al usuario
        html = """
            <html>
                <head>
                    <title></title>
                </head>
                <body style="background-color:lightblue;">
                    <h1>Introduzca su busqueda a continuacion...</h1>
                    <form method="get" action="listDrugs">
                        <input type = "submit" value="Lista medicamentos">
                        </input>
                    </form>
                    <form method="get" action="searchDrug">
                        <input type = "submit" value="Buscar medicamentos">
                        <input type = "text" name="drug"></input>
                        </input>
                    </form>
                    <form method="get" action="listCompanies">
                        <input type = "submit" value="Lista empresas">
                        </input>
                    </form>
                    <form method="get" action="searchCompany">
                        <input type = "submit" value="Busqueda empresas">
                        <input type = "text" name="company"></input>
                        </input>
                    </form>
                    <form method="get" action="listWarnings">
                        <input type = "submit" value="Lista advertencias">
                        </input>
                    </form>
                *Es importante que al realizar una busqueda introduzca el texto en mayusculas(ej: BAYER o NAPROXEN), ya que asi lo requiere la base de datos de la que le facilitamos los resultados.<br>
                *Tenga en cuenta que si pide una de las listas, por defecto solo le devolveremos un resultado, si desea una mayor numero de resultados, introduzca en la url:?limit= y el numero de resultados que desee obtener. 
                </body>
            </html>
                """
        return html
    def dame_web (self, lista):#recibe una lista de medicamentos , empresas o warnings y te devuelve una lista  en html
        listaHtml = """
                                <html>
                                    <head>
                                        <title>Resultados</title>
                                    </head>
                                    <body style="background-color:lightblue;">
                                        <h1>Aqui tiene los resultados requeridos</h1>
                                        <ul>
                            """
        for item in lista:
            listaHtml += "<li>" + item + "</li>"

        listaHtml += """
                                        </ul>
                                    </body>
                                </html>
                            """
        return listaHtml

    def dame_resultados_genericos (self, limit=10, skip_number=0):#Metodo para obtener toda la información de la pagina.
        conexion = http.client.HTTPSConnection("api.fda.gov")
        conexion.request("GET", "/drug/label.json" + "?limit="+str(limit)+"&skip="+str(skip_number))
        print ("/drug/label.json" + "?limit="+str(limit)+"&skip="+str(skip_number))#añade el limit y el skip
        respuesta = conexion.getresponse()
        metadatos = respuesta.read().decode("utf8")
        datos = json.loads(metadatos)
        resultados = datos['results']
        return resultados

    def do_GET(self):#unico metodo que se ejecuta de entrada, los demas son auxiliares y este metodo llama a las demas metodos y con su respuesta te hace el html con las respuestas.
        recurso_list = self.path.split("?")#Te separa el recurso por la interrogación.
        if len(recurso_list) > 1:#Si despues de la petición hay algo adicional, por ejemplo limit. si no hay nada despues se queda como está.
            params = recurso_list[1]#son los parámetros de un recurso de después de la interrogación.
        else:
            params = ""

        limit = 1#por defecto te devuelve un resultado.

        # Obtener los parametros
        if params:#si hay parametros, como el limit
            print("Hay parametros")
            parse_limit = params.split("=")#para sacar el valor del limit
            if parse_limit[0] == "limit":#detectamos que hay un limit que nos limita la respuesta.
                limit = int(parse_limit[1])#lo pasamos a entero porque era un string.
                print("Limit: {}".format(limit))
        else:
            print("SIN PARAMETROS")




        #si solo pedimos /...
        if self.path=='/':#es el unico recurso que no tienen parametro, los otros no tienen por que ser exactamente igual a la peticion.
            # Envía que ok
            self.send_response(200)

            # Enviar cabeceras
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html=self.get_formulario()#llama a un metodo anterior y lo que hace es cosntruir la web de lo formularios como un string y me lo devuelve.Este string html lo tenemos que devolver a los usuarios.
            self.wfile.write(bytes(html, "utf8"))
        #si pedimos una lista de medicamentos...
        elif 'listDrugs' in self.path:
            self.send_response(200)

            # Aqui enviamos las cabeceras
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            intento = 0
            medicamentos = []
            while len(medicamentos) != limit:
                resultados = self.dame_resultados_genericos(limit - len(medicamentos), limit * intento)#esta es la función que se conecta a openfda y te duvuelve todos los resultados.
                for resultado in resultados:
                    if ('generic_name' in resultado['openfda']):
                        medicamentos.append (resultado['openfda']['generic_name'][0])
                intento = intento + 1
            resultado_html = self.dame_web (medicamentos)#te construye la lista de medicamentos con un html.

            self.wfile.write(bytes(resultado_html, "utf8"))
        #si pedimos lista de empresas
        elif 'listCompanies' in self.path:#deuelve una lista de empresas y tiene que responder al comando limit, si no hay limit, te devuelve una compañia.
            self.send_response(200)

            # Enviar cabeceras
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            intento=0
            companies = []#hago una lista vacia para las empresas
            while len (companies)!=limit:#si la longitud de la lista es distinta al limit...
                resultados = self.dame_resultados_genericos (limit-len(companies), limit*intento)#se conecta a openfda y devuelve lo resultados
                print ("Recibimos estos resultados: ", len (resultados))#arriba cuantos pedir y cuantos skip saltarte en el caso de que tengan menos del limit nombre de compañia.
                for resultado in resultados:
                    if ('manufacturer_name' in resultado['openfda']):
                        companies.append (resultado['openfda']['manufacturer_name'][0])#añadir el nombre de la empresa a mi lista companies.
                intento=intento+1
            resultado_html = self.dame_web(companies)

            self.wfile.write(bytes(resultado_html, "utf8"))
        #si pedimos advertencias de medicamentos...
        elif 'listWarnings' in self.path:

            self.send_response(200)

            # Envía las cabeceras
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            intento = 0
            warnings = []
            while len(warnings) != limit:
                resultados = self.dame_resultados_genericos (limit-len(warnings), limit*intento)
                for resultado in resultados:
                    if ('warnings' in resultado):
                        warnings.append (resultado['warnings'][0])
                intento = intento + 1
            resultado_html = self.dame_web(warnings)

            self.wfile.write(bytes(resultado_html, "utf8"))
        #para buscar medicamentos  determinados, el formulario lo llama.
        elif 'searchDrug' in self.path:
            self.send_response(200)

            # Envía cabeceras
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            #Por defecto 10 en este caso, no 1
            limit = 10
            drug=self.path.split('=')[1]

            intento = 0
            drugs = []
            while len(drugs) != limit:
                conexion = http.client.HTTPSConnection("api.fda.gov")
                conexion.request("GET", "/drug/label.json" + "?limit="+str(limit-len(drugs))+"&skip="+str(limit*intento) + '&search=active_ingredient:' + drug)
                respuesta = conexion.getresponse()
                datos1 = respuesta.read()
                datos = datos1.decode("utf8")
                biblioteca_datos = json.loads(datos)
                events_search_drug = biblioteca_datos['results']
                for resultado in events_search_drug:
                    if ('generic_name' in resultado['openfda']):
                        drugs.append(resultado['openfda']['generic_name'][0])
                intento = intento + 1
            resultado_html = self.dame_web(drugs)

            self.wfile.write(bytes(resultado_html, "utf8"))
        #si buscamos compañias especificas...
        elif 'searchCompany' in self.path:
            self.send_response(200)

            # Enviamos las cabeceras
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            # Por defecto 10 en este caso, no 1
            limit = 10
            company=self.path.split('=')[1]
            intento = 0
            companies = []
            while len(companies) != limit:
                conexion = http.client.HTTPSConnection("api.fda.gov")
                conexion.request("GET", "/drug/label.json" + "?limit=" + str(limit - len(companies)) + "&skip=" + str(limit * intento) + '&search=openfda.manufacturer_name:' + company)
                respuesta = conexion.getresponse()
                datos1 = respuesta.read()
                datos = datos1.decode("utf8")
                biblioteca_datos = json.loads(datos)
                events_search_company = biblioteca_datos['results']

                for event in events_search_company:
                    companies.append(event['openfda']['manufacturer_name'][0])
                intento = intento + 1
            resultado_html = self.dame_web(companies)

            self.wfile.write(bytes(resultado_html, "utf8"))

        elif 'redirect' in self.path:#te redirige a la pagina rpincipal, el formulario en nuestro caso.
            print("Rerdirigimos la dirección a la página principal")
            self.send_error(302)
            self.send_header('Location', 'http://localhost:'+str(Puerto))#Te devuelve otra cabecera.
            self.end_headers()
        elif 'secret' in self.path:#si los datos a los que queremos acceder estan restringidos, te devuelve un error 401.
            self.send_error(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Mi servidor"')
            self.end_headers()
        else:#En caso de no encontrar el recurso
            self.send_error(404)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write("I don't know '{}'.".format(self.path).encode())
        return


#PROGRAMA PRINCIPAL, DONDE EMPEZAMOS A EJECUTAR

socketserver.TCPServer.allow_reuse_address= True#PARA poder reutilizar el puerto 8000 aun habiendo parado el servidor.

Handler = testHTTPRequestHandler#instancia de una clase que atiende a las peticiones http que pueden venir de dos sitios: un navegador manual o el test que nos han dado.

httpd = socketserver.TCPServer(("", Puerto), Handler)#asocia una ip y un puerto a tu manejador de peticiones, cuando me llegue una peticion a ese ip y puerto, se manda automaticamente a este manejador que atienda y responda la peticion.
print("sirviendo en el puerto:", Puerto)
httpd.serve_forever()# el servidor se pone a atender peticiones para siempre