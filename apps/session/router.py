class ModelMetaRouter(object):
    def db_for_read(self, model, **hints):

        db = getattr(model._meta, 'in_db', None)
        if db:
            return db
        else:
            return 'default'

    def db_for_write(self, model, **hints):
        db = getattr(model._meta, 'in_db', None)
        if db:
            return db
        else:
            return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        db_set = {'default', 'in_db'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return 'users_user'

        return True

    def allow_syncdb(self, db, model):
        if db == getattr(model._meta, 'in_db', 'default'):
            return True
        return False