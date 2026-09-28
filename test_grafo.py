"""Regresiones deterministas del núcleo de grafos y navegación, sin red."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
import networkx as nx
import pandas as pd
import callejero
import gps
import grafo_pesado as gp


def peso(G, u, v):
    return G[u][v]['weight']


def calle_lineal():
    G = nx.DiGraph()
    for n in range(4):
        G.add_node(n, x=n, y=0)
    for u, v, longitud, nombre in [(0,1,100,'A'), (1,2,200,'A'), (2,3,300,'B')]:
        G.add_edge(u,v,length=longitud,maxspeed=10,name=nombre,highway='residential')
    return G


class AlgoritmosTest(unittest.TestCase):
    def test_dijkstra_contra_networkx(self):
        for dirigido in (False, True):
            for seed in range(15):
                G=nx.gnp_random_graph(12,.2,seed=seed,directed=dirigido)
                for u,v in G.edges:
                    G[u][v]['weight']=(u*13+v*7+seed)%11
                for destino,distancia in nx.single_source_dijkstra_path_length(G,0).items():
                    with self.subTest(dirigido=dirigido,seed=seed,destino=destino):
                        ruta=gp.camino_minimo(G,peso,0,destino)
                        self.assertEqual((ruta[0],ruta[-1]),(0,destino))
                        self.assertEqual(sum(peso(G,u,v) for u,v in zip(ruta,ruta[1:])),distancia)

    def test_bosques_contra_networkx(self):
        for seed in range(20):
            G=nx.gnp_random_graph(15,.15,seed=seed)
            for u,v in G.edges:
                G[u][v]['weight']=(u*13+v*7+seed)%17-3
            esperado=nx.minimum_spanning_tree(G).size(weight='weight')
            prim=[(v,p) for v,p in gp.prim(G,peso).items() if p is not None]
            for aristas in (prim,gp.kruskal(G,peso)):
                with self.subTest(seed=seed,aristas=aristas):
                    T=nx.Graph(); T.add_nodes_from(G); T.add_edges_from(aristas)
                    self.assertTrue(nx.is_forest(T))
                    self.assertEqual(nx.number_connected_components(T),nx.number_connected_components(G))
                    self.assertEqual(sum(peso(G,u,v) for u,v in aristas),esperado)

    def test_inaccesible_y_nodos_ausentes(self):
        G=nx.DiGraph(); G.add_nodes_from([0,1])
        with self.assertRaises(nx.NetworkXNoPath):
            gp.camino_minimo(G,peso,0,1)
        for origen,destino in [(9,0),(0,9)]:
            with self.assertRaises(nx.NodeNotFound):
                gp.camino_minimo(G,peso,origen,destino)
        self.assertEqual(gp.camino_minimo(G,peso,0,0),[0])

    def test_empates_etiquetas_mixtas(self):
        G=nx.Graph(); G.add_weighted_edges_from([(0,'a',1),(0,2,1),('a',2,0)])
        self.assertEqual(gp.camino_minimo(G,peso,0,'a'),[0,'a'])
        self.assertEqual(len(gp.prim(G,peso)),3)

    def test_pesos_invalidos(self):
        for valor in (-1,float('inf'),float('nan')):
            G=nx.Graph(); G.add_edge(0,1,weight=valor)
            with self.assertRaises(ValueError):
                gp.dijkstra(G,peso,0)

    def test_tipos_y_grafo_vacio(self):
        self.assertEqual(gp.prim(nx.Graph(),peso),{})
        self.assertEqual(gp.kruskal(nx.Graph(),peso),[])
        for funcion in (gp.prim,gp.kruskal):
            with self.assertRaises(nx.NetworkXNotImplemented):
                funcion(nx.DiGraph(),peso)


class NavegacionTest(unittest.TestCase):
    def test_primer_tramo(self):
        resumen=gps.generar_instrucciones_navegacion(calle_lineal(),[0,1])[-1]
        self.assertEqual(resumen['distancia_total'],100)
        self.assertEqual(resumen['tiempo_circulacion_s'],10)
        self.assertAlmostEqual(resumen['tiempo_total'],1/6)

    def test_acumular_calle_y_esperas(self):
        instrucciones=gps.generar_instrucciones_navegacion(calle_lineal(),[0,1,2,3],24)
        giro=next(i for i in instrucciones if i['tipo']=='navegacion')
        self.assertEqual(giro['distancia'],300)
        self.assertEqual(instrucciones[-1]['distancia_total'],600)
        self.assertEqual(instrucciones[-1]['tiempo_espera_s'],48)
        self.assertAlmostEqual(instrucciones[-1]['tiempo_total'],108/60)

    def test_misma_posicion_y_nombre_ausente(self):
        G=calle_lineal(); G[0][1]['name']=None
        textos=gps.formatear_instrucciones(gps.generar_instrucciones_navegacion(G,[0,1]))
        self.assertNotIn('None',' '.join(textos))
        self.assertEqual(gps.generar_instrucciones_navegacion(G,[0],24)[-1]['tiempo_total'],0)
        self.assertEqual(gps.generar_instrucciones_navegacion(G,[]),[])

    def test_sentidos_y_velocidad(self):
        G=calle_lineal()
        with self.assertRaises(nx.NetworkXNoPath):
            gps.generar_instrucciones_navegacion(G,[1,0])
        with self.assertRaises(KeyError):
            gp.ruta_corta(G,1,0)
        G[0][1]['maxspeed']=0
        with self.assertRaises(ValueError):
            gps.generar_instrucciones_navegacion(G,[0,1])

    def test_giro_misma_calle(self):
        G=calle_lineal(); G.nodes[2].update(x=1,y=1)
        instrucciones=gps.generar_instrucciones_navegacion(G,[0,1,2])
        self.assertEqual(instrucciones[1]['giro'],'a la izquierda')

    def test_espera_cambia_ruta(self):
        G=nx.DiGraph()
        for u,v,longitud in [(0,1,10),(1,2,10),(0,2,30)]:
            G.add_edge(u,v,length=longitud,maxspeed=1)
        self.assertEqual(gp.camino_minimo(G,gp.ruta_rapida,0,2),[0,1,2])
        self.assertEqual(gp.camino_minimo(G,gp.ruta_optima,0,2),[0,2])


class CallejeroTest(unittest.TestCase):
    def test_direccion_ausente_y_espacios(self):
        df=pd.DataFrame([dict(DIRECCION_COMPLETA='CALLE DE PRUEBA',NUMERO=1,LATITUD=40.,LONGITUD=-3.)])
        self.assertEqual(callejero.busca_direccion('calle  de prueba, 1',df),(40,-3))
        for entrada in ('CALLE DE PRUEBA, 2','sin numero','calle, abc'):
            with self.assertRaises(callejero.AddressNotFoundError):
                callejero.busca_direccion(entrada,df)

    def test_paralelas_por_criterio(self):
        M=nx.MultiDiGraph(crs='epsg:4326')
        M.add_edge(0,1,length=100,highway=['unclassified'],name=[])
        M.add_edge(0,1,length=150,highway='motorway',name='Rapida')
        M.add_edge(0,0,length=1,highway='residential')
        with contextlib.redirect_stdout(io.StringIO()):
            corto=callejero.procesa_grafo(M)
            rapido=callejero.procesa_grafo(M,gp.ruta_rapida)
        self.assertEqual(corto[0][1]['length'],100)
        self.assertEqual(rapido[0][1]['length'],150)
        self.assertFalse(corto.has_edge(0,0))
        self.assertFalse(corto.has_edge(1,0))
        self.assertEqual(M[0][1][0]['highway'],['unclassified'])
        self.assertNotIn('maxspeed',M[0][1][0])

    def test_csv_y_errores(self):
        with tempfile.TemporaryDirectory() as directorio:
            archivo=Path(directorio)/'direcciones.csv'
            encabezado='VIA_CLASE;VIA_PAR;VIA_NOMBRE;NUMERO;LATITUD;LONGITUD\n'
            archivo.write_text(encabezado+"CALLE;;PRUEBA;1;40°30'0'' N;3°30'0'' W\n",encoding='latin-1')
            with contextlib.redirect_stdout(io.StringIO()):
                df=callejero.carga_callejero(archivo)
            self.assertEqual(callejero.busca_direccion('CALLE PRUEBA, 1',df),(40.5,-3.5))
            archivo.write_text(encabezado+"CALLE;;PRUEBA;1;40°24'60'' N;3°30'0'' W\n",encoding='latin-1')
            with contextlib.redirect_stdout(io.StringIO()):
                normalizado=callejero.carga_callejero(archivo)
            self.assertAlmostEqual(normalizado['LATITUD'].iloc[0],40+25/60)
            archivo.write_text(encabezado+"CALLE;;PRUEBA;1;incorrecta;3°30'0'' W\n",encoding='latin-1')
            with contextlib.redirect_stdout(io.StringIO()),self.assertRaises(ValueError):
                callejero.carga_callejero(archivo)
            with contextlib.redirect_stdout(io.StringIO()),self.assertRaises(FileNotFoundError):
                callejero.carga_callejero(Path(directorio)/'ausente.csv')


if __name__ == '__main__':
    unittest.main()
