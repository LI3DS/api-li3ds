# -*- coding: utf-8 -*-
from flask_restplus import fields

from api_li3ds.app import api, Resource
from api_li3ds.database import Database
from .datasource import datasource_model
from .posdatasource import posdatasource_model

nssession = api.namespace('sessions', description='sessions related operations')

session_model_post = nssession.model('Session Model Post', {
    'name': fields.String,
    'platform': fields.Integer(required=True),
    'start_time': fields.DateTime(dt_format='iso8601', default=None),
    'end_time': fields.DateTime(dt_format='iso8601', default=None),
    'project': fields.Integer(required=True),
})


session_model = nssession.inherit('Session Model', session_model_post, {
    'id': fields.Integer,
})


@nssession.route('/', endpoint='sessions')
class AllSessions(Resource):

    @nssession.marshal_with(session_model)
    def get(self):
        '''Get all sessions'''
        return Database.query_asjson("select * from li3ds.session")

    @nssession.expect(session_model_post)
    @nssession.marshal_with(session_model)
    @nssession.response(201, 'Session created')
    def post(self):
        '''Create a session'''
        return Database.query_asdict(
            "insert into li3ds.session (name, start_time, end_time, project, platform) "
            "values (%(name)s, %(start_time)s, %(end_time)s, %(project)s, %(platform)s) "
            "returning *",
            api.payload
        ), 201


@nssession.route('/<int:id>', endpoint='session')
@nssession.response(410, 'Session not found')
class OneSession(Resource):

    @nssession.marshal_with(session_model)
    def get(self, id):
        '''Get one session given its identifier'''
        return Database.query_asjson(
            "select * from li3ds.session where id=%s", (id,)
        )

    @nssession.response(204, 'Session deleted')
    def delete(self, id):
        '''Delete a session given its identifier'''
        res = Database.rowcount("delete from li3ds.session where id=%s", (id,))
        if not res:
            nssession.abort(410, 'Session not found')
        return '', 204


@nssession.route('/<int:id>/platform', endpoint='session_platform')
@nssession.param('id', 'The session identifier')
class Platform(Resource):

    @nssession.marshal_with(session_model)
    def get(self, id):
        '''Get the platform used by the given session'''
        return Database.query_asjson(
            """select p.* from li3ds.platform p
            join li3ds.session s on s.platform = p.id where s.id=%s
            """, (id,)
        )


@nssession.route('/<int:id>/datasources', endpoint='session_datasources')
class Datasources(Resource):

    @nssession.marshal_with(datasource_model)
    def get(self, id):
        '''List session datasources'''
        return Database.query_asjson(
            """select d.* from li3ds.session s
            join li3ds.datasource d on d.session = s.id
            where s.id = %s
            """, (id,))


@nssession.route('/<int:id>/posdatasources', endpoint='session_posdatasources')
class PosDatasources(Resource):

    @nssession.marshal_with(posdatasource_model)
    def get(self, id):
        '''List session positional datasources'''
        return Database.query_asjson(
            """select d.* from li3ds.session s
            join li3ds.posdatasource d on d.session = s.id
            where s.id = %s
            """, (id,))
