from flask import url_for
from graphviz import Digraph

from api_li3ds.database import Database

class Dot():
    '''
    Graphviz wrapper to export li3ds database elements
    '''

    def dot(name, url, label, nodes, edges):
        dot = Digraph(name=name, comment=url)
        dot.graph_attr.update({
            'label': label,
            'overlap': 'scalexy'
        })

        subgraphs = {}

        for node in nodes:
            if node.sensor not in subgraphs:
                url = url_for('sensor', id=node.sensor, _external=True)
                name = "cluster_sensor_{}".format(node.sensor)
                label = "Sensor {type}: {sname} ({sensor})".format_map(node._asdict())
                subgraphs[node.sensor] = Digraph(name=name, comment=url)
                subgraphs[node.sensor].graph_attr.update({'label': label})
            color = 'red' if node.root else 'black'
            label = '{name}\\n({id})'.format_map(node._asdict())
            subgraphs[node.sensor].node(str(node.id), label=label, color=color)

        for sensor in subgraphs:
            dot.subgraph(subgraphs[sensor])

        for edge in edges:
            # highlight sensor connections in blue
            color = 'blue' if edge.sc else 'black'
            label = '{tname}\\n({id})'.format_map(edge._asdict())
            dot.edge(str(edge.source), str(edge.target), label=label, color=color)

        dot.engine = 'dot'
        return dot

    def transfo_trees(name, url, label, ids):

        edges = Database.query(
            """
            select t.id, t.source, t.target, t.transfo_type, tf.sc, t.name, tft.name as tname
            from (
                select distinct
                    unnest(tt.transfos) as tid, sensor_connections as sc
                from li3ds.transfo_tree tt where tt.id = ANY(%s)
            ) as tf
            join li3ds.transfo t on t.id = tf.tid
            join li3ds.transfo_type tft on tft.id = t.transfo_type
            """, (list(ids), )
        )

        urefs = set()
        for edge in edges:
            urefs.add(edge.source)
            urefs.add(edge.target)

        nodes = Database.query("""
            select distinct r.id, r.name, r.root, r.sensor, s.name as sname, s.type
            from li3ds.referential r
            join li3ds.sensor s on r.sensor = s.id
            where ARRAY[r.id] <@ %s
        """, (list(urefs), ))

        return Dot.dot(name, url, label, nodes, edges)

    def platform_config(id):

        configs = Database.query_asdict("""
            select p.name as pname, p.id as pid, c.transfo_trees, c.id, c.name
            from li3ds.platform_config c
            join li3ds.platform p on p.id = c.platform
            where c.id = %s
        """, (id, ))

        if not configs:
            return None
        config = configs[0]

        name = "cluster_config_{}".format(id)
        url = url_for('platform_config', id=id, _external=True)
        label = "Platform: {pname} ({pid})\\nConfiguration: {name} ({id})".format_map(config)
        print (config)
        return Dot.transfo_trees(name, url, label, config['transfo_trees'])

    def transfo_tree(id):
        transfo_trees = Database.query_asdict(
            "select * from li3ds.transfo_tree where id=%s", (id,)
        )
        if not transfo_trees:
            return None
        transfo_tree = transfo_trees[0]

        name = "cluster_transfotree_{}".format(id)
        url = url_for('transfotree', id=id, _external=True)
        label = "TransfoTree: {name} ({id})".format_map(transfo_tree)

        return Dot.transfo_trees(name, url, label, [id])
