# -*- coding: utf-8 -*-
from flask_restplus import fields

from api_li3ds.app import api, Resource
from api_li3ds.database import Database


nsds = api.namespace('datasources', description='datasources related operations')

datasource_model_post = nsds.model('Datasource Model Post', {
    'uri': fields.String,
    'referential': fields.Integer(required=True),
    'session': fields.Integer(required=True)
})


datasource_model = nsds.inherit('Datasource Model', datasource_model_post, {
    'id': fields.Integer,
})

processing_model_post = nsds.model('Processing Model Post', {
    'launched': fields.DateTime(dt_format='iso8601', default=None),
    'tool': fields.String(required=True),
    'description': fields.String,
    'source': fields.Integer(required=True),
})

processing_model = nsds.inherit('Processing Model', processing_model_post, {
    'id': fields.Integer,
    'target': fields.Integer(required=True)
})


@nsds.route('/', endpoint='datasources')
class Datasources(Resource):

    @nsds.marshal_with(datasource_model)
    def get(self):
        '''Get all datasources'''
        return Database.query_asjson("select * from li3ds.datasource")

    @api.secure
    @nsds.expect(datasource_model_post)
    @nsds.marshal_with(datasource_model)
    @nsds.response(201, 'Datasource created')
    def post(self):
        '''Create a datasource'''
        return Database.query_asdict(
            "insert into li3ds.datasource (referential, session, uri) "
            "values (%(referential)s, %(session)s, %(uri)s) "
            "returning *",
            api.payload
        ), 201


@nsds.route('/<int:id>/', endpoint='datasource')
@nsds.response(404, 'Datasource not found')
class OneDatasource(Resource):

    @nsds.marshal_with(datasource_model)
    def get(self, id):
        '''Get one datasource given its identifier'''
        res = Database.query_asjson(
            "select * from li3ds.datasource where id=%s", (id,)
        )
        if not res:
            nsds.abort(404, 'Datasource not found')
        return res

    @api.secure
    @nsds.response(410, 'Datasource deleted')
    def delete(self, id):
        '''Delete a datasource given its identifier'''
        res = Database.rowcount("delete from li3ds.datasource where id=%s", (id,))
        if not res:
            nsds.abort(404, 'Datasource not found')
        return '', 410


@nsds.route('/<int:id>/processing/', endpoint='datasource_processing')
@nsds.param('id', 'The datasource identifier')
@nsds.response(404, 'Datasource not found')
class Processing(Resource):

    @nsds.marshal_with(processing_model)
    def get(self, id):
        '''Get the processing tool used to generate this datasource'''
        res = Database.query_asjson(
            "select * from li3ds.datasource where id=%s", (id,)
        )
        if not res:
            nsds.abort(404, 'Datasource not found')

        return Database.query_asjson(
            " select p.* from li3ds.processing p"
            " join li3ds.datasource s on s.id = p.target where s.id=%s",
            (id,)
        )

    @api.secure
    @nsds.expect(processing_model_post)
    @nsds.marshal_with(processing_model)
    @nsds.response(201, 'Datasource created')
    def post(self, id):
        '''Add a new processing tool that has generated the given datasource'''
        return Database.query_asdict(
            "insert into li3ds.processing (launched, tool, description, source, target) "
            "values (%(launched)s, %(tool)s, %(description)s, %(source)s, {}) "
            "returning *".format(id),
            api.payload
        ), 201


@nsds.route('/processing/<int:id>/', endpoint='processing')
@nsds.param('id', 'The Processing identifier')
@nsds.response(404, 'Processing not found')
class OneProcessing(Resource):

    @nsds.marshal_with(processing_model)
    def get(self, id):
        '''Get processing tool given its id'''
        return Database.query_asjson(
            " select * from li3ds.processing where id = %s", (id,)
        )

    @api.secure
    @nsds.response(410, 'Processing deleted')
    def delete(self, id):
        '''Delete a processing entry'''
        res = Database.rowcount("delete from li3ds.processing where id=%s", (id,))
        if not res:
            nsds.abort(404, 'Processing not found')
        return '', 410
