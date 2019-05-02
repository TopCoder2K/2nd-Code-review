from peewee import *

db = PostgresqlDatabase(database="postgres", user="postgres", password="TopCoder2000", host="localhost")


class TgUser(Model):
    name = CharField()
    req_visits = IntegerField()
    cur_visits = IntegerField()
    user_id = IntegerField()

    class Meta:
        # Model will use "postgres.db".
        database = db
